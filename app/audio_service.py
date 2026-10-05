import reflex as rx

import asyncio
from app.safe_logging import safe_log as logging
import os
from pathlib import PurePath
from urllib.parse import unquote

from fastapi import Request
from fastapi.responses import JSONResponse
from openai import (
    AsyncOpenAI,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)

from app.ai_provider import AIError

MAX_AUDIO_BYTES = 20_000_000
FORMATS = {"mp3", "m4a", "wav", "webm", "mp4"}
MIME_TYPES = {
    "mp3": {"audio/mpeg", "audio/mp3"},
    "m4a": {"audio/mp4", "audio/x-m4a", "video/mp4"},
    "wav": {"audio/wav", "audio/x-wav", "audio/wave"},
    "webm": {"audio/webm", "video/webm"},
    "mp4": {"audio/mp4", "video/mp4"},
}


def audio_availability() -> str:
    if os.getenv("OPENAI_AUDIO_ENABLED", "").lower() != "true":
        return "Audio transcription is not enabled for this provider. You can still type a note or use browser speech capture."
    if (
        not os.getenv("OPENAI_API_KEY", "").strip()
        or not os.getenv("OPENAI_TRANSCRIPTION_MODEL", "").strip()
    ):
        return "Transcription is not configured. Text notes and browser speech capture remain available."
    return ""


def validate_audio(
    filename: str, size: int, mime: str = "", header: bytes | None = None
) -> str:
    extension = PurePath(filename.replace("\\", "/")).suffix.lower().lstrip(".")
    if extension not in FORMATS or not 0 < size <= MAX_AUDIO_BYTES:
        raise AIError(
            "invalid_audio",
            "Choose one supported nonempty audio file up to 20 MB.",
            422,
        )
    if mime and mime.split(";")[0].lower() not in MIME_TYPES[extension] | {
        "application/octet-stream"
    }:
        raise AIError(
            "invalid_audio",
            "Choose one supported nonempty audio file up to 20 MB.",
            422,
        )
    if header is not None:
        valid = False
        if extension == "wav":
            valid = header[:4] == b"RIFF" and header[8:12] == b"WAVE"
        elif extension in ("mp4", "m4a"):
            valid = header[4:8] == b"ftyp"
        elif extension == "webm":
            valid = header[:4] == b"\x1a\x45\xdf\xa3"
        elif extension == "mp3":
            valid = header[:3] == b"ID3" or (
                len(header) >= 2 and header[0] == 255 and header[1] & 224 == 224
            )
        if not valid:
            raise AIError(
                "invalid_audio",
                "Choose one supported nonempty audio file up to 20 MB.",
                422,
            )
    return extension


async def transcribe_audio(
    filename: str, audio: bytes, mime: str, consent: bool, language: str = "en"
) -> str:
    if consent is not True:
        raise AIError(
            "consent_required",
            "Explicit audio consent is required. Nothing was sent to the provider.",
            422,
        )
    validate_audio(filename, len(audio), mime, audio[:16])
    if language not in ("en", "hi"):
        raise AIError("invalid_language", "Choose English or Hindi.", 422)
    reason = audio_availability()
    if reason:
        raise AIError("transcription_unavailable", reason)
    try:
        async with asyncio.timeout(90):
            async with AsyncOpenAI(
                api_key=os.environ["OPENAI_API_KEY"],
                base_url=os.getenv("OPENAI_BASE_URL") or None,
                timeout=85,
                max_retries=0,
            ) as client:
                response = await client.audio.transcriptions.create(
                    model=os.environ["OPENAI_TRANSCRIPTION_MODEL"],
                    file=(
                        f"audio.{validate_audio(filename, len(audio), mime)}",
                        audio,
                        mime or "application/octet-stream",
                    ),
                    language=language,
                )
        text = response.text
        if not isinstance(text, str) or not text.strip() or len(text) > 100000:
            raise AIError(
                "invalid_response",
                "No usable transcript was returned. Nothing was saved.",
                502,
            )
        return text.strip()

    except AIError:
        logging.exception("Unexpected error", exc_info=False)
        logging.warning("provider_response_invalid")
        raise
    except RateLimitError as e:
        logging.exception("Unexpected error")
        body = e.body if isinstance(e.body, dict) else {}
        details = body.get("error", body)
        details = details if isinstance(details, dict) else {}
        quota = (
            details.get("code")
            in ("credit_balance_exhausted", "insufficient_quota")
            or details.get("type") == "insufficient_quota"
        )
        logging.warning("insufficient_credits" if quota else "rate_limited")
        raise AIError(
            "insufficient_credits" if quota else "rate_limited",
            "The provider has insufficient credits for transcription. Retry only after credits are restored."
            if quota
            else "Transcription is rate limited. Wait before consenting to retry.",
            429,
            not quota,
        ) from None

    except (TimeoutError, APITimeoutError):
        logging.exception("Unexpected error")
        logging.warning("timeout")
        raise AIError(
            "timeout",
            "Transcription timed out. Review consent before retrying.",
            504,
            True,
        ) from None

    except APIConnectionError:
        logging.exception("Unexpected error")
        logging.warning("offline")
        raise AIError(
            "offline",
            "The transcription service cannot be reached. Check connectivity and retry.",
            503,
            True,
        ) from None

    except AuthenticationError:
        logging.exception("Unexpected error")
        logging.warning("provider_auth")
        raise AIError(
            "provider_auth",
            "Transcription is not configured. Text notes and browser speech capture remain available.",
            503,
        ) from None

    except APIStatusError:
        logging.exception("Unexpected error")
        logging.warning("unsupported_transcription")
        raise AIError(
            "unsupported_transcription",
            "The provider does not support this transcription request. No transcript was saved.",
            502,
        ) from None

    except Exception:
        logging.exception("Unexpected error")
        logging.error("provider_error")
        raise AIError(
            "provider_error",
            "Audio import failed. Nothing was saved. Select your file and consent again to retry.",
            502,
            True,
        ) from None


async def audio_endpoint(request: Request) -> JSONResponse:
    audio = bytearray()
    try:
        if request.headers.get("x-audio-consent") != "true":
            raise AIError(
                "consent_required",
                "Explicit audio consent is required. Nothing was sent to the provider.",
                422,
            )
        reason = audio_availability()
        if reason:
            raise AIError("transcription_unavailable", reason)
        filename = unquote(request.headers.get("x-audio-filename", ""))
        mime = request.headers.get("content-type", "")
        declared = request.headers.get("content-length")
        if declared:
            try:
                validate_audio(filename, int(declared), mime)
            except ValueError:
                raise AIError(
                    "invalid_audio",
                    "Choose one supported nonempty audio file up to 20 MB.",
                    422,
                ) from None
        async with asyncio.timeout(45):
            async for chunk in request.stream():
                if len(audio) + len(chunk) > MAX_AUDIO_BYTES:
                    raise AIError(
                        "audio_too_large",
                        "Choose one supported nonempty audio file up to 20 MB.",
                        413,
                    )
                audio.extend(chunk)
        text = await transcribe_audio(
            filename,
            bytes(audio),
            mime,
            True,
            request.headers.get("x-audio-language", "en"),
        )
        return JSONResponse({"transcript": text})

    except AIError as e:
        logging.exception("Unexpected error")
        logging.warning("audio_request_failed")
        return JSONResponse(e.payload(), status_code=e.status)

    except TimeoutError:
        logging.exception("Unexpected error")
        logging.warning("timeout")
        return JSONResponse(
            AIError(
                "timeout",
                "Transcription timed out. Review consent before retrying.",
                408,
                True,
            ).payload(),
            status_code=408,
        )

    except Exception:
        logging.exception("Unexpected error")
        logging.error("import_failed")
        return JSONResponse(
            AIError(
                "import_failed",
                "Audio import failed. Nothing was saved. Select your file and consent again to retry.",
                502,
                True,
            ).payload(),
            status_code=502,
        )
    finally:
        audio.clear()
