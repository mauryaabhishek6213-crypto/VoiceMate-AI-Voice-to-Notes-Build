import reflex as rx

import json
import logging
from datetime import datetime, timezone
from typing import Any, TypedDict
from uuid import uuid4


class Note(TypedDict):
    id: str
    title: str
    content: str
    category: str
    favorite: bool
    created_at: str
    updated_at: str


CATEGORIES = ["Personal", "Work", "Learning", "Ideas"]
STORAGE_KEY = "voicemate.notes.v1"
MAX_STORAGE_BYTES = 3_500_000


def decode_notes(raw: str) -> list[Note]:
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Notes must be a list.")
    notes: list[Note] = []
    ids: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Invalid note.")
        for key in (
            "id",
            "title",
            "content",
            "category",
            "created_at",
            "updated_at",
        ):
            if not isinstance(item.get(key), str):
                raise ValueError("Invalid note field.")
        if (
            type(item.get("favorite")) is not bool
            or not item["id"]
            or item["id"] in ids
        ):
            raise ValueError("Invalid note identity.")
        if item["category"] not in CATEGORIES:
            raise ValueError("Invalid category.")
        for key in ("created_at", "updated_at"):
            timestamp = datetime.fromisoformat(item[key])
            if timestamp.tzinfo is None:
                raise ValueError("Missing timestamp timezone.")
        ids.add(item["id"])
        notes.append(
            Note(
                id=item["id"],
                title=item["title"],
                content=item["content"],
                category=item["category"],
                favorite=item["favorite"],
                created_at=item["created_at"],
                updated_at=item["updated_at"],
            )
        )
    return notes


def serialize_notes(notes: list[Note]) -> str:
    raw = json.dumps(notes, ensure_ascii=False, separators=(",", ":"))
    if len(raw.encode("utf-8")) > MAX_STORAGE_BYTES:
        raise ValueError(
            "Your notebook is getting full. Shorten a note or delete notes you no longer need, then try again."
        )
    return raw


def upsert_note(
    notes: list[Note],
    note_id: str,
    title: str,
    content: str,
    category: str,
    favorite: bool,
) -> tuple[list[Note], Note]:
    if category not in CATEGORIES:
        raise ValueError("Choose a valid category.")
    if not title.strip() and not content.strip():
        raise ValueError("Add a title or some text before saving your note.")
    if len(title.strip()) > 160 or len(content) > 100_000:
        raise ValueError(
            "Use a title under 160 characters and note text under 100,000 characters."
        )
    existing = next((n for n in notes if n["id"] == note_id), None)
    if note_id and existing is None:
        raise ValueError(
            "This note no longer exists. Return to your notes and create a new one."
        )
    now = datetime.now(timezone.utc).isoformat()
    note = Note(
        id=note_id or str(uuid4()),
        title=title.strip() or "Untitled note",
        content=content,
        category=category,
        favorite=favorite,
        created_at=existing["created_at"] if existing else now,
        updated_at=now,
    )
    return [n for n in notes if n["id"] != note["id"]] + [note], note


def remove_note(notes: list[Note], note_id: str) -> list[Note]:
    if not any(n["id"] == note_id for n in notes):
        raise ValueError("This note has already been deleted.")
    return [n for n in notes if n["id"] != note_id]


def filter_notes(
    notes: list[Note],
    query: str,
    category: str,
    favorites_only: bool,
    sorting: str,
) -> list[Note]:
    query = query.strip().casefold()
    filtered = [
        n
        for n in notes
        if (not query or query in f"{n['title']} {n['content']}".casefold())
        and (category == "All notes" or n["category"] == category)
        and (not favorites_only or n["favorite"])
    ]
    if sorting == "Title A–Z":
        return sorted(filtered, key=lambda n: n["title"].casefold())
    key = "created_at" if sorting == "Newest created" else "updated_at"
    return sorted(
        filtered, key=lambda n: n[key], reverse=sorting != "Oldest updated"
    )


def display_date(value: str) -> str:
    return datetime.fromisoformat(value).strftime("%b %d, %Y")


class NotesState(rx.State):
    stored_notes: str = rx.LocalStorage("[]", name=STORAGE_KEY, sync=True)
    categories: list[str] = CATEGORIES
    filters: list[str] = ["All notes", *CATEGORIES]
    sort_options: list[str] = [
        "Recently updated",
        "Newest created",
        "Oldest updated",
        "Title A–Z",
    ]
    query: str = ""
    displayed_limit: int = 48
    category_filter: str = "All notes"
    sorting: str = "Recently updated"
    view: str = "home"
    ready: bool = False
    editing_id: str = ""
    draft_title: str = ""
    draft_content: str = ""
    draft_category: str = "Personal"
    draft_favorite: bool = False
    editor_key: int = 0
    editor_missing: bool = False
    created_label: str = ""
    updated_label: str = ""
    feedback: str = ""
    error: str = ""
    saving: bool = False
    delete_id: str = ""
    delete_title: str = ""
    leave_open: bool = False
    pending_route: str = ""
    capture_saved_id: str = ""
    _previous_raw: str = "[]"
    _expected_raw: str = ""
    _saved_id: str = ""
    _deleted_id: str = ""

    @rx.var(backend=True)
    def notes(self) -> list[Note]:
        try:
            return decode_notes(self.stored_notes)
        except (ValueError, TypeError, KeyError):
            logging.exception("Unexpected error")
            return []

    @rx.var
    def storage_invalid(self) -> bool:
        try:
            decode_notes(self.stored_notes)
            return False
        except (ValueError, TypeError, KeyError):
            logging.exception("Unexpected error")
            return True

    @rx.var
    def note_count(self) -> int:
        return len(self.notes)

    @rx.var
    def favorite_count(self) -> int:
        return sum(n["favorite"] for n in self.notes)

    def _matching_notes(self) -> list[Note]:
        return filter_notes(
            self.notes,
            self.query,
            self.category_filter,
            self.view == "favorites",
            self.sorting,
        )

    @rx.var
    def matched_count(self) -> int:
        return len(self._matching_notes())

    @rx.var
    def visible_notes(self) -> list[dict[str, str | bool]]:
        return self._cards(self._matching_notes()[: self.displayed_limit])

    @rx.event
    def load_more(self):
        self.displayed_limit = min(
            self.displayed_limit + 48, max(48, self.matched_count)
        )

    @rx.var
    def recent_notes(self) -> list[dict[str, str | bool]]:
        return self._cards(
            filter_notes(
                self.notes, "", "All notes", False, "Recently updated"
            )[:4]
        )

    @rx.var
    def category_counts(self) -> list[dict[str, str | int]]:
        return [
            {"name": c, "count": sum(n["category"] == c for n in self.notes)}
            for c in CATEGORIES
        ]

    def _cards(self, notes: list[Note]) -> list[dict[str, str | bool]]:
        return [
            {
                "id": n["id"],
                "title": n["title"],
                "preview": " ".join(n["content"].split())[:180]
                or "A little space for your next thought.",
                "category": n["category"],
                "favorite": n["favorite"],
                "date": display_date(n["updated_at"]),
                "words": f"{len(n['content'].split())} words",
            }
            for n in notes
        ]

    @rx.event
    def load_home(self):
        self.view = "home"
        self._load()

    @rx.event
    def load_library(self):
        self.view = "notes"
        self._load()

    @rx.event
    def load_favorites(self):
        self.view = "favorites"
        self._load()

    def _load(self):
        self.displayed_limit = 48
        self.ready = True
        self.error = ""
        self.feedback = ""
        self.delete_id = ""
        self.leave_open = False
        self.saving = False

    @rx.event
    def load_record(self):
        self._load()
        self.view = "record"
        self.capture_saved_id = ""

    @rx.event
    def save_transcript(self, title: str, content: str, category: str):
        if (
            self.saving
            or self.capture_saved_id
            or self.view not in ("record", "import")
        ):
            return
        try:
            if not content.strip():
                raise ValueError("Add some transcript text before saving.")
            notes, note = upsert_note(
                decode_notes(self.stored_notes),
                "",
                title,
                content,
                category,
                False,
            )
            self._commit(notes)
            self._saved_id = note["id"]
        except (ValueError, TypeError, KeyError) as e:
            logging.exception(f"Error: {e}")
            self.error = (
                "Stored notes couldn't be read. Nothing has been overwritten."
                if self.storage_invalid
                else str(e)
            )
            self.feedback = ""
            return
        yield
        yield self._verification_event()

    @rx.event
    def load_new(self):
        self._load()
        self.view = "editor"
        self.editing_id = ""
        self.draft_title = ""
        self.draft_content = ""
        self.draft_category = "Personal"
        self.draft_favorite = False
        self.created_label = ""
        self.updated_label = ""
        self.editor_missing = False
        self.editor_key += 1

    @rx.event
    def load_editor(self):
        self._load()
        self.view = "editor"
        note = next((n for n in self.notes if n["id"] == self.note_id), None)
        self.editor_missing = note is None
        if note:
            self._set_draft(note)

    def _set_draft(self, note: Note):
        self.editing_id = note["id"]
        self.draft_title = note["title"]
        self.draft_content = note["content"]
        self.draft_category = note["category"]
        self.draft_favorite = note["favorite"]
        self.created_label = display_date(note["created_at"])
        self.updated_label = display_date(note["updated_at"])
        self.editor_key += 1

    @rx.event
    def search(self, value: str):
        self.displayed_limit = 48
        self.query = value

    @rx.event
    def choose_category(self, category: str):
        if category in self.filters:
            self.displayed_limit = 48
            self.category_filter = category

    @rx.event
    def choose_sort(self, value: str):
        if value in self.sort_options:
            self.displayed_limit = 48
            self.sorting = value

    @rx.event
    def clear_filters(self):
        self.displayed_limit = 48
        self.query = ""
        self.category_filter = "All notes"
        self.sorting = "Recently updated"

    @rx.event
    def browse_category(self, category: str):
        self.displayed_limit = 48
        self.category_filter = category
        self.query = ""
        return rx.redirect("/notes")

    @rx.event
    def go(self, route: str):
        self.pending_route = route
        if self.view == "editor" and not self.editor_missing:
            return rx.call_script(
                "(() => { const form = document.getElementById('note-editor'); return form ? JSON.stringify(Object.fromEntries(new FormData(form))) : '{}'; })()",
                callback=NotesState.check_leave,
            )
        self.query = ""
        self.category_filter = "All notes"
        return rx.redirect(route)

    @rx.event
    def check_leave(self, result: str):
        data = json.loads(result)
        changed = (
            str(data.get("title", "")) != self.draft_title
            or str(data.get("content", "")) != self.draft_content
            or str(data.get("category", "Personal")) != self.draft_category
            or (data.get("favorite") == "on") != self.draft_favorite
        )
        if changed:
            self.leave_open = True
        else:
            self.query = ""
            self.category_filter = "All notes"
            return rx.redirect(self.pending_route)

    @rx.event
    def stay(self):
        self.leave_open = False

    @rx.event
    def discard_and_leave(self):
        self.leave_open = False
        self.query = ""
        self.category_filter = "All notes"
        return rx.redirect(self.pending_route)

    def _commit(self, notes: list[Note]):
        raw = serialize_notes(notes)
        self._previous_raw = self.stored_notes
        self._expected_raw = raw
        self.stored_notes = raw
        self.saving = True
        self.error = ""
        self.feedback = "Saving to this browser…"

    def _verification_event(self):
        return rx.call_script(
            "(() => { try { return localStorage.getItem('voicemate.notes.v1') || ''; } catch (_) { return '__unavailable__'; } })()",
            callback=NotesState.verify_storage,
        )

    @rx.event
    def verify_storage(self, result: str):
        self.saving = False
        if result != self._expected_raw:
            self.stored_notes = self._previous_raw
            self.error = "We couldn't confirm the save in this browser. Keep this page open and try again. Check that browser storage is enabled and has space."
            self.feedback = ""
        else:
            self.feedback = "Saved in this browser"
            if self.view in ("record", "import"):
                self.capture_saved_id = self._saved_id
            if self.view == "editor":
                note = next(
                    (n for n in self.notes if n["id"] == self._saved_id), None
                )
                if note:
                    self._set_draft(note)

    @rx.event
    def save_note(self, form_data: dict[str, Any]):
        if self.saving:
            return
        try:
            notes = decode_notes(self.stored_notes)
            notes, note = upsert_note(
                notes,
                self.editing_id,
                str(form_data.get("title", "")),
                str(form_data.get("content", "")),
                str(form_data.get("category", "Personal")),
                form_data.get("favorite") == "on",
            )
            self._commit(notes)
            self._saved_id = note["id"]
        except (ValueError, TypeError, KeyError) as e:
            logging.exception(f"Error: {e}")
            self.error = (
                str(e)
                if not self.storage_invalid
                else "Stored notes couldn't be read. Nothing has been overwritten."
            )
            self.feedback = ""
            return
        yield
        yield self._verification_event()

    @rx.event
    def toggle_favorite(self, note_id: str):
        if self.saving:
            return
        try:
            notes = decode_notes(self.stored_notes)
            note = next((n for n in notes if n["id"] == note_id), None)
            if note is None:
                raise ValueError("This note no longer exists.")
            note["favorite"] = not note["favorite"]
            self._commit(notes)
        except (ValueError, TypeError, KeyError) as e:
            logging.exception(f"Error: {e}")
            self.error = "Couldn't update this note. Reload and try again."
            return
        yield
        yield self._verification_event()

    @rx.event
    def request_delete(self):
        self.delete_id = self.editing_id
        self.delete_title = self.draft_title

    @rx.event
    def cancel_delete(self):
        self.delete_id = ""

    @rx.event
    def confirm_delete(self):
        if self.saving:
            return
        try:
            self._commit(
                remove_note(decode_notes(self.stored_notes), self.delete_id)
            )
            self._deleted_id = self.delete_id
            self.delete_id = ""
        except (ValueError, TypeError, KeyError) as e:
            logging.exception(f"Error: {e}")
            self.error = "Couldn't delete this note. Reload and try again."
            return
        yield
        yield rx.call_script(
            "(() => { try { return localStorage.getItem('voicemate.notes.v1') || ''; } catch (_) { return '__unavailable__'; } })()",
            callback=NotesState.verify_delete,
        )

    @rx.event
    async def verify_delete(self, result: str):
        self.saving = False
        if result != self._expected_raw:
            self.stored_notes = self._previous_raw
            self.error = "Deletion couldn't be saved in this browser. Your note has been kept."
            self.feedback = ""
        else:
            from app.states.ai_state import AIState

            assistant = await self.get_state(AIState)
            assistant._clear_note_results(self._deleted_id)
            self._deleted_id = ""
            self.feedback = "Note deleted"
            yield
            yield rx.call_script(
                "(() => { try { const raw = localStorage.getItem('voicemate.notes.v1') || '[]'; const ids = new Set(JSON.parse(raw).map(n => n.id)); const key = 'voicemate.ai-results.v1'; const results = JSON.parse(localStorage.getItem(key) || '[]'); if (Array.isArray(results)) localStorage.setItem(key, JSON.stringify(results.filter(r => ids.has(r.note_id)))); } catch (_) {} })()"
            )
            yield rx.redirect("/notes")
