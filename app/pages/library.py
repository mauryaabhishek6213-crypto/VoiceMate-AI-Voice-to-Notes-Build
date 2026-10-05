import reflex as rx

from app.components.note_cards import empty_notebook, no_matches, note_card
from app.components.workspace import PRIMARY, SECONDARY, shell
from app.states.notes_state import NotesState
from app.components.preferences import tr


def filter_chip(category: str) -> rx.Component:
    return rx.el.button(
        tr(category),
        on_click=NotesState.choose_category(category),
        aria_pressed=NotesState.category_filter == category,
        class_name=rx.cond(
            NotesState.category_filter == category,
            "shrink-0 rounded-full border border-[#6757C8] bg-[#6757C8] px-4 py-2.5 text-xs font-medium text-white transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#6757C8]",
            "shrink-0 rounded-full border border-[var(--vm-border)] bg-[var(--vm-card)] px-4 py-2.5 text-xs font-medium text-[var(--vm-muted)] transition hover:border-[#BDB0E4] hover:bg-[#F0EAF8] focus-visible:outline-2 focus-visible:outline-[#6757C8]",
        ),
    )


def library() -> rx.Component:
    return shell(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        tr("YOUR NOTEBOOK"),
                        class_name="mb-3 text-[10px] font-semibold tracking-[0.22em] text-[#9A8FB0]",
                    ),
                    rx.el.h1(
                        rx.cond(
                            NotesState.view == "favorites",
                            tr("Keep your favorites close."),
                            tr("Every thought, in one place."),
                        ),
                        class_name="font-['DM_Sans'] text-3xl font-semibold leading-tight tracking-tight text-[var(--vm-ink)] sm:text-4xl",
                    ),
                    rx.el.p(
                        rx.cond(
                            NotesState.view == "favorites",
                            tr(
                                "The ideas you want to come back to, collected here."
                            ),
                            tr(
                                "Find a thought, revisit an idea, or start something new."
                            ),
                        ),
                        class_name="mt-3 text-sm leading-6 text-[var(--vm-muted)]",
                    ),
                ),
                rx.el.button(
                    rx.icon("plus", class_name="h-4 w-4"),
                    tr("New note"),
                    on_click=NotesState.go("/notes/new"),
                    disabled=NotesState.storage_invalid,
                    class_name=PRIMARY,
                ),
                class_name="flex flex-col items-start justify-between gap-5 sm:flex-row sm:items-center",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "search",
                        class_name="pointer-events-none absolute top-3.5 left-4 h-5 w-5 text-[#A096AD]",
                    ),
                    rx.el.input(
                        default_value=NotesState.query,
                        on_change=NotesState.search.debounce(500),
                        placeholder=tr("Search titles and note text…"),
                        aria_label="Search notes by title or text",
                        class_name="w-full rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-card)] py-3.5 pr-4 pl-12 text-sm text-[var(--vm-ink)] placeholder:text-[#A299AA] focus:border-[#6757C8] focus:outline-2 focus:outline-[#E2D9F6]",
                    ),
                    class_name="relative w-full min-w-0 flex-1",
                ),
                rx.el.div(
                    rx.el.select(
                        rx.foreach(
                            NotesState.sort_options,
                            lambda option: rx.el.option(
                                tr(option), value=option
                            ),
                        ),
                        value=NotesState.sorting,
                        on_change=NotesState.choose_sort,
                        aria_label="Sort notes",
                        class_name="w-full appearance-none rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-card)] py-3.5 pr-10 pl-4 text-sm text-[var(--vm-muted)] focus:outline-2 focus:outline-[#6757C8]",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="pointer-events-none absolute top-4 right-3 h-4 w-4 text-[#8F859C]",
                    ),
                    class_name="relative w-full sm:w-48",
                ),
                class_name="mt-8 flex flex-col gap-3 sm:flex-row",
            ),
            rx.el.div(
                rx.foreach(NotesState.filters, filter_chip),
                aria_label="Filter by category",
                class_name="mt-5 flex gap-2 overflow-x-auto pb-2",
            ),
            rx.el.div(
                rx.el.p(
                    f"{NotesState.matched_count} {tr('notes')}",
                    class_name="text-xs font-medium text-[#8D8397]",
                ),
                rx.cond(
                    (NotesState.query != "")
                    | (NotesState.category_filter != "All notes"),
                    rx.el.button(
                        tr("Clear filters"),
                        on_click=NotesState.clear_filters,
                        class_name="rounded-lg text-xs font-medium text-[var(--vm-accent)] hover:underline focus-visible:outline-2 focus-visible:outline-[#6757C8]",
                    ),
                ),
                class_name="mt-5 mb-5 flex items-center justify-between",
                aria_live="polite",
            ),
            rx.cond(
                NotesState.visible_notes.length() > 0,
                rx.el.div(
                    rx.foreach(NotesState.visible_notes, note_card),
                    class_name="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3",
                ),
                rx.cond(
                    (NotesState.note_count == 0)
                    & (NotesState.view != "favorites")
                    & (NotesState.query == "")
                    & (NotesState.category_filter == "All notes"),
                    empty_notebook(),
                    no_matches(),
                ),
            ),
            rx.cond(
                NotesState.visible_notes.length() < NotesState.matched_count,
                rx.el.div(
                    rx.el.button(
                        tr("Load more"),
                        type="button",
                        on_click=NotesState.load_more,
                        class_name=SECONDARY,
                    ),
                    class_name="mt-6 flex justify-center",
                ),
            ),
        )
    )
