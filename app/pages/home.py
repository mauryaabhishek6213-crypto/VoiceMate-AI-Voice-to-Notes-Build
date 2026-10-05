import reflex as rx

from app.components.note_cards import category_icon, empty_notebook, note_card
from app.components.workspace import PRIMARY, shell
from app.states.notes_state import NotesState
from app.components.preferences import tr


def category_tile(item: dict[str, str | int]) -> rx.Component:
    return rx.el.button(
        rx.el.div(
            category_icon(item["name"].to(str)),
            rx.icon("arrow-up-right", class_name="h-4 w-4 text-[#B3A8C7]"),
            class_name="flex items-center justify-between",
        ),
        rx.el.p(
            tr(item["name"].to(str)),
            class_name="mt-4 text-sm font-semibold text-[var(--vm-ink)]",
        ),
        rx.el.p(
            f"{item['count'].to(int)} {tr('notes')}",
            class_name="mt-1 text-xs text-[var(--vm-muted)]",
        ),
        on_click=NotesState.browse_category(item["name"].to(str)),
        class_name="w-full rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-4 text-left transition hover:border-[#BDB0E4] hover:bg-[#F6F1FC] focus-visible:outline-2 focus-visible:outline-[#6757C8] sm:p-5",
    )


def home() -> rx.Component:
    return shell(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        tr("YOUR PERSONAL SPACE"),
                        class_name="mb-3 text-[10px] font-semibold tracking-[0.22em] text-[#9A8FB0]",
                    ),
                    rx.el.h1(
                        tr("A clearer mind starts here."),
                        class_name="font-['DM_Sans'] text-3xl font-semibold leading-tight tracking-tight text-[var(--vm-ink)] sm:text-4xl",
                    ),
                    rx.el.p(
                        tr(
                            "Catch a thought. Keep what matters. Come back to it."
                        ),
                        class_name="mt-3 text-sm leading-6 text-[var(--vm-muted)] sm:text-base",
                    ),
                ),
                rx.el.span(
                    rx.icon("sun", class_name="h-7 w-7 text-[#B3A17F]"),
                    class_name="hidden h-14 w-14 items-center justify-center rounded-full border border-[#E7DECE] bg-[var(--vm-card)] sm:flex",
                ),
                class_name="mb-8 flex items-start justify-between gap-6",
            ),
            rx.el.section(
                rx.el.div(
                    rx.el.span(
                        rx.icon("pen-line", class_name="h-4 w-4"),
                        tr("One thought at a time"),
                        class_name="mb-5 inline-flex w-fit items-center gap-2 rounded-full border border-[#D8CFEF] bg-[var(--vm-lavender)] px-3 py-1.5 text-xs font-medium text-[var(--vm-accent)]",
                    ),
                    rx.el.h2(
                        tr("Make room for\nyour next idea."),
                        class_name="whitespace-pre-line font-['DM_Sans'] text-3xl font-semibold leading-[1.2] tracking-tight text-[var(--vm-ink)] sm:text-[38px]",
                    ),
                    rx.el.p(
                        tr(
                            "No perfect words needed. Just a quiet place to begin."
                        ),
                        class_name="mt-4 max-w-sm text-sm leading-6 text-[var(--vm-muted)]",
                    ),
                    rx.el.button(
                        rx.icon("plus", class_name="h-4 w-4"),
                        tr("Create a text note"),
                        on_click=NotesState.go("/notes/new"),
                        disabled=NotesState.storage_invalid,
                        class_name=PRIMARY,
                    ),
                    rx.el.button(
                        rx.icon("mic", class_name="h-4 w-4"),
                        tr("Capture a spoken thought"),
                        on_click=NotesState.go("/record"),
                        class_name="inline-flex items-center gap-2 rounded-2xl px-3 py-3 text-sm font-semibold text-[var(--vm-accent)] transition hover:bg-[var(--vm-lavender)] focus-visible:outline-2 focus-visible:outline-[#6757C8]",
                    ),
                    class_name="relative z-10 flex flex-col items-start gap-2",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.icon(
                            "notebook-pen",
                            class_name="h-7 w-7 text-[var(--vm-accent)]",
                        ),
                        rx.el.span(
                            tr("A thought worth keeping"),
                            class_name="mt-4 block text-sm font-medium text-[var(--vm-accent)]",
                        ),
                        rx.el.div(
                            class_name="mt-5 h-1.5 w-36 rounded-full bg-[#D7CAEC]"
                        ),
                        rx.el.div(
                            class_name="mt-3 h-1.5 w-28 rounded-full bg-[#E3D9F3]"
                        ),
                        rx.el.div(
                            class_name="mt-3 h-1.5 w-32 rounded-full bg-[#E3D9F3]"
                        ),
                        rx.icon(
                            "sparkles", class_name="mt-6 h-5 w-5 text-[#AE99D3]"
                        ),
                        class_name="relative z-10 w-56 -rotate-6 rounded-3xl border border-[#D2C3E8] bg-[var(--vm-card)] p-7",
                    ),
                    rx.el.div(
                        class_name="absolute top-10 right-1 h-64 w-56 rotate-6 rounded-3xl border border-[#D2C3E8] bg-[var(--vm-lavender)]"
                    ),
                    class_name="relative mr-7 hidden shrink-0 lg:block",
                    aria_hidden=True,
                ),
                class_name="flex items-center justify-between gap-6 overflow-hidden rounded-[28px] border border-[#DED3ED] bg-[var(--vm-lavender)] p-7 sm:p-10",
            ),
            rx.el.section(
                rx.el.div(
                    rx.el.h2(
                        tr("Pick up where you left off"),
                        class_name="font-['DM_Sans'] text-xl font-semibold tracking-tight text-[var(--vm-ink)]",
                    ),
                    rx.el.button(
                        tr("All notes"),
                        rx.icon("arrow-right", class_name="h-4 w-4"),
                        on_click=NotesState.go("/notes"),
                        class_name="flex shrink-0 items-center gap-2 rounded-lg p-1 text-xs font-semibold text-[var(--vm-accent)] hover:underline focus-visible:outline-2 focus-visible:outline-[#6757C8]",
                    ),
                    class_name="mb-5 flex items-center justify-between gap-3",
                ),
                rx.cond(
                    NotesState.note_count > 0,
                    rx.el.div(
                        rx.foreach(NotesState.recent_notes, note_card),
                        class_name="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4",
                    ),
                    empty_notebook(),
                ),
                class_name="mt-9",
            ),
            rx.el.section(
                rx.el.h2(
                    tr("A place for every thought"),
                    class_name="mb-5 font-['DM_Sans'] text-xl font-semibold tracking-tight text-[var(--vm-ink)]",
                ),
                rx.el.div(
                    rx.foreach(NotesState.category_counts, category_tile),
                    class_name="grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4",
                ),
                class_name="mt-9",
            ),
        )
    )
