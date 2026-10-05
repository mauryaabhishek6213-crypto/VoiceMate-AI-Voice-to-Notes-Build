import reflex as rx

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from test_utils import run_event

from app.audio_service import (
    MAX_AUDIO_BYTES,
    audio_availability,
    transcribe_audio,
    validate_audio,
)
from app.ai_api import create_api
from app.ai_provider import AIError
from app.components.note_export import COPY_SCRIPT, SHARE_SCRIPT
from app.pages.audio_import import CLIENT_INIT, SEND_SCRIPT
from app.states.export_state import export_filename, format_note, share_outcome
from app.states.import_state import ImportState
from app.states.notes_state import upsert_note
from app.states.settings_state import (
    DEFAULT_SETTINGS,
    SettingsState,
    TRANSLATIONS,
    clear_verified,
    decode_settings,
)

HEADERS = {
    "mp3": b"ID3" + b"\0" * 16,
    "wav": b"RIFF\0\0\0\0WAVE" + b"\0" * 8,
    "m4a": b"\0\0\0\x18ftypM4A " + b"\0" * 8,
    "mp4": b"\0\0\0\x18ftypisom" + b"\0" * 8,
    "webm": b"\x1a\x45\xdf\xa3" + b"\0" * 16,
}


@pytest.mark.parametrize("extension", list(HEADERS))
def test_audio_formats_and_boundaries(extension):
    data = HEADERS[extension]
    assert (
        validate_audio(f"clip.{extension.upper()}", MAX_AUDIO_BYTES, "", data)
        == extension
    )
    for size in (0, -1, MAX_AUDIO_BYTES + 1):
        with pytest.raises(AIError):
            validate_audio(f"clip.{extension}", size)
    with pytest.raises(AIError):
        validate_audio(f"clip.{extension}", len(data), "text/plain", data)
    with pytest.raises(AIError):
        validate_audio(f"clip.{extension}", len(data), "", b"not audio")


@pytest.mark.parametrize(
    "filename",
    ["file.ogg", "file.flac", "file.txt", "file.mp3.exe", "file", ""],
)
def test_unsupported_audio(filename):
    with pytest.raises(AIError):
        validate_audio(filename, 12)


def test_audio_disabled_and_consent_fail_closed(monkeypatch):
    monkeypatch.delenv("OPENAI_AUDIO_ENABLED", raising=False)
    assert audio_availability()
    with patch("app.audio_service.AsyncOpenAI") as sdk:
        for consent in (False, True):
            with pytest.raises(AIError) as error:
                asyncio.run(
                    transcribe_audio(
                        "clip.mp3", HEADERS["mp3"], "audio/mpeg", consent
                    )
                )
            assert error.value.code == (
                "consent_required"
                if not consent
                else "transcription_unavailable"
            )
        sdk.assert_not_called()


def enable_audio(monkeypatch):
    monkeypatch.setenv("OPENAI_AUDIO_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-value-only")
    monkeypatch.setenv("OPENAI_TRANSCRIPTION_MODEL", "test-model")


def test_real_sdk_contract_and_invalid_response(monkeypatch):
    enable_audio(monkeypatch)
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.audio.transcriptions.create.return_value = SimpleNamespace(
        text="Hello नमस्ते"
    )
    with patch("app.audio_service.AsyncOpenAI", return_value=client):
        assert (
            asyncio.run(
                transcribe_audio(
                    "clip.mp3", HEADERS["mp3"], "audio/mpeg", True, "hi"
                )
            )
            == "Hello नमस्ते"
        )
        call = client.audio.transcriptions.create.call_args.kwargs
        assert call["file"][1] == HEADERS["mp3"]
        assert call["language"] == "hi"
        client.audio.transcriptions.create.return_value = SimpleNamespace(
            text=" "
        )
        with pytest.raises(AIError) as error:
            asyncio.run(
                transcribe_audio("clip.mp3", HEADERS["mp3"], "audio/mpeg", True)
            )
        assert error.value.code == "invalid_response"


def test_audio_api_consent_and_real_validation(monkeypatch):
    enable_audio(monkeypatch)
    with TestClient(
        create_api(token="", public=False, requests_per_minute=100)
    ) as client:
        headers = {"Content-Type": "audio/mpeg", "X-Audio-Filename": "clip.mp3"}
        with patch(
            "app.audio_service.transcribe_audio",
            new_callable=AsyncMock,
            return_value="Real SDK result in test",
        ) as transcribe:
            assert (
                client.post(
                    "/api/v1/audio/transcribe",
                    content=HEADERS["mp3"],
                    headers=headers,
                ).status_code
                == 422
            )
            transcribe.assert_not_called()
            headers["X-Audio-Consent"] = "true"
            response = client.post(
                "/api/v1/audio/transcribe",
                content=HEADERS["mp3"],
                headers=headers,
            )
            assert response.json()["transcript"] == "Real SDK result in test"
        headers["X-Audio-Filename"] = "clip.exe"
        response = client.post(
            "/api/v1/audio/transcribe", content=HEADERS["mp3"], headers=headers
        )
        assert response.status_code == 422


def test_reflex_audio_transformer_starlette():
    from app.app import configure_audio_api

    api = Starlette()
    assert configure_audio_api(api) is api
    with TestClient(api) as client:
        for _ in range(10):
            response = client.post("/api/v1/audio/transcribe", content=b"")
            assert response.status_code == 422
            assert response.json()["error"]["code"] == "consent_required"
        response = client.post("/api/v1/audio/transcribe", content=b"")
        assert response.status_code == 429
        assert response.json()["error"]["code"] == "rate_limited"
        assert response.headers["Retry-After"] == "60"
    with TestClient(configure_audio_api(Starlette())) as client:
        response = client.post(
            "/api/v1/audio/transcribe",
            content=b"x",
            headers={"Content-Length": str(MAX_AUDIO_BYTES + 1)},
        )
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "request_too_large"


def test_audio_api_auth_and_size(monkeypatch):
    enable_audio(monkeypatch)
    with TestClient(create_api(token="test-only-token", public=True)) as client:
        assert (
            client.post(
                "/api/v1/audio/transcribe", content=b"private"
            ).status_code
            == 401
        )
        response = client.post(
            "/api/v1/audio/transcribe",
            content=b"x",
            headers={
                "Authorization": "Bearer test-only-token",
                "Content-Length": str(MAX_AUDIO_BYTES + 1),
            },
        )
        assert response.status_code == 413


def test_import_callbacks_and_stale_results():
    state = ImportState()
    state.token = "current"
    state.busy = True
    asyncio.run(
        run_event(
            state.receive, json.dumps({"token": "old", "transcript": "ignore"})
        )
    )
    assert state.busy & (state.transcript == "")
    asyncio.run(
        run_event(
            state.receive,
            json.dumps({"token": "current", "error": "quota unavailable"}),
        )
    )
    assert ~state.busy & (state.transcript == "") & (state.error != "")
    asyncio.run(
        run_event(
            state.receive,
            json.dumps({"token": "current", "transcript": "Words नमस्ते"}),
        )
    )
    assert (state.transcript == "Words नमस्ते") & (state.error == "")
    asyncio.run(run_event(state.receive, "broken"))
    assert (state.error != "") & ~state.busy


def test_export_text_filename_and_fallback():
    _, note = upsert_note(
        [], "", "Thought नमस्ते", "Line 1\nLine 2", "Ideas", False
    )
    assert format_note(note) == "Thought नमस्ते\n\nLine 1\nLine 2\n"
    for title in ("../../unsafe:name?", "CON", "NUL", "", "\0", "x" * 200):
        filename = export_filename(title)
        assert filename.endswith(".txt") and len(filename) <= 84
        assert not any(c in filename for c in "/\\:\0?")
    assert share_outcome("unavailable")[1]
    assert share_outcome("share-error")[1]
    assert not share_outcome("cancelled")[1]
    assert not share_outcome("shared")[1]
    assert "navigator.clipboard" not in SHARE_SCRIPT
    assert "navigator.share" in SHARE_SCRIPT and "AbortError" in SHARE_SCRIPT
    assert "localStorage" in COPY_SCRIPT and "note.content" in COPY_SCRIPT


def test_settings_validation_and_clear_verification():
    assert decode_settings(json.dumps(DEFAULT_SETTINGS)) == DEFAULT_SETTINGS
    for raw in (
        "{}",
        "[]",
        "broken",
        json.dumps({**DEFAULT_SETTINGS, "theme": "auto"}),
        json.dumps({**DEFAULT_SETTINGS, "language": "fr"}),
        json.dumps({**DEFAULT_SETTINGS, "speech": "xx"}),
        json.dumps({**DEFAULT_SETTINGS, "extra": True}),
    ):
        with pytest.raises(ValueError):
            decode_settings(raw)
    assert clear_verified(json.dumps({"notes": "[]", "results": "[]"}))
    assert not clear_verified(json.dumps({"notes": "[]", "results": "[{}]"}))
    assert not clear_verified("")
    state = SettingsState()
    state.saving = True
    state._expected = "expected"
    state._previous = json.dumps(DEFAULT_SETTINGS)
    asyncio.run(run_event(state.verify_preferences, "wrong"))
    assert ~state.saving & (state.error != "")


def test_browser_import_contract_and_translation_coverage():
    assert "fetch(" not in CLIENT_INIT
    assert "20000000" in CLIENT_INIT and "20000000" in SEND_SCRIPT
    assert "consent.checked = false" in SEND_SCRIPT
    assert "X-Audio-Consent" in SEND_SCRIPT
    assert "AbortController" in SEND_SCRIPT
    for label in (
        "Home",
        "My notes",
        "Settings",
        "Import audio",
        "Save note",
        "Start",
        "Stop",
        "Copy note",
        "Share note",
        "Save preferences",
        "Clear all notes and AI results",
    ):
        assert label in TRANSLATIONS
