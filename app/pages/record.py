import reflex as rx

from app.components.workspace import PRIMARY, SECONDARY, shell
from app.states.notes_state import NotesState
from app.components.preferences import tr
from app.states.record_state import CLEANUP_SCRIPT, RecordState


FIELD = "w-full rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-field)] px-4 py-3 text-sm text-[var(--vm-ink)] placeholder:text-[#A299AA] focus:outline-2 focus:outline-[#6757C8] disabled:opacity-60"


def capture_controls() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.icon("mic", class_name="h-7 w-7 text-[var(--vm-accent)]"),
                class_name=rx.cond(
                    RecordState.status == "listening",
                    "flex h-16 w-16 animate-pulse items-center justify-center rounded-3xl bg-[#E3DBF7]",
                    "flex h-16 w-16 items-center justify-center rounded-3xl bg-[#EDE7FA]",
                ),
            ),
            rx.el.div(
                rx.el.p(
                    tr(RecordState.status_label),
                    role="status",
                    aria_live="polite",
                    class_name="text-sm font-semibold text-[var(--vm-ink)]",
                ),
                rx.el.p(
                    RecordState.timer_label,
                    class_name="mt-1 font-mono text-2xl text-[var(--vm-accent)]",
                ),
            ),
            class_name="flex items-center gap-4",
        ),
        rx.el.div(
            rx.el.span(
                tr("Speech language"),
                class_name="text-xs font-semibold text-[var(--vm-muted)]",
            ),
            rx.el.div(
                rx.el.button(
                    "English",
                    on_click=RecordState.choose_language("en-US"),
                    disabled=RecordState.active,
                    aria_pressed=RecordState.language == "en-US",
                    class_name=rx.cond(
                        RecordState.language == "en-US",
                        "rounded-xl bg-[#6757C8] px-4 py-2 text-sm font-medium text-white disabled:opacity-60",
                        "rounded-xl bg-[var(--vm-card)] px-4 py-2 text-sm font-medium text-[var(--vm-accent)] hover:bg-[#EDE7FA] disabled:opacity-60",
                    ),
                ),
                rx.el.button(
                    "हिन्दी · Hindi",
                    on_click=RecordState.choose_language("hi-IN"),
                    disabled=RecordState.active,
                    aria_pressed=RecordState.language == "hi-IN",
                    class_name=rx.cond(
                        RecordState.language == "hi-IN",
                        "rounded-xl bg-[#6757C8] px-4 py-2 text-sm font-medium text-white disabled:opacity-60",
                        "rounded-xl bg-[var(--vm-card)] px-4 py-2 text-sm font-medium text-[var(--vm-accent)] hover:bg-[#EDE7FA] disabled:opacity-60",
                    ),
                ),
                class_name="flex flex-wrap gap-2",
            ),
            class_name="mt-6 flex flex-wrap items-center gap-4",
        ),
        rx.cond(
            ~RecordState.probed,
            rx.el.p(
                tr("Checking browser speech support…"),
                class_name="mt-5 animate-pulse text-sm text-[var(--vm-muted)]",
            ),
            rx.cond(
                RecordState.supported,
                rx.el.div(
                    rx.el.button(
                        rx.icon("mic", class_name="h-4 w-4"),
                        tr("Start"),
                        on_click=rx.call_script(
                            f"(() => {{ const c = window.vmSpeech; if (!c || c.closed) return ''; c.start({RecordState.language.to_string()}); return c.snapshot(); }})()",
                            callback=RecordState.receive,
                        ),
                        disabled=RecordState.active
                        | NotesState.saving
                        | (NotesState.capture_saved_id != ""),
                        class_name=PRIMARY,
                    ),
                    rx.el.button(
                        rx.icon("square", class_name="h-4 w-4"),
                        tr("Stop"),
                        on_click=RecordState.stop,
                        disabled=~RecordState.active
                        | (RecordState.status == "stopping"),
                        class_name="inline-flex items-center gap-2 rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-card)] px-4 py-3 text-sm font-medium text-[var(--vm-ink)] hover:bg-[#F1ECFA] disabled:opacity-40",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-4 w-4"),
                        tr("Cancel session"),
                        on_click=RecordState.cancel,
                        disabled=NotesState.saving
                        | (NotesState.capture_saved_id != ""),
                        class_name="inline-flex items-center gap-2 rounded-2xl px-4 py-3 text-sm font-medium text-[var(--vm-muted)] hover:bg-[#F1ECFA] disabled:opacity-40",
                    ),
                    class_name="mt-6 flex flex-wrap gap-3",
                ),
                rx.el.button(
                    tr("Create a text note instead"),
                    on_click=NotesState.go("/notes/new"),
                    class_name=SECONDARY,
                ),
            ),
        ),
        rx.cond(
            RecordState.error != "",
            rx.el.p(
                tr(RecordState.error),
                role="alert",
                class_name="mt-5 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm leading-6 text-red-700",
            ),
        ),
        rx.el.p(
            tr(
                "Start requests microphone access. Stop waits for final words; tentative words may not be finalized by the speech service. Start again to append more. Cancel discards all text in this capture session."
            ),
            class_name="mt-5 text-xs leading-6 text-[var(--vm-muted)]",
        ),
        class_name="rounded-3xl border border-[#DED3ED] bg-[var(--vm-lavender)] p-5 sm:p-7",
    )


def transcript_form() -> rx.Component:
    return rx.el.form(
        rx.el.h2(
            tr("Your words, ready to refine"),
            class_name="font-['DM_Sans'] text-xl font-semibold text-[var(--vm-ink)]",
        ),
        rx.cond(
            RecordState.active,
            rx.el.div(
                rx.el.p(
                    RecordState.transcript,
                    class_name="whitespace-pre-wrap break-words text-base leading-8 text-[var(--vm-ink)]",
                ),
                rx.el.p(
                    RecordState.interim,
                    class_name="whitespace-pre-wrap break-words text-base italic leading-8 text-[#9A8FB0]",
                ),
                rx.el.p(
                    tr(
                        "Live text · lighter words are tentative. Edit after capture ends."
                    ),
                    class_name="mt-3 text-xs text-[var(--vm-muted)]",
                ),
                class_name="mt-5 min-h-40 rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-field)] p-4",
            ),
        ),
        rx.el.label(
            tr("Note title"),
            html_for="capture-title",
            class_name="mt-6 mb-2 block text-xs font-semibold text-[var(--vm-muted)]",
        ),
        rx.el.input(
            id="capture-title",
            name="title",
            placeholder=tr("Give this thought a name…"),
            max_length=160,
            class_name=FIELD,
        ),
        rx.el.label(
            tr("Category"),
            html_for="capture-category",
            class_name="mt-4 mb-2 block text-xs font-semibold text-[var(--vm-muted)]",
        ),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    NotesState.categories,
                    lambda c: rx.el.option(tr(c), value=c),
                ),
                id="capture-category",
                name="category",
                default_value="Personal",
                class_name="w-full appearance-none rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-field)] py-3 pr-10 pl-4 text-sm text-[var(--vm-ink)] focus:outline-2 focus:outline-[#6757C8]",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute top-3.5 right-4 h-4 w-4 text-[var(--vm-muted)]",
            ),
            class_name="relative w-full sm:w-48",
        ),
        rx.el.label(
            tr("Final transcript · editable after stopping"),
            html_for="capture-text",
            class_name="mt-6 mb-2 block text-xs font-semibold text-[var(--vm-muted)]",
        ),
        rx.el.textarea(
            id="capture-text",
            name="content",
            default_value=RecordState.transcript,
            key=RecordState.revision,
            disabled=RecordState.active | (NotesState.capture_saved_id != ""),
            max_length=100000,
            placeholder=tr(
                "Recognized words will appear here. You can also type and correct them before saving."
            ),
            class_name="min-h-64 w-full resize-y rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-field)] p-4 text-base leading-8 text-[var(--vm-ink)] placeholder:text-[#A299AA] focus:outline-2 focus:outline-[#6757C8] disabled:opacity-50",
        ),
        rx.cond(
            NotesState.capture_saved_id != "",
            rx.el.div(
                rx.icon("circle-check", class_name="h-5 w-5 text-green-500"),
                rx.el.span(
                    tr("Transcript saved and verified in this browser."),
                    class_name="text-sm text-[var(--vm-ink)]",
                ),
                rx.el.button(
                    tr("Open saved note"),
                    type="button",
                    on_click=NotesState.go(
                        f"/notes/{NotesState.capture_saved_id}"
                    ),
                    class_name=SECONDARY,
                ),
                class_name="mt-5 flex flex-wrap items-center gap-3",
            ),
            rx.el.button(
                rx.icon("check", class_name="h-4 w-4"),
                rx.cond(
                    NotesState.saving,
                    tr("Saving…"),
                    tr("Save transcript as note"),
                ),
                type="submit",
                disabled=RecordState.active
                | NotesState.saving
                | NotesState.storage_invalid,
                class_name=PRIMARY,
            ),
        ),
        rx.el.p(
            tr(
                "Only text is saved, never an audio recording. Keep this page open if saving fails; your editable transcript stays here for retry. Leaving this page discards unsaved capture text."
            ),
            class_name="mt-4 text-xs leading-6 text-[var(--vm-muted)]",
        ),
        on_submit=RecordState.save,
        class_name="mt-6 rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-5 sm:p-7",
    )


def record() -> rx.Component:
    return shell(
        rx.el.div(
            rx.el.p(
                tr("A LITTLE SPACE TO SPEAK"),
                class_name="mb-3 text-[10px] font-semibold tracking-[0.22em] text-[#9A8FB0]",
            ),
            rx.el.h1(
                tr("Speak a thought. Keep the words."),
                class_name="font-['DM_Sans'] text-3xl font-semibold tracking-tight text-[var(--vm-ink)] sm:text-4xl",
            ),
            rx.el.p(
                tr(
                    "Browser speech capture · English or Hindi · no audio files stored"
                ),
                class_name="mt-3 text-sm text-[var(--vm-muted)]",
            ),
            rx.el.div(
                rx.icon(
                    "shield-check",
                    class_name="h-5 w-5 shrink-0 text-[var(--vm-accent)]",
                ),
                rx.el.p(
                    tr(
                        "Your browser may send speech to its own recognition service, which may need internet access. VoiceMate receives recognized text to power this workspace. Language support and accuracy depend on your browser and speech service."
                    ),
                    class_name="text-xs leading-6 text-[var(--vm-muted)]",
                ),
                class_name="my-6 flex gap-3 rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-4",
            ),
            capture_controls(),
            transcript_form(),
            on_unmount=rx.call_script(CLEANUP_SCRIPT),
        )
    )
