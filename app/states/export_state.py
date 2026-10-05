import reflex as rx

import re
from app.states.notes_state import Note


def export_filename(title: str) -> str:
    stem = re.sub(r"[^\w\- ]", "", title, flags=re.UNICODE).strip()[:80].strip()
    if not stem or stem.upper() in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *{f"COM{i}" for i in range(1, 10)},
        *{f"LPT{i}" for i in range(1, 10)},
    }:
        stem = "voicemate-note"
    return f"{stem}.txt"


def format_note(note: Note) -> str:
    return f"{note['title']}\n\n{note['content']}\n"


def share_outcome(result: str) -> tuple[str, bool]:
    messages = {
        "copied": "Note copied",
        "shared": "Note shared",
        "cancelled": "Share cancelled",
        "unavailable": "Sharing unavailable. Choose Copy instead if you want to use the clipboard.",
        "share-error": "Sharing unavailable. Choose Copy instead if you want to use the clipboard.",
        "clipboard-error": "Clipboard unavailable. Select the saved note text and copy manually.",
    }
    return messages.get(result, messages["clipboard-error"]), result in (
        "unavailable",
        "share-error",
    )


class ExportState(rx.State):
    feedback: str = ""
    fallback: bool = False

    @rx.event
    def receive(self, result: str):
        self.feedback, self.fallback = share_outcome(result)

    @rx.event
    def dismiss(self):
        self.feedback = ""
        self.fallback = False

    @rx.event
    async def download(self):
        from app.states.notes_state import NotesState

        notes = await self.get_state(NotesState)
        note = next(
            (n for n in notes.notes if n["id"] == notes.editing_id), None
        )
        if not note or notes.storage_invalid or notes.saving:
            self.feedback = "Save this note successfully before exporting."
            return
        self.feedback = "Download requested · check your browser downloads."
        return rx.download(
            data=format_note(note).encode("utf-8"),
            filename=export_filename(note["title"]),
        )
