import reflex as rx

import asyncio
import json
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from uuid import NAMESPACE_URL, uuid5

import pytest
from test_utils import run_event

from app.pages.audio_import import SEND_SCRIPT
from app.states.import_state import ImportState
from app.states.notes_state import (
    CATEGORIES,
    Note,
    NotesState,
    filter_notes,
    serialize_notes,
)
from app.states.record_state import POLL_SCRIPT, RecordState


@pytest.fixture(autouse=True)
def reset_shared_test_defaults():
    def restore_defaults():
        imported = ImportState()
        imported.unavailable = ""
        imported.transcript = ""
        imported.error = ""
        imported.feedback = ""
        imported.busy = False
        imported.revision = 0
        imported.token = ""
        imported.endpoint = ""

        notes = NotesState()
        notes.stored_notes = "[]"
        notes.categories = CATEGORIES.copy()
        notes.filters = ["All notes", *CATEGORIES]
        notes.sort_options = [
            "Recently updated",
            "Newest created",
            "Oldest updated",
            "Title A–Z",
        ]
        notes.query = ""
        notes.displayed_limit = 48
        notes.category_filter = "All notes"
        notes.sorting = "Recently updated"
        notes.view = "home"
        notes.ready = False
        notes.editing_id = ""
        notes.draft_title = ""
        notes.draft_content = ""
        notes.draft_category = "Personal"
        notes.draft_favorite = False
        notes.editor_key = 0
        notes.editor_missing = False
        notes.created_label = ""
        notes.updated_label = ""
        notes.feedback = ""
        notes.error = ""
        notes.saving = False
        notes.delete_id = ""
        notes.delete_title = ""
        notes.leave_open = False
        notes.pending_route = ""
        notes.capture_saved_id = ""
        notes._previous_raw = "[]"
        notes._expected_raw = ""
        notes._saved_id = ""
        notes._deleted_id = ""

    restore_defaults()
    try:
        yield
    finally:
        restore_defaults()


def assembled_send() -> str:
    return f'(async () => {{ const TOKEN="session"; const ENDPOINT="/api"; const LANGUAGE="en"; const UNAVAILABLE=""; {SEND_SCRIPT} }})()'


def node_run(source: str, check: bool = False):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for browser script regression tests")
    command = [node, "--check"] if check else [node]
    result = subprocess.run(
        command, input=source, text=True, capture_output=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_assembled_audio_send_syntax():
    node_run(assembled_send(), check=True)


@pytest.mark.parametrize(
    "mode",
    [
        "missing",
        "consent",
        "mime",
        "network",
        "json",
        "error",
        "timeout",
        "success",
        "preflight",
    ],
)
def test_audio_send_completes_and_restores_controls(mode):
    setup = r"""
const assert = require('node:assert/strict');
global.window = {};
const file = {name:'clip.mp3', size:12, type:'audio/mpeg'};
const field = {files:[file], disabled:false};
const consent = {checked:true, disabled:false};
const button = {disabled:false};
const status = {textContent:''};
global.document = {getElementById(id) { return {'audio-file':field, 'audio-consent':consent, 'audio-send':button, 'audio-client-status':status}[id]; }};
let calls = 0;
if (MODE === 'missing') field.files = [];
if (MODE === 'consent') consent.checked = false;
if (MODE === 'mime') file.type = 'text/plain';
if (MODE === 'preflight') Object.defineProperty(field, 'files', {get() {throw new Error('preflight');}});
global.fetch = async () => {
    calls++;
    assert.equal(button.disabled, true);
    assert.equal(consent.checked, false);
    if (MODE === 'network') throw new Error('offline');
    if (MODE === 'timeout') throw Object.assign(new Error('timeout'), {name:'AbortError'});
    return {ok:MODE !== 'error', json:async () => {
        if (MODE === 'json') throw new SyntaxError('bad json');
        return MODE === 'error' ? {error:{message:'quota unavailable'}} : {transcript:'Recognized words'};
    }};
};
"""
    source = f"const MODE={json.dumps(mode)};\n{setup}\n{assembled_send()}.then(raw => {{ const data=JSON.parse(raw); assert.equal(data.token,'session'); assert.equal(window.vmAudioAbort,null); assert.equal(button.disabled,false); assert.equal(field.disabled,false); assert.equal(consent.disabled,false); assert.equal(consent.checked,false); assert.equal(typeof data[MODE === 'success' ? 'transcript' : 'error'],'string'); console.log(raw); }});"
    raw = node_run(source).strip()
    state = ImportState()
    state.token = "session"
    state.busy = True
    asyncio.run(run_event(state.receive, raw))
    assert ~state.busy
    assert (state.transcript != "") == (mode == "success")
    assert (state.error != "") == (mode != "success")


def test_audio_duplicate_does_not_fetch_or_clear_active_busy():
    source = f"global.window={{vmAudioAbort:{{}}}}; global.fetch=()=>{{throw new Error('duplicate fetch')}}; {assembled_send()}.then(raw=>console.log(raw));"
    raw = node_run(source).strip()
    state = ImportState()
    state.token = "session"
    state.busy = True
    state.error = "kept"
    asyncio.run(run_event(state.begin))
    assert state.error == "kept"
    asyncio.run(run_event(state.receive, raw))
    assert state.busy
    asyncio.run(
        run_event(
            state.receive,
            json.dumps({"token": "session", "error": "quota unavailable"}),
        )
    )
    assert ~state.busy
    assert state.error == "quota unavailable"
    assert state.transcript == ""


@pytest.fixture
def notebook():
    topics = (
        "Weekend walking plans",
        "Project planning meeting",
        "Language practice reflections",
        "Notebook design ideas",
    )
    paragraph = (
        "Review the week's progress and record the next steps. "
        "Keep useful observations together, make time for focused practice, "
        "and revisit the plan after discussing priorities with the team. "
    )
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    notes = []
    for i in range(125):
        stamp = (start + timedelta(minutes=i)).isoformat()
        notes.append(
            Note(
                id=str(
                    uuid5(NAMESPACE_URL, f"https://voicemate.example/notes/{i}")
                ),
                title=f"{topics[i % len(topics)]} — entry {i + 1}",
                content=f"{paragraph * 4}Reference: deep-search-marker",
                category=CATEGORIES[i % 4],
                favorite=i % 2 == 0,
                created_at=stamp,
                updated_at=stamp,
            )
        )
    state = NotesState()
    state.stored_notes = serialize_notes(notes)
    state.load_library()
    return state, notes


def test_pagination_count_order_and_storage_unchanged(notebook):
    state, notes = notebook
    raw = state.stored_notes
    expected = filter_notes(notes, "", "All notes", False, "Recently updated")
    assert state.matched_count == 125
    assert len(state.visible_notes) == 48
    state.load_more()
    assert len(state.visible_notes) == 96
    state.load_more()
    assert len(state.visible_notes) == 125
    state.load_more()
    assert [n["id"] for n in state.visible_notes] == [n["id"] for n in expected]
    assert state.stored_notes == raw
    state.load_favorites()
    assert state.displayed_limit == 48
    assert state.matched_count == 63
    state.load_more()
    assert len(state.visible_notes) == 63
    assert all(n["favorite"] for n in state.visible_notes)
    state.load_library()
    assert len(state.visible_notes) == 48
    assert state.stored_notes == raw


def test_search_filters_sort_and_reset(notebook):
    state, notes = notebook
    raw = state.stored_notes
    state.load_more()
    state.search("DEEP-SEARCH-MARKER")
    assert state.matched_count == 125
    assert len(state.visible_notes) == 48
    assert all(
        "deep-search-marker" not in n["preview"] for n in state.visible_notes
    )
    for sorting in state.sort_options:
        state.load_more()
        state.choose_sort(sorting)
        expected = filter_notes(
            notes, state.query, state.category_filter, False, sorting
        )
        assert state.displayed_limit == 48
        assert [n["id"] for n in state.visible_notes] == [
            n["id"] for n in expected[:48]
        ]
    state.load_more()
    state.choose_category("Work")
    assert state.displayed_limit == 48
    assert state.matched_count == 31
    assert all(n["category"] == "Work" for n in state.visible_notes)
    state.load_favorites()
    assert state.matched_count == 0
    assert state.visible_notes == []
    state.clear_filters()
    assert state.matched_count == 63
    assert state.displayed_limit == 48
    state.search("unmatched-unique-token")
    assert state.matched_count == 0
    assert state.visible_notes == []
    state.clear_filters()
    state.search(notes[0]["title"])
    assert notes[0]["id"] in [n["id"] for n in state.visible_notes]
    state.browse_category("Ideas")
    assert state.displayed_limit == 48
    state.load_home()
    assert state.displayed_limit == 48
    assert state.stored_notes == raw


def test_speech_poll_one_second_and_live_state():
    assert ", 1000))" in POLL_SCRIPT
    state = RecordState()
    state.token = "session"
    state.status = "listening"
    asyncio.run(
        run_event(
            state.receive,
            json.dumps(
                {
                    "token": "session",
                    "supported": True,
                    "status": "listening",
                    "text": "Final words",
                    "interim": "live words",
                    "elapsed": 61,
                    "error": "",
                }
            ),
        )
    )
    assert state.active
    assert state.transcript == "Final words"
    assert state.interim == "live words"
    assert state.timer_label == "01:01"
    asyncio.run(
        run_event(
            state.receive,
            json.dumps(
                {
                    "token": "session",
                    "supported": True,
                    "status": "error",
                    "text": "Final words",
                    "interim": "",
                    "elapsed": 61,
                    "error": "network",
                }
            ),
        )
    )
    assert ~state.active
    assert state.transcript == "Final words"
    assert state.error
