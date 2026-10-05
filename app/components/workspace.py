import reflex as rx

from app.states.notes_state import NotesState
from app.states.settings_state import SettingsState
from app.components.preferences import tr


PRIMARY = "inline-flex items-center justify-center gap-2 rounded-2xl bg-[#6757C8] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#5546B4] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#6757C8] disabled:opacity-50"
SECONDARY = "inline-flex items-center justify-center gap-2 rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-card)] px-4 py-3 text-sm font-medium text-[var(--vm-ink)] transition hover:bg-[#F1ECFA] focus-visible:outline-2 focus-visible:outline-[#6757C8]"


def brand() -> rx.Component:
    return rx.el.button(
        rx.el.span(
            rx.icon("audio-lines", class_name="h-6 w-6 text-white"),
            class_name="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#6757C8]",
        ),
        rx.el.span(
            "VoiceMate",
            rx.el.span(
                tr("A little space for your mind"),
                class_name="mt-0.5 block text-[11px] font-normal tracking-normal text-[var(--vm-muted)]",
            ),
            class_name="text-xl font-semibold tracking-tight text-[var(--vm-ink)]",
        ),
        on_click=NotesState.go("/"),
        aria_label="VoiceMate home",
        class_name="flex items-center gap-3 text-left focus-visible:outline-2 focus-visible:outline-[#6757C8] rounded-xl",
    )


def nav_item(label: str, icon: str, route: str, active: str) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            rx.icon(icon, class_name="h-5 w-5"),
            class_name=rx.cond(
                NotesState.view == active,
                "flex h-8 w-14 items-center justify-center rounded-full bg-[var(--vm-lavender)] text-[var(--vm-accent)]",
                "flex h-8 w-14 items-center justify-center rounded-full bg-transparent text-[#8A8392]",
            ),
        ),
        rx.el.span(
            tr(label),
            class_name=rx.cond(
                NotesState.view == active,
                "text-[11px] font-semibold text-[var(--vm-accent)]",
                "text-[11px] font-medium text-[var(--vm-muted)]",
            ),
        ),
        on_click=NotesState.go(route),
        aria_current=rx.cond(NotesState.view == active, "page", "false"),
        class_name="flex min-w-0 flex-1 flex-col items-center gap-1 rounded-xl py-2 transition hover:bg-[#F6F2FA] focus-visible:outline-2 focus-visible:outline-[#6757C8]",
    )


def bottom_navigation() -> rx.Component:
    return rx.el.footer(
        rx.el.nav(
            nav_item("Home", "house", "/", "home"),
            nav_item("My notes", "notebook-pen", "/notes", "notes"),
            nav_item("Favorites", "star", "/favorites", "favorites"),
            nav_item("Capture", "mic", "/record", "record"),
            rx.el.button(
                rx.icon("plus", class_name="h-5 w-5"),
                rx.el.span(
                    tr("New note"), class_name="text-[11px] font-semibold"
                ),
                on_click=NotesState.go("/notes/new"),
                class_name="m-1 flex min-w-0 flex-1 flex-col items-center justify-center gap-1 rounded-2xl bg-[#6757C8] py-2 text-white transition hover:bg-[#5546B4] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#6757C8]",
            ),
            aria_label="Main navigation",
            class_name="mx-auto flex w-full max-w-lg items-center gap-1 px-3",
        ),
        class_name="shrink-0 border-t border-[var(--vm-border)] bg-[var(--vm-card)] pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))]",
    )


def feedback() -> rx.Component:
    return rx.el.div(
        rx.cond(
            NotesState.storage_invalid,
            rx.el.div(
                rx.icon("triangle-alert", class_name="h-5 w-5 shrink-0"),
                rx.el.div(
                    rx.el.p(
                        "Your saved notebook couldn't be read.",
                        class_name="font-semibold",
                    ),
                    rx.el.p(
                        "Nothing has been overwritten. Check this browser's stored data or try reloading. Creating and updating notes is paused to protect your existing notes.",
                        class_name="mt-1 text-sm",
                    ),
                ),
                class_name="mb-5 flex gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700",
                role="alert",
            ),
        ),
        rx.cond(
            NotesState.error != "",
            rx.el.div(
                rx.icon("circle-alert", class_name="h-5 w-5 shrink-0"),
                rx.el.p(tr(NotesState.error), class_name="text-sm"),
                role="alert",
                class_name="mb-5 flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700",
            ),
        ),
        rx.cond(
            NotesState.feedback != "",
            rx.el.div(
                rx.cond(
                    NotesState.saving,
                    rx.icon("loader-circle", class_name="h-4 w-4 animate-spin"),
                    rx.icon("circle-check", class_name="h-4 w-4"),
                ),
                tr(NotesState.feedback),
                role="status",
                aria_live="polite",
                class_name="mb-5 flex items-center gap-2 rounded-xl bg-[var(--vm-lavender)] px-4 py-3 text-sm text-[var(--vm-accent)]",
            ),
        ),
    )


def local_notice() -> rx.Component:
    return rx.el.div(
        rx.icon(
            "hard-drive", class_name="h-4 w-4 shrink-0 text-[var(--vm-accent)]"
        ),
        rx.el.p(
            rx.cond(
                SettingsState.language == "hi",
                "इस ब्राउज़र में सहेजा जाता है, क्लाउड नोटबुक नहीं। ब्राउज़र डेटा हटाने पर नोट्स मिटेंगे। कार्यक्षेत्र चलाने के लिए पाठ Reflex सर्वर से गुजरता है। वैकल्पिक AI या आयात केवल आपकी स्पष्ट अनुमति पर सामग्री बाहरी प्रदाता को भेजते हैं। ऑडियो सहेजा नहीं जाता। AI परिणाम इसी ब्राउज़र में रहते हैं।",
                "Saved in this browser, not a cloud notebook. Clearing browser data removes notes. Text passes through Reflex to power this workspace. Optional AI and audio import send content to an external provider only after explicit approval. Audio is not saved; AI results are saved in this browser.",
            ),
            class_name="text-xs leading-relaxed text-[var(--vm-muted)]",
        ),
        class_name="mt-9 flex items-start gap-2 border-t border-[var(--vm-border)] pt-5",
    )


def confirmation_modals() -> rx.Component:
    return rx.fragment(
        rx.cond(
            NotesState.delete_id != "",
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.icon("trash-2", class_name="h-6 w-6 text-red-600"),
                        class_name="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-red-50",
                    ),
                    rx.el.h2(
                        tr("Delete this note?"),
                        id="delete-title",
                        class_name="text-xl font-semibold text-[var(--vm-ink)]",
                    ),
                    rx.el.p(
                        NotesState.delete_title,
                        class_name="mt-3 break-words text-sm font-medium text-[var(--vm-ink)]",
                    ),
                    rx.el.p(
                        tr(
                            "This removes the note and its attached AI results from this browser. You can't undo this action."
                        ),
                        id="delete-description",
                        class_name="mt-2 text-sm leading-relaxed text-[var(--vm-muted)]",
                    ),
                    rx.el.div(
                        rx.el.button(
                            tr("Keep note"),
                            on_click=NotesState.cancel_delete,
                            auto_focus=True,
                            class_name=SECONDARY,
                        ),
                        rx.el.button(
                            tr("Delete note"),
                            on_click=NotesState.confirm_delete,
                            disabled=NotesState.saving,
                            class_name="rounded-2xl bg-red-600 px-5 py-3 text-sm font-semibold text-white hover:bg-red-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600 disabled:opacity-50",
                        ),
                        class_name="mt-7 flex justify-end gap-3",
                    ),
                    role="alertdialog",
                    aria_modal=True,
                    aria_labelledby="delete-title",
                    aria_describedby="delete-description",
                    class_name="w-full max-w-md rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-6 sm:p-8",
                ),
                class_name="fixed inset-0 z-50 flex items-center justify-center bg-[#242333]/40 p-5 backdrop-blur-xs",
            ),
        ),
        rx.cond(
            NotesState.leave_open,
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.icon(
                            "file-pen-line",
                            class_name="h-6 w-6 text-[var(--vm-accent)]",
                        ),
                        class_name="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--vm-lavender)]",
                    ),
                    rx.el.h2(
                        tr("Keep your thoughts safe"),
                        id="leave-title",
                        class_name="text-xl font-semibold text-[var(--vm-ink)]",
                    ),
                    rx.el.p(
                        tr(
                            "You have unsaved changes. Stay here to save them, or leave and discard your changes."
                        ),
                        id="leave-description",
                        class_name="mt-3 text-sm leading-relaxed text-[var(--vm-muted)]",
                    ),
                    rx.el.div(
                        rx.el.button(
                            tr("Discard & leave"),
                            on_click=NotesState.discard_and_leave,
                            class_name=SECONDARY,
                        ),
                        rx.el.button(
                            tr("Keep editing"),
                            on_click=NotesState.stay,
                            auto_focus=True,
                            class_name=PRIMARY,
                        ),
                        class_name="mt-7 flex flex-wrap justify-end gap-3",
                    ),
                    role="alertdialog",
                    aria_modal=True,
                    aria_labelledby="leave-title",
                    aria_describedby="leave-description",
                    class_name="w-full max-w-md rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-6 sm:p-8",
                ),
                class_name="fixed inset-0 z-50 flex items-center justify-center bg-[#242333]/40 p-5 backdrop-blur-xs",
            ),
        ),
    )


def shell(content: rx.Component) -> rx.Component:
    return rx.el.div(
        rx.el.header(
            rx.el.div(
                brand(),
                rx.el.div(
                    rx.el.button(
                        rx.icon("file-audio", class_name="h-5 w-5"),
                        rx.el.span(
                            tr("Import audio"), class_name="hidden sm:inline"
                        ),
                        on_click=NotesState.go("/import"),
                        aria_label=tr("Import audio"),
                        class_name="flex items-center gap-2 rounded-xl p-3 text-sm text-[var(--vm-accent)] hover:bg-[var(--vm-lavender)] focus-visible:outline-2 focus-visible:outline-[#6757C8]",
                    ),
                    rx.el.button(
                        rx.icon("settings", class_name="h-5 w-5"),
                        rx.el.span(
                            tr("Settings"), class_name="hidden sm:inline"
                        ),
                        on_click=NotesState.go("/settings"),
                        aria_label=tr("Settings"),
                        class_name="flex items-center gap-2 rounded-xl p-3 text-sm text-[var(--vm-accent)] hover:bg-[var(--vm-lavender)] focus-visible:outline-2 focus-visible:outline-[#6757C8]",
                    ),
                    class_name="flex shrink-0 items-center gap-1",
                ),
                class_name="mx-auto flex w-full max-w-6xl items-center justify-between px-5 py-5 sm:px-8",
            ),
            class_name="shrink-0 border-b border-[var(--vm-border)] bg-[var(--vm-card)]",
        ),
        rx.el.main(
            rx.el.div(
                feedback(),
                rx.cond(
                    NotesState.ready,
                    content,
                    rx.el.div(
                        rx.el.div(
                            class_name="h-64 animate-pulse rounded-3xl bg-[#EEE8E0]"
                        ),
                        rx.el.p(
                            tr("Opening your notebook…"),
                            role="status",
                            class_name="mt-4 text-sm text-[var(--vm-muted)]",
                        ),
                    ),
                ),
                local_notice(),
                class_name="mx-auto w-full max-w-6xl px-5 pt-7 pb-8 sm:px-8 sm:pt-10",
            ),
            id="main-content",
            class_name="min-h-0 w-full min-w-0 flex-1 overflow-y-auto",
        ),
        bottom_navigation(),
        confirmation_modals(),
        lang=SettingsState.language,
        on_mount=rx.call_script(
            f"document.documentElement.lang = {SettingsState.language.to_string()}"
        ),
        class_name=rx.cond(
            SettingsState.theme == "dark",
            "flex h-dvh w-full flex-col overflow-hidden bg-[#191820] font-['Inter'] text-[#F2EDF8] selection:bg-[#534575] [--vm-card:#272530] [--vm-page:#191820] [--vm-field:#302D3B] [--vm-ink:#F2EDF8] [--vm-muted:#C3B9CF] [--vm-lavender:#373044] [--vm-border:#514859] [--vm-accent:#C0B2FF]",
            "flex h-dvh w-full flex-col overflow-hidden bg-[#FAF7F1] font-['Inter'] text-[var(--vm-ink)] selection:bg-[#E3DBF7] [--vm-card:#FFFDF9] [--vm-page:#FAF7F1] [--vm-field:#FFFEFC] [--vm-ink:#242333] [--vm-muted:#82798C] [--vm-lavender:#F6F1FC] [--vm-border:#E5DFD7] [--vm-accent:#6757C8]",
        ),
    )
