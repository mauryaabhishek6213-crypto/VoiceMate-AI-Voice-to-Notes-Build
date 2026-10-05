import reflex as rx

from app.components.workspace import PRIMARY, SECONDARY
from app.states.ai_state import AIState, Result
from app.states.notes_state import NotesState
from app.components.preferences import tr


FIELD = "w-full rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-card)] px-4 py-3 text-sm text-[var(--vm-ink)] placeholder:text-[#A299AA] focus:border-[#6757C8] focus:outline-2 focus:outline-[#E2D9F6]"


def action_controls() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    tr("What would help?"),
                    html_for="ai-action",
                    class_name="mb-2 block text-xs font-semibold text-[var(--vm-muted)]",
                ),
                rx.el.div(
                    rx.el.select(
                        rx.foreach(
                            AIState.actions,
                            lambda action: rx.el.option(
                                tr(action["label"]), value=action["value"]
                            ),
                        ),
                        name="action",
                        id="ai-action",
                        default_value=AIState.pending_action,
                        disabled=AIState.busy | AIState.storing,
                        class_name="w-full appearance-none rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-card)] py-3 pr-10 pl-4 text-sm text-[var(--vm-ink)] focus:outline-2 focus:outline-[#6757C8]",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="pointer-events-none absolute top-3.5 right-3 h-4 w-4 text-[var(--vm-muted)]",
                    ),
                    class_name="relative",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.label(
                    tr("Translation target"),
                    html_for="ai-language",
                    class_name="mb-2 block text-xs font-semibold text-[var(--vm-muted)]",
                ),
                rx.el.div(
                    rx.el.select(
                        rx.el.option("English", value="English"),
                        rx.el.option("Hindi · हिन्दी", value="Hindi"),
                        name="target_language",
                        id="ai-language",
                        default_value=AIState.pending_language,
                        disabled=AIState.busy | AIState.storing,
                        class_name="w-full appearance-none rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-card)] py-3 pr-10 pl-4 text-sm text-[var(--vm-ink)] focus:outline-2 focus:outline-[#6757C8]",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="pointer-events-none absolute top-3.5 right-3 h-4 w-4 text-[var(--vm-muted)]",
                    ),
                    class_name="relative",
                ),
                class_name="sm:w-48",
            ),
            class_name="flex flex-col gap-4 sm:flex-row",
        ),
        rx.el.label(
            tr("Question (for Ask this note only)"),
            html_for="ai-question",
            class_name="mt-4 mb-2 block text-xs font-semibold text-[var(--vm-muted)]",
        ),
        rx.el.input(
            name="question",
            id="ai-question",
            default_value=AIState.pending_question,
            max_length=1000,
            placeholder=tr("What does this note say about…?"),
            disabled=AIState.busy | AIState.storing,
            class_name=FIELD,
        ),
        rx.el.div(
            rx.el.p(
                tr(
                    "Uses only your last saved transcript, not unsaved edits. Maximum 20,000 characters. Results never replace your original note."
                ),
                class_name="text-xs leading-5 text-[var(--vm-muted)]",
            ),
            rx.el.button(
                rx.cond(
                    AIState.busy,
                    rx.icon("loader-circle", class_name="h-4 w-4 animate-spin"),
                    rx.icon("sparkles", class_name="h-4 w-4"),
                ),
                rx.cond(AIState.busy, tr("Working…"), tr("Review AI request")),
                type="submit",
                disabled=AIState.busy
                | AIState.storing
                | NotesState.saving
                | NotesState.storage_invalid,
                class_name=PRIMARY,
            ),
            class_name="mt-5 flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between",
        ),
        on_submit=AIState.prepare,
        class_name="mt-6",
    )


def result_card(record: Result) -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.h3(
                record["action"],
                class_name="text-sm font-semibold text-[var(--vm-accent)]",
            ),
            rx.el.span(
                tr("Editable AI result"),
                class_name="text-[11px] text-[var(--vm-muted)]",
            ),
            class_name="mb-3 flex items-center justify-between gap-3",
        ),
        rx.el.input(
            type="hidden", name="result_id", default_value=record["id"]
        ),
        rx.el.textarea(
            name="content",
            default_value=record["content"],
            key=record["content"],
            max_length=30000,
            aria_label="Edit AI result",
            class_name="min-h-44 w-full resize-y rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-4 text-sm leading-7 text-[var(--vm-ink)] focus:outline-2 focus:outline-[#E2D9F6]",
        ),
        rx.el.p(
            f"Generated {record['created_at']} · based on saved version {record['source_updated_at']}",
            class_name="mt-2 break-words text-[10px] leading-5 text-[var(--vm-muted)]",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("copy", class_name="h-4 w-4"),
                tr("Copy current text"),
                type="button",
                on_click=rx.call_script(
                    "(async () => { try { const form = document.activeElement.closest('form'); const text = form.querySelector('textarea').value; await navigator.clipboard.writeText(text); return 'copied'; } catch (_) { return 'unavailable'; } })()",
                    callback=AIState.copy_feedback,
                ),
                class_name=SECONDARY,
            ),
            rx.el.button(
                rx.icon("check", class_name="h-4 w-4"),
                tr("Save result"),
                type="submit",
                disabled=AIState.busy
                | AIState.storing
                | AIState.storage_invalid,
                class_name=PRIMARY,
            ),
            class_name="mt-4 flex flex-wrap justify-end gap-3",
        ),
        on_submit=AIState.save_result,
        key=record["id"],
        class_name="rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-lavender)] p-4 sm:p-5",
    )


def consent_dialog() -> rx.Component:
    return rx.cond(
        AIState.confirmation,
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "shield-check",
                    class_name="mb-4 h-8 w-8 text-[var(--vm-accent)]",
                ),
                rx.el.h2(
                    tr("Send this saved note to AI?"),
                    id="ai-consent-title",
                    class_name="text-xl font-semibold text-[var(--vm-ink)]",
                ),
                rx.el.p(
                    f"{AIState.action_label} · {AIState.pending_title} · {AIState.pending_characters:,} characters",
                    class_name="mt-3 break-words text-sm font-medium text-[var(--vm-accent)]",
                ),
                rx.el.p(
                    tr(
                        "If you confirm, the full original saved transcript and your question (if provided) will be sent through this app's server to its configured external OpenAI-compatible AI provider. This is not on-device processing. The provider may process or retain your text under its own privacy policies. Do not send confidential or sensitive information."
                    ),
                    id="ai-consent-description",
                    class_name="mt-4 text-sm leading-6 text-[var(--vm-muted)]",
                ),
                rx.el.p(
                    tr(
                        "Only this request is approved. Retrying requires a fresh confirmation. Your transcript will not be overwritten. No provider call has happened yet."
                    ),
                    class_name="mt-3 text-xs leading-5 text-[var(--vm-muted)]",
                ),
                rx.el.div(
                    rx.el.button(
                        tr("Don't send"),
                        on_click=AIState.cancel,
                        auto_focus=True,
                        class_name=SECONDARY,
                    ),
                    rx.el.button(
                        tr("I agree · Send to AI"),
                        on_click=rx.call_script(
                            "navigator.onLine !== false",
                            callback=AIState.confirm_online,
                        ),
                        class_name=PRIMARY,
                    ),
                    class_name="mt-6 flex flex-wrap justify-end gap-3",
                ),
                role="alertdialog",
                aria_modal=True,
                aria_labelledby="ai-consent-title",
                aria_describedby="ai-consent-description",
                class_name="max-h-[85dvh] w-full max-w-lg overflow-y-auto rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-6 sm:p-8",
            ),
            class_name="fixed inset-0 z-50 flex items-center justify-center bg-[#242333]/40 p-5 backdrop-blur-xs",
        ),
    )


def ai_assistant() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "sparkles", class_name="h-5 w-5 text-[var(--vm-accent)]"
                ),
                class_name="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--vm-lavender)]",
            ),
            rx.el.div(
                rx.el.h2(
                    tr("A little help with your thoughts"),
                    class_name="font-['DM_Sans'] text-xl font-semibold text-[var(--vm-ink)]",
                ),
                rx.el.p(
                    tr("AI assistant · optional, with your permission"),
                    class_name="mt-1 text-xs text-[var(--vm-muted)]",
                ),
            ),
            class_name="flex items-center gap-3",
        ),
        rx.el.div(
            rx.icon(
                "circle-alert", class_name="h-4 w-4 shrink-0 text-yellow-700"
            ),
            rx.el.p(
                tr(
                    "The last provider check reported insufficient credits. AI may remain unavailable until credits are replenished. No successful connection is assumed; your local notes and recording still work."
                ),
                class_name="text-xs leading-5 text-yellow-800",
            ),
            class_name="mt-5 flex gap-2 rounded-2xl border border-yellow-200 bg-yellow-50 p-3",
        ),
        action_controls(),
        rx.cond(
            AIState.storage_invalid,
            rx.el.p(
                "Existing AI result storage could not be read. It will not be overwritten. Original notes are unaffected.",
                role="alert",
                class_name="mt-4 text-sm text-red-600",
            ),
        ),
        rx.cond(
            AIState.error != "",
            rx.el.div(
                rx.el.p(
                    tr(AIState.error),
                    class_name="text-sm leading-6 text-red-700",
                ),
                rx.el.button(
                    rx.icon("rotate-ccw", class_name="h-4 w-4"),
                    tr("Retry · review permission"),
                    on_click=AIState.retry,
                    disabled=AIState.busy | AIState.storing,
                    class_name=SECONDARY,
                ),
                role="alert",
                class_name="mt-5 flex flex-col items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4",
            ),
        ),
        rx.el.p(
            tr(AIState.feedback),
            role="status",
            aria_live="polite",
            class_name="mt-4 text-xs leading-5 text-[var(--vm-accent)]",
        ),
        rx.cond(
            AIState.busy,
            rx.el.div(
                class_name="mt-5 h-28 animate-pulse rounded-2xl bg-[#EEE8F9]"
            ),
        ),
        rx.el.div(
            rx.el.h3(
                tr("Attached results"),
                class_name="mb-2 text-sm font-semibold text-[var(--vm-ink)]",
            ),
            rx.el.p(
                "Review AI output for mistakes. Save edits explicitly; Copy includes your current edits. Results are stored only in this browser and are removed when their note is deleted.",
                class_name="mb-4 text-xs leading-5 text-[var(--vm-muted)]",
            ),
            rx.cond(
                AIState.results.length() == 0,
                rx.el.p(
                    "No AI results for this note yet. Nothing is generated until you confirm a request.",
                    class_name="rounded-2xl border border-dashed border-[var(--vm-border)] bg-[var(--vm-page)] p-5 text-sm leading-6 text-[var(--vm-muted)]",
                ),
            ),
            rx.el.div(
                rx.foreach(AIState.results, result_card),
                class_name="flex flex-col gap-4",
            ),
            class_name="mt-6 border-t border-[#EEE8E0] pt-5",
        ),
        consent_dialog(),
        key=NotesState.editing_id,
        on_mount=AIState.open_note,
        aria_label="AI assistant for saved note",
        class_name="mt-7 w-full rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-5 sm:p-8",
    )
