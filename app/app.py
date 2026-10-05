import reflex as rx


from app.pages.home import home
from app.pages.library import library
from app.pages.editor import editor
from app.pages.record import record
from app.states.record_state import RecordState
from app.states.notes_state import NotesState
from app.pages.audio_import import audio_import
from app.pages.settings import settings
from app.states.import_state import ImportState
from app.states.settings_state import SettingsState
from app.audio_service import audio_endpoint
from app.ai_api import RequestGuard


def index() -> rx.Component:
    return home()


def configure_audio_api(api):
    api.add_route("/api/v1/audio/transcribe", audio_endpoint, methods=["POST"])
    api.add_middleware(
        RequestGuard, token="", public=False, requests_per_minute=10
    )
    return api


app = rx.App(
    api_transformer=configure_audio_api,
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            cross_origin="",
        ),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(
    index,
    route="/",
    title="VoiceMate · Your personal notebook",
    on_load=NotesState.load_home,
)
app.add_page(
    editor,
    route="/notes/[note_id]",
    title="VoiceMate · Edit note",
    on_load=NotesState.load_editor,
)
app.add_page(
    editor,
    route="/notes/new",
    title="VoiceMate · New note",
    on_load=NotesState.load_new,
)
app.add_page(
    library,
    route="/notes",
    title="VoiceMate · My notes",
    on_load=NotesState.load_library,
)
app.add_page(
    record,
    route="/record",
    title="VoiceMate · Speech capture",
    on_load=RecordState.load_record,
)
app.add_page(
    settings,
    route="/settings",
    title="VoiceMate · Settings",
    on_load=SettingsState.load_settings,
)
app.add_page(
    audio_import,
    route="/import",
    title="VoiceMate · Import audio",
    on_load=ImportState.load_import,
)
app.add_page(
    library,
    route="/favorites",
    title="VoiceMate · Favorites",
    on_load=NotesState.load_favorites,
)
