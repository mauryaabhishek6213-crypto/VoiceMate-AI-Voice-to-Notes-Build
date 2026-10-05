import reflex as rx

import json
from datetime import datetime, timezone
from typing import Any, TypedDict
from uuid import uuid4

from pydantic import ValidationError

from app.ai_provider import (
    AIError,
    AIRequest,
    INSTRUCTIONS,
    MAX_INPUT,
    OpenAIProvider,
    run_action,
)

from app.safe_logging import safe_log as logging


RESULTS_KEY = "voicemate.ai-results.v1"
MAX_RESULTS_BYTES = 1_500_000
LABELS: dict[str, str] = {
    "summarize": "Summarize",
    "key-points": "Key points",
    "title": "Suggest title",
    "action-items": "Action items",
    "questions": "Study questions",
    "rewrite": "Simplify",
    "translate": "Translate",
    "ask": "Ask this note",
}


class Result(TypedDict):
    id: str
    note_id: str
    action: str
    content: str
    created_at: str
    source_updated_at: str


def decode_results(raw: str) -> list[Result]:
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Invalid results storage.")
    output: list[Result] = []
    ids: set[str] = set()
    for item in data:
        if not isinstance(item, dict) or not all(
            isinstance(item.get(k), str) for k in Result.__annotations__
        ):
            raise ValueError("Invalid result record.")
        if (
            not item["id"]
            or not item["note_id"]
            or item["id"] in ids
            or item["action"] not in INSTRUCTIONS
            or len(item["content"]) > 30_000
        ):
            raise ValueError("Invalid result identity or content.")
        ids.add(item["id"])
        output.append(
            Result(**{key: item[key] for key in Result.__annotations__})
        )
    return output


def serialize_results(results: list[Result]) -> str:
    raw = json.dumps(results, ensure_ascii=False, separators=(",", ":"))
    if len(raw.encode("utf-8")) > MAX_RESULTS_BYTES:
        raise ValueError(
            "AI result storage is full. Copy your new result or shorten existing results before saving again."
        )
    return raw


def without_note_results(raw: str, note_id: str) -> str:
    return serialize_results(
        [r for r in decode_results(raw) if r["note_id"] != note_id]
    )


class AIState(rx.State):
    stored_results: str = rx.LocalStorage("[]", name=RESULTS_KEY, sync=True)
    actions: list[dict[str, str]] = [
        {"value": key, "label": value} for key, value in LABELS.items()
    ]
    context_id: str = ""
    confirmation: bool = False
    busy: bool = False
    storing: bool = False
    error: str = ""
    error_code: str = ""
    feedback: str = ""
    action_label: str = ""
    pending_action: str = "summarize"
    pending_question: str = ""
    pending_language: str = "English"
    pending_title: str = ""
    pending_characters: int = 0
    unsaved: list[Result] = []
    _approved_text: str = ""
    _approved_updated: str = ""
    _approved_note_id: str = ""
    _previous_results: str = "[]"
    _expected_results: str = ""

    @rx.var
    def results(self) -> list[Result]:
        try:
            saved = decode_results(self.stored_results)
        except (ValueError, TypeError, KeyError):
            logging.exception("Unexpected error")
            return [r for r in self.unsaved if r["note_id"] == self.context_id]
        unsaved_ids = {r["id"] for r in self.unsaved}
        return [
            r
            for r in saved
            if r["note_id"] == self.context_id and r["id"] not in unsaved_ids
        ] + [r for r in self.unsaved if r["note_id"] == self.context_id]

    @rx.var
    def storage_invalid(self) -> bool:
        try:
            decode_results(self.stored_results)
            return False
        except (ValueError, TypeError, KeyError):
            logging.exception("Unexpected error")
            return True

    @rx.event
    async def open_note(self):
        from app.states.notes_state import NotesState

        notes = await self.get_state(NotesState)
        self.context_id = notes.editing_id
        self.confirmation = False
        self.error = ""
        self.feedback = ""
        # Results for deleted notes are never displayed, even across tabs.
        try:
            known = {n["id"] for n in notes.notes}
            if not notes.storage_invalid:
                pruned = [
                    r
                    for r in decode_results(self.stored_results)
                    if r["note_id"] in known
                ]
                if len(pruned) != len(decode_results(self.stored_results)):
                    self.stored_results = serialize_results(pruned)
        except (ValueError, TypeError, KeyError):
            logging.exception("Unexpected error")
            self.error = "Saved AI results could not be read. They have not been overwritten. Your original notes are unaffected."

    @rx.event
    async def prepare(self, form_data: dict[str, Any]):
        if self.busy or self.storing:
            return
        action = str(form_data.get("action", "summarize"))
        if action not in INSTRUCTIONS:
            self.error = "Choose one of the eight AI actions."
            return
        self.pending_action = action
        self.pending_question = str(form_data.get("question", ""))
        self.pending_language = str(form_data.get("target_language", "English"))
        await self._prepare_saved_note()

    async def _prepare_saved_note(self):
        from app.states.notes_state import NotesState

        notes = await self.get_state(NotesState)
        self.confirmation = False
        self.error = ""
        self.error_code = ""
        self.feedback = ""
        note = next(
            (n for n in notes.notes if n["id"] == notes.editing_id), None
        )
        if (
            not note
            or notes.editor_missing
            or notes.storage_invalid
            or notes.saving
        ):
            self.error = "Save this note successfully before using AI."
            return
        try:
            AIRequest(
                text=note["content"],
                question=self.pending_question,
                target_language=self.pending_language,
                consent=True,
            )
            if (
                self.pending_action == "ask"
                and not self.pending_question.strip()
            ):
                raise AIError(
                    "empty_question",
                    "Enter a question before asking this note.",
                    422,
                )

        except (ValidationError, AIError):
            logging.exception("Unexpected error", exc_info=False)
            logging.warning("invalid_input")
            self.error = f"Use nonblank saved note text up to {MAX_INPUT:,} characters, a question up to 1,000 characters (required for Ask), and English or Hindi for translation."
            self.error_code = "invalid_input"
            return
        self.context_id = note["id"]
        self._approved_note_id = note["id"]
        self._approved_text = note["content"]
        self._approved_updated = note["updated_at"]
        self.pending_title = note["title"]
        self.pending_characters = len(note["content"])
        self.action_label = LABELS[self.pending_action]
        self.confirmation = True

    @rx.event
    async def retry(self):
        if not self.busy and not self.storing:
            await self._prepare_saved_note()

    @rx.event
    def cancel(self):
        self.confirmation = False
        self._approved_text = ""

    @rx.event
    def confirm_online(self, online: bool):
        if not self.confirmation or self.busy:
            return
        if not online:
            self.confirmation = False
            self.error = "This browser is offline. Reconnect and retry. No note text was sent to the AI provider."
            self.error_code = "offline"
            return
        self.confirmation = False
        self.busy = True
        self.error = ""
        self.feedback = "Sending the saved note you approved…"
        return AIState.generate

    @rx.event(background=True)
    async def generate(self):
        from app.states.notes_state import NotesState

        async with self:
            if not self.busy:
                return
            notes = await self.get_state(NotesState)
            note_id = self._approved_note_id
            text = self._approved_text
            updated = self._approved_updated
            action = self.pending_action
            question = self.pending_question
            language = self.pending_language
            current = next((n for n in notes.notes if n["id"] == note_id), None)
            if (
                not current
                or current["content"] != text
                or current["updated_at"] != updated
            ):
                self.busy = False
                self.error = "The saved note changed or was deleted. Retry to review and confirm the current text. Nothing was sent."
                self.feedback = ""
                return
        try:
            payload = AIRequest(
                text=text,
                question=question,
                target_language=language,
                consent=True,
            )
            response = await run_action(OpenAIProvider(), action, payload)
            record = Result(
                id=str(uuid4()),
                note_id=note_id,
                action=action,
                content=response.result,
                created_at=datetime.now(timezone.utc).isoformat(),
                source_updated_at=updated,
            )
            async with self:
                notes = await self.get_state(NotesState)
                if not any(n["id"] == note_id for n in notes.notes):
                    self.error = "This note was deleted while AI was working. Its result was discarded."
                    self.feedback = ""
                else:
                    self.unsaved.append(record)
                    try:
                        records = decode_results(self.stored_results)
                        records.append(record)
                        self._commit(records)
                    except (ValueError, TypeError, KeyError):
                        logging.exception("Unexpected error", exc_info=False)
                        logging.warning("result_storage_failed")
                        self.error = "The result is available below but could not be saved. Copy it or retry Save result. Your existing storage was not overwritten."
                        self.feedback = "Result not saved"

        except AIError as e:
            logging.exception("Unexpected error", exc_info=False)
            logging.warning("ai_request_failed")
            async with self:
                self.error = e.message
                self.error_code = e.code
                self.feedback = "No new result was generated."

        except Exception:
            logging.exception("Unexpected error", exc_info=False)
            logging.error("provider_error")
            async with self:
                self.error = "AI could not complete this request. No new result was saved. Please retry later."
                self.error_code = "provider_error"
                self.feedback = ""
        finally:
            async with self:
                self.busy = False
                self._approved_text = ""
                verify = self.storing
        if verify:
            yield self._verify_event()

    def _commit(self, records: list[Result]):
        raw = serialize_results(records)
        self._previous_results = self.stored_results
        self._expected_results = raw
        self.stored_results = raw
        self.storing = True
        self.error = ""
        self.feedback = "Saving result to this browser…"

    def _verify_event(self):
        return rx.call_script(
            "(() => { try { return localStorage.getItem('voicemate.ai-results.v1') || ''; } catch (_) { return '__unavailable__'; } })()",
            callback=AIState.verify_results,
        )

    @rx.event
    def verify_results(self, raw: str):
        if not self.storing:
            return
        self.storing = False
        if raw == self._expected_results:
            saved_ids = {r["id"] for r in decode_results(raw)}
            self.unsaved = [r for r in self.unsaved if r["id"] not in saved_ids]
            self.feedback = (
                "Result saved in this browser · original note unchanged"
            )
            self.error = ""
        else:
            self.stored_results = self._previous_results
            self.feedback = "Result not saved"
            self.error = "Browser storage could not be confirmed. Copy the result or retry Save result. Keep this page open; unsaved results will otherwise be lost."

    @rx.event
    async def save_result(self, form_data: dict[str, Any]):
        from app.states.notes_state import NotesState

        if self.busy or self.storing:
            return
        notes = await self.get_state(NotesState)
        if not any(n["id"] == self.context_id for n in notes.notes):
            self.error = (
                "This note no longer exists. Its result cannot be saved."
            )
            return
        content = str(form_data.get("content", ""))
        result_id = str(form_data.get("result_id", ""))
        if not content.strip() or len(content) > 30_000:
            self.error = "Enter result text between 1 and 30,000 characters."
            return
        record = next(
            (r.copy() for r in self.results if r["id"] == result_id), None
        )
        if not record:
            self.error = "This result is no longer available."
            return
        record["content"] = content
        self.unsaved = [r for r in self.unsaved if r["id"] != result_id] + [
            record
        ]
        try:
            records = [
                r
                for r in decode_results(self.stored_results)
                if r["id"] != result_id
            ]
            self._commit(records + [record])
        except (ValueError, TypeError, KeyError):
            logging.exception("Unexpected error")
            self.error = "The edited result could not be saved. Copy it to keep it safe; existing results have not been overwritten."
            return
        yield
        yield self._verify_event()

    @rx.event
    def copy_feedback(self, result: str):
        if result == "copied":
            self.feedback = "Result copied"
            self.error = ""
        else:
            self.error = "Clipboard unavailable. Select the result text and copy it manually."

    def _clear_note_results(self, note_id: str):
        self.storing = False
        self._expected_results = ""
        self.unsaved
        self.unsaved = [r for r in self.unsaved if r["note_id"] != note_id]
        try:
            self.stored_results = without_note_results(
                self.stored_results, note_id
            )
        except (ValueError, TypeError, KeyError):
            logging.exception("Unexpected error")
            self.error = "The note was deleted, but unreadable AI storage could not be cleaned up. No results will be shown for this note."
        if self.context_id == note_id:
            self.confirmation = False
