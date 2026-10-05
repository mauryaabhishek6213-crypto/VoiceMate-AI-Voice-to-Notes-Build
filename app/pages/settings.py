import reflex as rx

from app.components.preferences import tr
from app.components.workspace import PRIMARY, SECONDARY, shell
from app.states.settings_state import SettingsState


def preference_select(
    name: str, title: str, options: list[tuple[str, str]]
) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            tr(title),
            html_for=name,
            class_name="mb-2 block text-sm font-semibold text-[var(--vm-ink)]",
        ),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    options,
                    lambda option: rx.el.option(tr(option[1]), value=option[0]),
                ),
                name=name,
                id=name,
                default_value=SettingsState.preferences[name],
                key=SettingsState.preferences[name],
                class_name="w-full appearance-none rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-field)] py-3 pr-10 pl-4 text-sm text-[var(--vm-ink)] focus:outline-2 focus:outline-[#6757C8]",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute top-3 right-4 h-5 w-5 text-[var(--vm-muted)]",
            ),
            class_name="relative",
        ),
        class_name="w-full",
    )


def settings() -> rx.Component:
    return shell(
        rx.el.div(
            rx.el.h1(
                tr("Settings"),
                class_name="font-['DM_Sans'] text-3xl font-semibold text-[var(--vm-ink)]",
            ),
            rx.el.form(
                rx.el.div(
                    preference_select(
                        "theme",
                        "Appearance",
                        [("light", "Light"), ("dark", "Dark")],
                    ),
                    preference_select(
                        "language",
                        "Interface language",
                        [("en", "English"), ("hi", "हिन्दी")],
                    ),
                    preference_select(
                        "speech",
                        "Default speech language",
                        [("en-US", "English"), ("hi-IN", "हिन्दी")],
                    ),
                    class_name="grid grid-cols-1 gap-5 sm:grid-cols-3",
                ),
                rx.el.button(
                    rx.icon("check", class_name="h-4 w-4"),
                    tr("Save preferences"),
                    type="submit",
                    disabled=SettingsState.saving,
                    class_name=PRIMARY,
                ),
                on_submit=SettingsState.save_preferences,
                class_name="mt-6 flex flex-col items-start gap-6 rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-5 sm:p-7",
            ),
            rx.el.p(
                tr(SettingsState.feedback),
                role="status",
                aria_live="polite",
                class_name="mt-4 text-sm text-[var(--vm-accent)]",
            ),
            rx.el.p(
                tr(SettingsState.error),
                role="alert",
                class_name="mt-4 text-sm text-red-600",
            ),
            rx.el.section(
                rx.el.div(
                    rx.icon(
                        "shield-check",
                        class_name="h-6 w-6 text-[var(--vm-accent)]",
                    ),
                    rx.el.h2(
                        tr("Privacy & help"),
                        class_name="text-xl font-semibold text-[var(--vm-ink)]",
                    ),
                    class_name="flex items-center gap-3",
                ),
                rx.el.p(
                    rx.cond(
                        SettingsState.language == "hi",
                        "VoiceMate एक ब्राउज़र-आधारित Reflex ऐप है, मूल Android या Flutter ऐप नहीं। नोट्स, AI परिणाम और पसंद इस ब्राउज़र में रहते हैं; वे एन्क्रिप्टेड बैकअप नहीं हैं और उपकरणों के बीच सिंक नहीं होते। कार्यक्षेत्र चलाने के लिए पाठ Reflex सर्वर से गुजरता है। ऐप को कनेक्शन की ज़रूरत हो सकती है; ऑफ़लाइन कार्य करने की गारंटी नहीं है।",
                        "VoiceMate is a browser-based Reflex app, not a native Android or Flutter app. Notes, AI results and preferences live in this browser; they are not encrypted backups and do not sync between devices. Text passes through the Reflex server to power the workspace. The app may require connectivity; offline operation is not guaranteed.",
                    ),
                    class_name="mt-4 text-sm leading-7 text-[var(--vm-muted)]",
                ),
                rx.el.p(
                    rx.cond(
                        SettingsState.language == "hi",
                        "ब्राउज़र आवाज़ पहचान अपनी बाहरी सेवा का उपयोग कर सकती है। वैकल्पिक AI और ऑडियो आयात केवल स्पष्ट अनुमति पर प्रदाता को सामग्री भेजते हैं। ऑडियो ब्राउज़र संग्रहण या सर्वर डिस्क में सहेजा नहीं जाता। बाहरी प्रदाता की गोपनीयता नीति लागू होती है। निजी सामग्री साझा करने से बचें।",
                        "Browser speech recognition may use its own external service. Optional AI and audio import send content to a provider only with explicit approval. Audio is not saved in browser storage or on server disk. External provider privacy policies apply. Avoid sharing sensitive content.",
                    ),
                    class_name="mt-4 text-sm leading-7 text-[var(--vm-muted)]",
                ),
                rx.el.p(
                    rx.cond(
                        SettingsState.language == "hi",
                        "नोट सहेजें दबाएँ और सत्यापन संदेश देखें। ज़रूरी नोट्स का पाठ डाउनलोड करके बैकअप रखें। संग्रहण विफल हो तो पेज खुला रखें और कॉपी करें या फिर सहेजें। आवाज़ पहचान के लिए HTTPS और समर्थित ब्राउज़र चाहिए। आयात अनुपलब्ध हो तो लिखित नोट या ब्राउज़र आवाज़ पहचान चुनें। एक ही समय में कई टैब में संपादन न करें; अंतिम बदलाव प्रभावी होता है।",
                        "Tap Save note and look for verification feedback. Download important notes as text backups. If storage fails, keep the page open and copy or retry saving. Speech capture requires HTTPS and a supported browser. When import is unavailable, use text notes or browser speech capture. Avoid concurrent editing in multiple tabs; the last write wins.",
                    ),
                    class_name="mt-4 text-sm leading-7 text-[var(--vm-muted)]",
                ),
                rx.el.p(
                    "VoiceMate Web · v1.1",
                    class_name="mt-5 text-xs text-[var(--vm-accent)]",
                ),
                class_name="mt-6 rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-5 sm:p-7",
            ),
            rx.el.button(
                rx.icon("trash-2", class_name="h-4 w-4"),
                tr("Clear all notes and AI results"),
                on_click=SettingsState.request_clear,
                class_name="mt-6 inline-flex items-center gap-2 rounded-2xl border border-red-200 bg-red-50 px-5 py-3 text-sm font-semibold text-red-700 hover:bg-red-100",
            ),
            rx.cond(
                SettingsState.confirming,
                rx.el.div(
                    rx.el.div(
                        rx.el.h2(
                            tr("Clear this browser notebook?"),
                            id="clear-title",
                            class_name="text-xl font-semibold text-[var(--vm-ink)]",
                        ),
                        rx.el.p(
                            rx.cond(
                                SettingsState.language == "hi",
                                "इस ब्राउज़र के सभी नोट्स और AI परिणाम हमेशा के लिए मिटेंगे। पहले ज़रूरी नोट्स डाउनलोड करें। पसंद सुरक्षित रहेगी। अन्य उपकरणों और डाउनलोड किए बैकअप पर असर नहीं होगा। इसे वापस नहीं किया जा सकता।",
                                "All notes and AI results in this browser will be permanently removed. Download important notes first. Preferences stay intact. Other devices and downloaded backups are unaffected. This cannot be undone.",
                            ),
                            id="clear-description",
                            class_name="mt-4 text-sm leading-6 text-[var(--vm-muted)]",
                        ),
                        rx.el.div(
                            rx.el.button(
                                tr("Cancel"),
                                on_click=SettingsState.cancel_clear,
                                disabled=SettingsState.clearing,
                                auto_focus=True,
                                class_name=SECONDARY,
                            ),
                            rx.el.button(
                                rx.cond(
                                    SettingsState.clearing,
                                    tr("Clearing…"),
                                    tr("Yes, clear everything"),
                                ),
                                on_click=SettingsState.clear_all,
                                disabled=SettingsState.clearing,
                                class_name="rounded-2xl bg-red-600 px-5 py-3 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50",
                            ),
                            class_name="mt-6 flex flex-wrap justify-end gap-3",
                        ),
                        rx.el.p(
                            tr(SettingsState.error),
                            role="alert",
                            class_name="mt-4 text-sm text-red-600",
                        ),
                        role="alertdialog",
                        aria_modal=True,
                        aria_labelledby="clear-title",
                        aria_describedby="clear-description",
                        class_name="w-full max-w-lg rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-6 sm:p-8",
                    ),
                    class_name="fixed inset-0 z-50 flex items-center justify-center bg-[#242333]/50 p-5",
                ),
            ),
        )
    )
