import reflex as rx

import asyncio
import hmac
import os
import time
from collections import OrderedDict, deque

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.audio_service import MAX_AUDIO_BYTES, audio_endpoint

from app.ai_provider import (
    AIError,
    AIRequest,
    AIResponse,
    Action,
    ErrorResponse,
    OpenAIProvider,
    Provider,
    run_action,
)

import logging


MAX_REQUEST_BYTES = 96_000


def get_provider() -> Provider:
    return OpenAIProvider()


class RequestGuard:
    def __init__(
        self, app: ASGIApp, token: str, public: bool, requests_per_minute: int
    ):
        self.app = app
        self.token = token
        self.public = public
        self.limit = requests_per_minute
        self.clients: OrderedDict[str, deque[float]] = OrderedDict()

    async def reject(
        self, scope: Scope, receive: Receive, send: Send, error: AIError
    ):
        headers = {"Retry-After": "60"} if error.code == "rate_limited" else {}
        await JSONResponse(
            error.payload(), status_code=error.status, headers=headers
        )(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if (
            scope["type"] != "http"
            or not (
                scope["path"].startswith("/api/v1/ai/")
                or scope["path"] == "/api/v1/audio/transcribe"
            )
            or scope["method"] == "OPTIONS"
        ):
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        if self.public and not self.token:
            await self.reject(
                scope,
                receive,
                send,
                AIError(
                    "service_unavailable",
                    "Public AI requests are disabled until server authentication is configured.",
                ),
            )
            return
        if self.token:
            supplied = headers.get(b"authorization", b"")
            expected = f"Bearer {self.token}".encode()
            if not hmac.compare_digest(supplied, expected):
                await self.reject(
                    scope,
                    receive,
                    send,
                    AIError(
                        "unauthorized", "A valid bearer token is required.", 401
                    ),
                )
                return
        now = time.monotonic()
        client = scope.get("client")
        identity = str(client[0]) if client else "unknown"
        # Direct peer only: untrusted forwarded headers must not bypass the limiter.
        bucket = self.clients.pop(identity, deque())
        while bucket and bucket[0] <= now - 60:
            bucket.popleft()
        self.clients[identity] = bucket
        if len(self.clients) > 4096:
            self.clients.popitem(last=False)
        if len(bucket) >= self.limit:
            await self.reject(
                scope,
                receive,
                send,
                AIError(
                    "rate_limited",
                    "Too many requests. Wait a minute before retrying.",
                    429,
                    True,
                ),
            )
            return
        bucket.append(now)
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            await self.reject(
                scope,
                receive,
                send,
                AIError("invalid_request", "Invalid request length.", 400),
            )
            return
        maximum = (
            MAX_AUDIO_BYTES
            if scope["path"] == "/api/v1/audio/transcribe"
            else MAX_REQUEST_BYTES
        )
        if declared < 0 or declared > maximum:
            await self.reject(
                scope,
                receive,
                send,
                AIError(
                    "request_too_large",
                    "Request exceeds the 96,000-byte limit.",
                    413,
                ),
            )
            return
        body = bytearray()
        try:
            async with asyncio.timeout(10):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    body.extend(message.get("body", b""))
                    if len(body) > maximum:
                        await self.reject(
                            scope,
                            receive,
                            send,
                            AIError(
                                "request_too_large",
                                "Request exceeds the 96,000-byte limit.",
                                413,
                            ),
                        )
                        return
                    if not message.get("more_body", False):
                        break
        except TimeoutError:
            logging.exception("Unexpected error")
            await self.reject(
                scope,
                receive,
                send,
                AIError(
                    "request_timeout",
                    "Request body took too long to arrive.",
                    408,
                    True,
                ),
            )
            return
        delivered = False

        async def replay() -> Message:
            nonlocal delivered
            if not delivered:
                delivered = True
                return {
                    "type": "http.request",
                    "body": bytes(body),
                    "more_body": False,
                }
            return await receive()

        await self.app(scope, replay, send)


def create_api(
    *,
    token: str | None = None,
    public: bool | None = None,
    requests_per_minute: int = 10,
) -> FastAPI:
    service = FastAPI(
        title="VoiceMate AI", version="1.0", docs_url=None, redoc_url=None
    )
    service.add_middleware(
        RequestGuard,
        token=os.getenv("AI_API_BEARER_TOKEN", "") if token is None else token,
        public=os.getenv("AI_API_PUBLIC", "false").lower() == "true"
        if public is None
        else public,
        requests_per_minute=max(1, requests_per_minute),
    )
    service.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["GET", "POST"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Audio-Filename",
            "X-Audio-Consent",
            "X-Audio-Language",
        ],
        allow_credentials=False,
    )

    @service.exception_handler(AIError)
    async def ai_error(request: Request, error: AIError):
        headers = {"Retry-After": "60"} if error.code == "rate_limited" else {}
        return JSONResponse(
            error.payload(), status_code=error.status, headers=headers
        )

    @service.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        return JSONResponse(
            AIError(
                "invalid_request",
                "Use a supported action, nonblank text (1–20,000 characters), a question up to 1,000 characters, English or Hindi as target_language, and consent=true. Unknown fields are not accepted.",
                422,
            ).payload(),
            status_code=422,
        )

    @service.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        return JSONResponse(
            AIError(
                "http_error",
                "This endpoint or request method is not available.",
                error.status_code,
            ).payload(),
            status_code=error.status_code,
        )

    @service.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception):
        return JSONResponse(
            AIError(
                "internal_error",
                "The request could not be completed. No result was returned.",
                500,
                True,
            ).payload(),
            status_code=500,
        )

    @service.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "provider": "not_probed"}

    @service.post(
        "/api/v1/ai/{action}",
        response_model=AIResponse,
        responses={
            422: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
            504: {"model": ErrorResponse},
        },
    )
    async def generate(
        action: Action,
        payload: AIRequest,
        provider: Provider = Depends(get_provider),
    ) -> AIResponse:
        return await run_action(provider, action, payload)

    service.add_api_route(
        "/api/v1/audio/transcribe", audio_endpoint, methods=["POST"]
    )
    return service


api = create_api()
