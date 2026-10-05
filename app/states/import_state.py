import reflex as rx

import json
import logging
from typing import Any
from uuid import uuid4

from app.audio_service import audio_availability


class ImportState(rx.State):
    unavailable: str = ""
    transcript: str = ""
    error: str = ""
    feedback: str = ""
    busy: bool = False
    revision: int = 0
    token: str = ""
    endpoint: str = ""

    @rx.event
    def begin(self):
        if self.busy:
            return
        self.busy = True
        self.error = self.feedback = ""

    @rx.event
    async def load_import(self):
        from app.states.notes_state import NotesState

        notes = await self.get_state(NotesState)
        notes._load()
        notes.view = "import"
        notes.capture_saved_id = ""
        self.unavailable = audio_availability()
        self.token = str(uuid4())
        self.transcript = self.error = self.feedback = ""
        self.busy = False
        self.revision += 1
        self.endpoint = f"{rx.config.get_config().api_url.rstrip('/')}/api/v1/audio/transcribe"

    @rx.event
    def receive(self, raw: str):
        try:
            data = json.loads(raw)
            if not isinstance(data, dict) or data.get("token") != self.token:
                return
            if data.get("ignored") is True:
                return
            self.busy = False
            text = data.get("transcript", "")
            if isinstance(text, str) and text.strip() and len(text) <= 100000:
                self.transcript = text
                self.revision += 1
                self.error = ""
                self.feedback = (
                    "Transcription received. Review and correct before saving."
                )
            else:
                self.error = str(
                    data.get(
                        "error",
                        "Audio import failed. Nothing was saved. Select your file and consent again to retry.",
                    )
                )
                self.feedback = ""
        except (ValueError, TypeError) as e:
            logging.exception(f"Error: {e}")
            self.busy = False
            self.error = "Audio import failed. Nothing was saved. Select your file and consent again to retry."

    @rx.event
    async def save(self, form_data: dict[str, Any]):
        from app.states.notes_state import NotesState

        notes = await self.get_state(NotesState)
        if self.busy or notes.saving or notes.capture_saved_id:
            return
        self.transcript = str(form_data.get("content", ""))
        if not self.transcript.strip():
            self.error = "Add some transcript text before saving."
            return
        return NotesState.save_transcript(
            str(form_data.get("title", "")),
            self.transcript,
            str(form_data.get("category", "Personal")),
        )
