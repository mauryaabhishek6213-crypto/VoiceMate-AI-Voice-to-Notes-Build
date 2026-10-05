import reflex as rx

from app.components.workspace import PRIMARY, SECONDARY, shell
from app.components.ai_assistant import ai_assistant
from app.states.notes_state import NotesState
from app.components.preferences import tr
from app.components.note_export import note_export


FIELD = "w-full rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-card)] px-4 py-3 text-sm text-[var(--vm-ink)] placeholder:text-[#A299AA] focus:border-[#6757C8] focus:outline-2 focus:outline-[#E2D9F6]"


def editor_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    tr("Note title"),
                    html_for="note-title",
                    class_name="mb-2 block text-xs font-semibold text-[var(--vm-muted)]",
                ),
                rx.el.input(
                    name="title",
                    id="note-title",
                    default_value=NotesState.draft_title,
                    key=NotesState.draft_title,
                    max_length=160,
                    placeholder=tr("Give this thought a name…"),
                    auto_focus=True,
                    class_name="w-full border-0 bg-transparent py-2 font-['DM_Sans'] text-2xl font-semibold tracking-tight text-[var(--vm-ink)] placeholder:text-[#B4AABD] focus:outline-2 focus:outline-[#E2D9F6] sm:text-3xl",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.label(
                rx.el.input(
                    type="checkbox",
                    name="favorite",
                    default_checked=NotesState.draft_favorite,
                    class_name="h-4 w-4 accent-[#6757C8]",
                ),
                rx.icon("star", class_name="h-4 w-4 text-[var(--vm-accent)]"),
                tr("Favorite"),
                class_name="flex w-fit cursor-pointer items-center gap-2 rounded-full border border-[var(--vm-border)] bg-[var(--vm-lavender)] px-4 py-2.5 text-xs font-medium text-[var(--vm-accent)]",
            ),
            class_name="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center",
        ),
        rx.el.div(
            rx.el.label(
                tr("Category"),
                html_for="note-category",
                class_name="text-xs font-semibold text-[var(--vm-muted)]",
            ),
            rx.el.div(
                rx.el.select(
                    rx.foreach(
                        NotesState.categories,
                        lambda category: rx.el.option(
                            tr(category), value=category
                        ),
                    ),
                    id="note-category",
                    name="category",
                    default_value=NotesState.draft_category,
                    class_name="w-full appearance-none rounded-xl border border-[var(--vm-border)] bg-[var(--vm-card)] py-2.5 pr-10 pl-3 text-sm text-[var(--vm-muted)] focus:outline-2 focus:outline-[#6757C8]",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="pointer-events-none absolute top-3 right-3 h-4 w-4 text-[#8F859C]",
                ),
                class_name="relative w-40",
            ),
            class_name="mt-6 flex items-center gap-4",
        ),
        rx.el.div(
            rx.el.label(
                tr("Note text / transcript"),
                html_for="note-content",
                class_name="text-xs font-semibold text-[var(--vm-muted)]",
            ),
            rx.el.span(
                tr("Editable · plain text"),
                class_name="text-[11px] text-[#A096AA]",
            ),
            class_name="mt-7 mb-3 flex items-center justify-between gap-3 border-t border-[#EEE8E0] pt-6",
        ),
        rx.el.textarea(
            name="content",
            id="note-content",
            default_value=NotesState.draft_content,
            key=NotesState.draft_content,
            max_length=100000,
            placeholder=tr(
                "What's on your mind?\n\nWrite freely. This space is yours."
            ),
            class_name="min-h-72 w-full resize-y rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-field)] p-4 text-base leading-8 text-[var(--vm-ink)] placeholder:text-[#B1A7BA] focus:border-[#6757C8] focus:outline-2 focus:outline-[#E2D9F6] sm:min-h-80",
        ),
        rx.el.div(
            rx.el.p(
                tr("Changes are saved only when you tap Save note."),
                class_name="text-xs leading-5 text-[var(--vm-muted)]",
            ),
            rx.el.button(
                rx.cond(
                    NotesState.saving,
                    rx.icon("loader-circle", class_name="h-4 w-4 animate-spin"),
                    rx.icon("check", class_name="h-4 w-4"),
                ),
                rx.cond(NotesState.saving, tr("Saving…"), tr("Save note")),
                type="submit",
                disabled=NotesState.saving | NotesState.storage_invalid,
                class_name=PRIMARY,
            ),
            class_name="mt-6 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center",
        ),
        id="note-editor",
        key=NotesState.editor_key,
        on_submit=NotesState.save_note,
        on_mount=rx.call_script(
            "(() => { if (window.vmCleanup) window.vmCleanup(); const f = document.getElementById('note-editor'); if (!f) return; const initial = JSON.stringify(Object.fromEntries(new FormData(f))); const warn = e => { if (JSON.stringify(Object.fromEntries(new FormData(f))) !== initial) { e.preventDefault(); e.returnValue = ''; } }; window.addEventListener('beforeunload', warn); window.vmCleanup = () => window.removeEventListener('beforeunload', warn); })()"
        ),
        on_unmount=rx.call_script(
            "if (window.vmCleanup) { window.vmCleanup(); window.vmCleanup = null; }"
        ),
        class_name="rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-5 sm:p-8",
    )


def editor() -> rx.Component:
    return shell(
        rx.el.div(
            rx.el.button(
                rx.icon("arrow-left", class_name="h-4 w-4"),
                tr("Back to notes"),
                on_click=NotesState.go("/notes"),
                class_name="mb-6 flex items-center gap-2 rounded-lg py-1 text-xs font-medium text-[var(--vm-muted)] hover:text-[var(--vm-accent)] focus-visible:outline-2 focus-visible:outline-[#6757C8]",
            ),
            rx.cond(
                NotesState.editor_missing,
                rx.el.div(
                    rx.icon(
                        "file-question",
                        class_name="mx-auto h-10 w-10 text-[#B1A5CC]",
                    ),
                    rx.el.h1(
                        tr("This note isn't here"),
                        class_name="mt-5 text-2xl font-semibold text-[var(--vm-ink)]",
                    ),
                    rx.el.p(
                        tr(
                            "It may have been deleted, or saved in a different browser."
                        ),
                        class_name="mt-3 mb-6 text-sm text-[var(--vm-muted)]",
                    ),
                    rx.el.button(
                        tr("Return to notes"),
                        on_click=NotesState.go("/notes"),
                        class_name=PRIMARY,
                    ),
                    class_name="rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-10 text-center",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.p(
                                tr("A SPACE TO THINK"),
                                class_name="mb-3 text-[10px] font-semibold tracking-[0.22em] text-[#9A8FB0]",
                            ),
                            rx.el.h1(
                                rx.cond(
                                    NotesState.editing_id == "",
                                    tr("Start with a thought."),
                                    tr("Make this thought your own."),
                                ),
                                class_name="font-['DM_Sans'] text-3xl font-semibold tracking-tight text-[var(--vm-ink)]",
                            ),
                            rx.el.p(
                                tr(
                                    "Write, revisit, and refine. You're in no rush."
                                ),
                                class_name="mt-3 text-sm text-[var(--vm-muted)]",
                            ),
                        ),
                        rx.cond(
                            NotesState.editing_id != "",
                            rx.el.button(
                                rx.icon("trash-2", class_name="h-4 w-4"),
                                tr("Delete"),
                                on_click=NotesState.request_delete,
                                disabled=NotesState.saving,
                                class_name=SECONDARY,
                            ),
                        ),
                        class_name="mb-7 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center",
                    ),
                    editor_form(),
                    rx.cond(NotesState.editing_id != "", note_export()),
                    rx.cond(
                        NotesState.editing_id != "",
                        ai_assistant(),
                        rx.el.p(
                            tr(
                                "Save your note to unlock the optional AI assistant."
                            ),
                            class_name="mt-5 text-xs text-[var(--vm-muted)]",
                        ),
                    ),
                    rx.cond(
                        NotesState.created_label != "",
                        rx.el.div(
                            rx.el.span(f"Created {NotesState.created_label}"),
                            rx.el.span(f"Updated {NotesState.updated_label}"),
                            class_name="mt-4 flex flex-wrap gap-x-5 gap-y-2 px-1 text-[11px] text-[var(--vm-muted)]",
                        ),
                    ),
                ),
            ),
        )
    )
