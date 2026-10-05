import reflex as rx

from app.components.preferences import tr
from app.components.workspace import SECONDARY
from app.states.export_state import ExportState
from app.states.notes_state import NotesState

SAVED_SCRIPT = "const note = JSON.parse(localStorage.getItem('voicemate.notes.v1') || '[]').find(n => n.id === decodeURIComponent(location.pathname.split('/').pop())); if (!note) return 'clipboard-error'; const text = `${note.title}\\n\\n${note.content}\\n`;"
COPY_SCRIPT = f"(async () => {{ try {{ {SAVED_SCRIPT} await navigator.clipboard.writeText(text); return 'copied'; }} catch (_) {{ return 'clipboard-error'; }} }})()"
SHARE_SCRIPT = f"(async () => {{ try {{ {SAVED_SCRIPT} if (!navigator.share) return 'unavailable'; await navigator.share({{title: note.title, text}}); return 'shared'; }} catch (e) {{ return e.name === 'AbortError' ? 'cancelled' : 'share-error'; }} }})()"


def note_export() -> rx.Component:
    return rx.el.section(
        rx.el.p(
            tr("Saved version only · unsaved editor changes are not included."),
            class_name="text-xs leading-5 text-[var(--vm-muted)]",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("copy", class_name="h-4 w-4"),
                tr("Copy note"),
                type="button",
                disabled=NotesState.saving,
                on_click=rx.call_script(
                    COPY_SCRIPT, callback=ExportState.receive
                ),
                class_name=SECONDARY,
            ),
            rx.el.button(
                rx.icon("download", class_name="h-4 w-4"),
                tr("Download text"),
                type="button",
                disabled=NotesState.saving,
                on_click=ExportState.download,
                class_name=SECONDARY,
            ),
            rx.el.button(
                rx.icon("share-2", class_name="h-4 w-4"),
                tr("Share note"),
                type="button",
                disabled=NotesState.saving,
                on_click=rx.call_script(
                    SHARE_SCRIPT, callback=ExportState.receive
                ),
                class_name=SECONDARY,
            ),
            class_name="mt-3 flex flex-wrap gap-3",
        ),
        rx.el.p(
            tr(ExportState.feedback),
            role="status",
            aria_live="polite",
            class_name="mt-3 text-sm text-[var(--vm-accent)]",
        ),
        rx.cond(
            ExportState.fallback,
            rx.el.div(
                rx.el.button(
                    tr("Copy instead"),
                    on_click=rx.call_script(
                        COPY_SCRIPT, callback=ExportState.receive
                    ),
                    class_name=SECONDARY,
                ),
                rx.el.button(
                    tr("Dismiss"),
                    on_click=ExportState.dismiss,
                    class_name=SECONDARY,
                ),
                class_name="mt-3 flex flex-wrap gap-3",
            ),
        ),
        on_mount=ExportState.dismiss,
        class_name="mt-5 rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-5",
    )
