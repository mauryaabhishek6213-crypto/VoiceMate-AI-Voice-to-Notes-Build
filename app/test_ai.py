import reflex as rx

import asyncio
import json
import logging
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)

from app.ai_api import MAX_REQUEST_BYTES, create_api, get_provider
from app.ai_provider import (
    AIError,
    AIRequest,
    INSTRUCTIONS,
    MAX_INPUT,
    OpenAIProvider,
    run_action,
)
from app.states.ai_state import (
    decode_results,
    serialize_results,
    without_note_results,
)
from app.states.notes_state import serialize_notes, upsert_note
from app.safe_logging import safe_log


class FakeProvider:
    def __init__(
        self,
        result: str = "Injected test output",
        error: Exception | None = None,
    ):
        self.result = result
        self.error = error
        self.calls: list[tuple[str, AIRequest]] = []

    async def generate(self, action: str, request: AIRequest) -> str:
        self.calls.append((action, request))
        if self.error:
            raise self.error
        return self.result


def client_for(provider: FakeProvider, **options) -> TestClient:
    service = create_api(
        token="", public=False, requests_per_minute=100, **options
    )
    service.dependency_overrides[get_provider] = lambda: provider
    return TestClient(service, raise_server_exceptions=False)


def payload(**overrides) -> dict[str, str | bool]:
    return {"text": "Private note नमस्ते", "consent": True, **overrides}


def test_health_does_not_probe():
    provider = FakeProvider()
    with client_for(provider) as client:
        assert client.get("/health").json() == {
            "status": "ok",
            "provider": "not_probed",
        }
        assert provider.calls == []


@pytest.mark.parametrize("action", list(INSTRUCTIONS))
def test_all_actions(action):
    provider = FakeProvider()
    with client_for(provider) as client:
        response = client.post(
            f"/api/v1/ai/{action}",
            json=payload(question="What happened?", target_language="Hindi"),
        )
    assert response.status_code == 200
    assert response.json() == {
        "action": action,
        "result": "Injected test output",
    }
    assert len(provider.calls) == 1
    assert provider.calls[0][1].text == "Private note नमस्ते"


@pytest.mark.parametrize(
    "invalid",
    [
        {"text": ""},
        {"text": "   "},
        {"text": "x" * (MAX_INPUT + 1)},
        {"consent": False},
        {"consent": "true"},
        {"question": "x" * 1001},
        {"target_language": "French"},
        {"text": 42},
        {"extra": "private-extra"},
    ],
)
def test_validation_never_calls_provider_or_echoes_private_input(invalid):
    provider = FakeProvider()
    with client_for(provider) as client:
        response = client.post("/api/v1/ai/summarize", json=payload(**invalid))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
    assert "Private note" not in response.text
    assert "private-extra" not in response.text
    assert provider.calls == []


def test_missing_consent_unknown_action_empty_question_and_malformed_json():
    provider = FakeProvider()
    with client_for(provider) as client:
        assert (
            client.post(
                "/api/v1/ai/summarize", json={"text": "private"}
            ).status_code
            == 422
        )
        assert (
            client.post("/api/v1/ai/unknown", json=payload()).status_code == 422
        )
        response = client.post("/api/v1/ai/ask", json=payload(question=" "))
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "empty_question"
        assert (
            client.post(
                "/api/v1/ai/summarize",
                content="{private",
                headers={"Content-Type": "application/json"},
            ).status_code
            == 422
        )
    assert provider.calls == []


@pytest.mark.parametrize(
    "code,status,retryable",
    [
        ("insufficient_credits", 429, False),
        ("rate_limited", 429, True),
        ("timeout", 504, True),
        ("offline", 503, True),
        ("provider_unavailable", 503, False),
        ("provider_auth", 503, False),
        ("provider_error", 502, True),
    ],
)
def test_safe_provider_errors(code, status, retryable):
    provider = FakeProvider(
        error=AIError(code, "Safe failure.", status, retryable)
    )
    with client_for(provider) as client:
        response = client.post("/api/v1/ai/summarize", json=payload())
    assert response.status_code == status
    assert response.json() == {
        "error": {
            "code": code,
            "message": "Safe failure.",
            "retryable": retryable,
        }
    }
    assert "Private note" not in response.text


@pytest.mark.parametrize("result", ["", " ", "x" * 30001])
def test_invalid_outputs_are_not_published(result):
    with client_for(FakeProvider(result=result)) as client:
        response = client.post("/api/v1/ai/summarize", json=payload())
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "invalid_response"


def test_unexpected_failure_is_sanitized():
    with client_for(
        FakeProvider(error=RuntimeError("Private note and internal details"))
    ) as client:
        response = client.post("/api/v1/ai/summarize", json=payload())
    assert response.status_code == 500
    assert "Private note" not in response.text
    assert response.json()["error"]["code"] == "internal_error"


def test_service_deadline():
    class SlowProvider:
        async def generate(self, action, request):
            await asyncio.sleep(1)
            return "not reached"

    async def check():
        with patch("app.ai_provider.TIMEOUT", 0.001):
            with pytest.raises(AIError) as raised:
                await run_action(
                    SlowProvider(), "summarize", AIRequest(**payload())
                )
        assert raised.value.code == "timeout"

    asyncio.run(check())


def test_request_bytes_declared_and_streamed():
    provider = FakeProvider()
    with client_for(provider) as client:
        oversized = client.post(
            "/api/v1/ai/summarize", content=b"x" * (MAX_REQUEST_BYTES + 1)
        )
        assert oversized.status_code == 413
        spoofed = client.post(
            "/api/v1/ai/summarize",
            content=b"x" * (MAX_REQUEST_BYTES + 1),
            headers={"Content-Length": "1"},
        )
        assert spoofed.status_code == 413
        invalid = client.post(
            "/api/v1/ai/summarize",
            content="{}",
            headers={"Content-Length": "bad"},
        )
        assert invalid.status_code == 400
    assert provider.calls == []


def test_rate_limit_and_cors():
    service = create_api(token="", public=False, requests_per_minute=1)
    provider = FakeProvider()
    service.dependency_overrides[get_provider] = lambda: provider
    with TestClient(service) as client:
        assert (
            client.post("/api/v1/ai/title", json=payload()).status_code == 200
        )
        response = client.post("/api/v1/ai/title", json=payload())
        assert response.status_code == 429
        assert response.headers["retry-after"] == "60"
        allowed = client.options(
            "/api/v1/ai/title",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert (
            allowed.headers["access-control-allow-origin"]
            == "http://localhost:3000"
        )
        denied = client.options(
            "/api/v1/ai/title",
            headers={
                "Origin": "https://untrusted.invalid",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in denied.headers


def test_public_fails_closed_and_optional_token():
    provider = FakeProvider()
    for token, public in [
        ("", True),
        ("test-only-token", False),
        ("test-only-token", True),
    ]:
        service = create_api(token=token, public=public)
        service.dependency_overrides[get_provider] = lambda: provider
        with TestClient(service) as client:
            assert client.get("/health").status_code == 200
            response = client.post("/api/v1/ai/title", json=payload())
            assert response.status_code == (401 if token else 503)
            if token:
                assert (
                    client.post(
                        "/api/v1/ai/title",
                        json=payload(),
                        headers={"Authorization": "Bearer wrong"},
                    ).status_code
                    == 401
                )
                assert (
                    client.post(
                        "/api/v1/ai/title",
                        json=payload(),
                        headers={"Authorization": f"Bearer {token}"},
                    ).status_code
                    == 200
                )


def test_missing_provider(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(AIError) as raised:
        asyncio.run(OpenAIProvider().generate("title", AIRequest(**payload())))
    assert raised.value.code == "provider_unavailable"


@pytest.mark.parametrize(
    "kind,expected",
    [
        ("credits", "insufficient_credits"),
        ("rate", "rate_limited"),
        ("timeout", "timeout"),
        ("offline", "offline"),
        ("auth", "provider_auth"),
    ],
)
def test_sdk_error_mapping_without_real_network(monkeypatch, kind, expected):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-value")
    request = httpx.Request("POST", "https://example.invalid")
    response = httpx.Response(429, request=request)
    errors = {
        "credits": RateLimitError(
            "sensitive provider message",
            response=response,
            body={
                "error": {
                    "code": "credit_balance_exhausted",
                    "type": "insufficient_quota",
                }
            },
        ),
        "rate": RateLimitError(
            "sensitive provider message",
            response=response,
            body={"code": "rate_limit_exceeded"},
        ),
        "timeout": APITimeoutError(request=request),
        "offline": APIConnectionError(request=request),
        "auth": AuthenticationError(
            "sensitive provider message",
            response=httpx.Response(401, request=request),
            body={},
        ),
    }
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.chat.completions.create.side_effect = errors[kind]
    with patch("app.ai_provider.AsyncOpenAI", return_value=mock_client):
        with pytest.raises(AIError) as raised:
            asyncio.run(
                OpenAIProvider().generate("summarize", AIRequest(**payload()))
            )
    assert raised.value.code == expected
    assert "sensitive" not in raised.value.message


@pytest.mark.parametrize(
    "provider_code,expected",
    [
        ("rate_limit_exceeded", "rate_limited"),
        ("credit_balance_exhausted", "insufficient_credits"),
    ],
)
def test_provider_rate_limit_logging_is_sanitized(
    monkeypatch, caplog, provider_code, expected
):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-value")
    private_marker = "PRIVATE_PROVIDER_LOG_REGRESSION_7e28b36c"
    request = httpx.Request("POST", "https://example.invalid")
    error = RateLimitError(
        private_marker,
        response=httpx.Response(429, request=request),
        body={"code": provider_code, "message": private_marker},
    )
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.chat.completions.create.side_effect = error
    with caplog.at_level(logging.WARNING):
        with patch("app.ai_provider.AsyncOpenAI", return_value=mock_client):
            with pytest.raises(AIError) as raised:
                asyncio.run(
                    OpenAIProvider().generate(
                        "summarize", AIRequest(**payload())
                    )
                )
    assert raised.value.code == expected
    assert raised.value.status == 429
    assert raised.value.retryable == (expected == "rate_limited")
    assert private_marker not in raised.value.message
    assert private_marker not in caplog.text
    assert caplog.records
    assert expected in [record.getMessage() for record in caplog.records]
    assert all(record.exc_info is None for record in caplog.records)
    assert all(record.stack_info is None for record in caplog.records)
    assert all(not record.args for record in caplog.records)
    mock_client.chat.completions.create.assert_awaited_once()


def test_local_results_roundtrip_edit_and_deletion_leave_transcript_unchanged():
    notes, note = upsert_note(
        [], "", "Original", "Original transcript", "Personal", False
    )
    original = serialize_notes(notes)
    result = {
        "id": "r1",
        "note_id": note["id"],
        "action": "summarize",
        "content": "Result नमस्ते",
        "created_at": note["created_at"],
        "source_updated_at": note["updated_at"],
    }
    other = {**result, "id": "r2", "note_id": "another-note"}
    raw = serialize_results([result, other])
    assert decode_results(raw)[0] == result
    edited = decode_results(raw)
    edited[0]["content"] = "Edited result"
    assert (
        decode_results(serialize_results(edited))[0]["content"]
        == "Edited result"
    )
    assert decode_results(without_note_results(raw, note["id"])) == [other]
    assert serialize_notes(notes) == original
    for invalid in ("{}", "[{}]", "not json", json.dumps([result, result])):
        with pytest.raises(ValueError):
            decode_results(invalid)


def test_storage_budget():
    record = {
        "id": "r",
        "note_id": "n",
        "action": "rewrite",
        "content": "x" * 30000,
        "created_at": "now",
        "source_updated_at": "now",
    }
    with pytest.raises(ValueError):
        serialize_results([record] * 60)


@pytest.mark.parametrize("method", ["exception", "warning", "error", "debug"])
def test_safe_logger_drops_private_messages_and_metadata(caplog, method):
    private_marker = "PRIVATE_SAFE_LOG_REGRESSION_29ab"
    with caplog.at_level(logging.DEBUG):
        getattr(safe_log, method)(
            private_marker,
            exc_info=True,
            stack_info=True,
            extra={"private": private_marker},
        )
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.getMessage() == "provider_error"
    assert private_marker not in caplog.text
    assert record.exc_info is None
    assert record.stack_info is None
    assert not record.args
    assert not hasattr(record, "private")


@pytest.mark.parametrize("method", ["warning", "error", "debug"])
@pytest.mark.parametrize(
    "code", ["rate_limited", "insufficient_credits", "timeout"]
)
def test_safe_logger_preserves_known_codes(caplog, method, code):
    with caplog.at_level(logging.DEBUG):
        getattr(safe_log, method)(code)
    assert [record.getMessage() for record in caplog.records] == [code]
    assert all(record.exc_info is None for record in caplog.records)
    assert all(record.stack_info is None for record in caplog.records)
    assert all(not record.args for record in caplog.records)


@pytest.mark.parametrize("method", ["warning", "error", "debug"])
def test_safe_logger_never_stringifies_untrusted_objects(caplog, method):
    class UntrustedMessage:
        def __str__(self):
            raise AssertionError("Untrusted message must not be formatted")

    with caplog.at_level(logging.DEBUG):
        getattr(safe_log, method)(UntrustedMessage())
    assert [record.getMessage() for record in caplog.records] == [
        "provider_error"
    ]
