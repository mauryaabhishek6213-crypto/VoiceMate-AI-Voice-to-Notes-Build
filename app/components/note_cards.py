import reflex as rx

from app.components.workspace import PRIMARY, SECONDARY
from app.states.notes_state import NotesState
from app.components.preferences import tr


def category_icon(category: str) -> rx.Component:
    return rx.match(
        category,
        (
            "Personal",
            rx.icon("flower-2", class_name="h-5 w-5 text-[var(--vm-accent)]"),
        ),
        (
            "Work",
            rx.icon(
                "briefcase-business",
                class_name="h-5 w-5 text-[var(--vm-accent)]",
            ),
        ),
        (
            "Learning",
            rx.icon("book-open", class_name="h-5 w-5 text-[var(--vm-accent)]"),
        ),
        rx.icon("lightbulb", class_name="h-5 w-5 text-[var(--vm-accent)]"),
    )


def note_card(note: dict[str, str | bool]) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                category_icon(note["category"].to(str)),
                rx.el.span(
                    tr(note["category"].to(str)),
                    class_name="text-xs font-medium text-[var(--vm-muted)]",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.button(
                rx.icon(
                    "star",
                    class_name=rx.cond(
                        note["favorite"].to(bool),
                        "h-4 w-4 fill-[#6757C8] text-[var(--vm-accent)]",
                        "h-4 w-4 text-[#AAA2B2]",
                    ),
                ),
                aria_label=rx.cond(
                    note["favorite"].to(bool),
                    f"Remove {note['title'].to(str)} from favorites",
                    f"Favorite {note['title'].to(str)}",
                ),
                aria_pressed=note["favorite"].to(bool),
                on_click=NotesState.toggle_favorite(note["id"].to(str)),
                disabled=NotesState.saving,
                class_name="flex h-9 w-9 items-center justify-center rounded-full transition hover:bg-[#EDE7FA] focus-visible:outline-2 focus-visible:outline-[#6757C8] disabled:opacity-50",
            ),
            class_name="flex items-center justify-between",
        ),
        rx.el.a(
            rx.el.h3(
                note["title"].to(str),
                class_name="mt-3 line-clamp-2 break-words text-lg font-semibold tracking-tight text-[var(--vm-ink)]",
            ),
            rx.el.p(
                note["preview"].to(str),
                class_name="mt-2 min-h-16 line-clamp-3 break-words text-sm leading-6 text-[var(--vm-muted)]",
            ),
            rx.el.div(
                rx.el.span(
                    rx.icon("clock-3", class_name="h-3.5 w-3.5"),
                    note["date"].to(str),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.span(note["words"].to(str)),
                class_name="mt-6 flex items-center justify-between gap-2 border-t border-[#EEE9E2] pt-4 text-[11px] text-[#9A929E]",
            ),
            href=f"/notes/{note['id'].to(str)}",
            class_name="block rounded-xl focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#6757C8]",
        ),
        key=note["id"].to(str),
        class_name="group w-full rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-5 transition duration-200 hover:border-[#BDB0E4] sm:p-6",
    )


def empty_notebook() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "notebook-pen", class_name="h-9 w-9 text-[var(--vm-accent)]"
                ),
                class_name="flex h-20 w-20 -rotate-6 items-center justify-center rounded-3xl border border-[#DDD3F3] bg-[#EEE7FA]",
            ),
            rx.el.span(
                rx.icon(
                    "sparkles", class_name="h-4 w-4 text-[var(--vm-accent)]"
                ),
                class_name="absolute -right-2 top-0 rounded-full bg-[var(--vm-page)] p-2",
            ),
            class_name="relative mx-auto mb-6 w-fit",
        ),
        rx.el.h3(
            tr("Your next thought belongs here"),
            class_name="text-xl font-semibold tracking-tight text-[var(--vm-ink)]",
        ),
        rx.el.p(
            tr(
                "A passing idea, a lesson learned, a plan for tomorrow. Start with a few words and make it your own."
            ),
            class_name="mx-auto mt-3 max-w-sm text-sm leading-6 text-[var(--vm-muted)]",
        ),
        rx.el.button(
            rx.icon("plus", class_name="h-4 w-4"),
            tr("Write your first note"),
            on_click=NotesState.go("/notes/new"),
            disabled=NotesState.storage_invalid,
            class_name=PRIMARY,
        ),
        class_name="flex flex-col items-center gap-5 rounded-3xl border border-dashed border-[#DCD4E4] bg-[var(--vm-card)]/70 px-6 py-12 text-center",
    )


def no_matches() -> rx.Component:
    return rx.el.div(
        rx.icon("search", class_name="mx-auto mb-5 h-9 w-9 text-[#B1A5CC]"),
        rx.el.h3(
            rx.cond(
                NotesState.view == "favorites",
                tr("A space for your favorites"),
                tr("No notes found"),
            ),
            class_name="text-xl font-semibold text-[var(--vm-ink)]",
        ),
        rx.el.p(
            rx.cond(
                NotesState.view == "favorites",
                tr(
                    "Star a note to keep it close. If you've already starred notes, try changing your filters."
                ),
                tr(
                    "Try another word or category. Your next idea might be a new note."
                ),
            ),
            class_name="mx-auto mt-3 max-w-sm text-sm leading-6 text-[var(--vm-muted)]",
        ),
        rx.el.div(
            rx.el.button(
                tr("Reset filters"),
                on_click=NotesState.clear_filters,
                class_name=SECONDARY,
            ),
            rx.cond(
                NotesState.view == "favorites",
                rx.el.button(
                    tr("Browse notes"),
                    on_click=NotesState.go("/notes"),
                    class_name=PRIMARY,
                ),
                rx.el.button(
                    tr("New note"),
                    on_click=NotesState.go("/notes/new"),
                    disabled=NotesState.storage_invalid,
                    class_name=PRIMARY,
                ),
            ),
            class_name="mt-6 flex flex-wrap justify-center gap-3",
        ),
        class_name="rounded-3xl border border-dashed border-[#DCD4E4] bg-[var(--vm-card)]/70 px-6 py-12 text-center",
    )
