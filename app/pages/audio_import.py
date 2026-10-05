import reflex as rx

from app.components.preferences import tr
from app.components.workspace import PRIMARY, SECONDARY, shell
from app.states.import_state import ImportState
from app.states.notes_state import NotesState
from app.states.settings_state import SettingsState

FIELD = "w-full rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-field)] px-4 py-3 text-sm text-[var(--vm-ink)] focus:outline-2 focus:outline-[#6757C8]"

CLIENT_INIT = r"""(() => {
    const input = document.getElementById('audio-file');
    const consent = document.getElementById('audio-consent');
    const status = document.getElementById('audio-client-status');
    if (!input || !consent || !status) return;
    input.onchange = () => {
        consent.checked = false;
        const file = input.files[0];
        const valid = file && file.size > 0 && file.size <= 20000000 && /\.(mp3|m4a|wav|webm|mp4)$/i.test(file.name);
        const mime = !file || !file.type || ['audio/mpeg','audio/mp3','audio/mp4','audio/x-m4a','audio/wav','audio/x-wav','audio/wave','audio/webm','video/webm','video/mp4','application/octet-stream'].includes(file.type);
        status.textContent = valid && mime ? `${file.name} · ${(file.size/1000000).toFixed(2)} MB` : (input.closest('[lang]').lang === 'hi' ? '20 MB तक की MP3, M4A, WAV, WebM या MP4 फ़ाइल चुनें।' : 'Choose a nonempty MP3, M4A, WAV, WebM or MP4 file up to 20 MB.');
        if (!valid || !mime) input.value = '';
    };
})()"""
SEND_SCRIPT = r"""
    const token = TOKEN;
    const error = message => JSON.stringify({token, error: message});
    if (window.vmAudioAbort) return JSON.stringify({token, ignored: true});
    let field, consent, button, status, controller, timeout;
    try {
    field = document.getElementById('audio-file');
    consent = document.getElementById('audio-consent');
    button = document.getElementById('audio-send');
    status = document.getElementById('audio-client-status');
    if (button) button.disabled = true;
    controller = new AbortController();
    window.vmAudioAbort = controller;
    if (UNAVAILABLE) return error(UNAVAILABLE);
    if (!token || !ENDPOINT || !field || !button || !status) return error('Audio import failed. Nothing was saved. Select your file and consent again to retry.');
    const file = field.files && field.files[0];
    if (!file || !file.size || file.size > 20000000 || !/\.(mp3|m4a|wav|webm|mp4)$/i.test(file.name)) return error('Choose one supported nonempty audio file up to 20 MB.');
    if (!consent || !consent.checked) return error('Explicit audio consent is required. Nothing was sent to the provider.');
    const types = {mp3: ['audio/mpeg','audio/mp3'], m4a: ['audio/mp4','audio/x-m4a','video/mp4'], wav: ['audio/wav','audio/x-wav','audio/wave'], webm: ['audio/webm','video/webm'], mp4: ['audio/mp4','video/mp4']};
    const ext = file.name.split('.').pop().toLowerCase();
    if (file.type && file.type !== 'application/octet-stream' && !types[ext].includes(file.type)) return error('Choose one supported nonempty audio file up to 20 MB.');
    consent.checked = false;
    field.disabled = consent.disabled = button.disabled = true;
    status.textContent = LANGUAGE === 'hi' ? 'ऑडियो भेजा जा रहा है और प्रतिलेखन जारी है…' : 'Sending audio and transcribing…';
    timeout = setTimeout(() => controller.abort(), 100000);
        const response = await fetch(ENDPOINT, {method: 'POST', body: file, signal: controller.signal,
            headers: {'Content-Type': file.type || 'application/octet-stream', 'X-Audio-Filename': encodeURIComponent(file.name), 'X-Audio-Consent': 'true', 'X-Audio-Language': LANGUAGE}});
        const data = await response.json();
        if (!response.ok) return error(data && data.error && data.error.message || 'Audio import failed. Nothing was saved. Select your file and consent again to retry.');
        if (!data || typeof data.transcript !== 'string') return error('No usable transcript was returned. Nothing was saved.');
        return JSON.stringify({token, transcript: data.transcript});
    } catch (e) {
        return error(e && e.name === 'AbortError' ? 'Transcription timed out. Review consent before retrying.' : 'Audio import failed. Nothing was saved. Select your file and consent again to retry.');
    } finally {
        clearTimeout(timeout);
        if (window.vmAudioAbort === controller) window.vmAudioAbort = null;
        if (field) field.disabled = !!UNAVAILABLE;
        if (consent) { consent.checked = false; consent.disabled = !!UNAVAILABLE; }
        if (button) button.disabled = !!UNAVAILABLE;
        if (status) status.textContent = LANGUAGE === 'hi' ? 'अनुरोध समाप्त। फिर भेजने के लिए नई सहमति दें।' : 'Request finished. Fresh consent is required to send again.';
    }
"""


def import_transcript() -> rx.Component:
    return rx.el.form(
        rx.el.h2(
            tr("Review transcript"),
            class_name="text-xl font-semibold text-[var(--vm-ink)]",
        ),
        rx.el.label(
            tr("Note title"),
            html_for="import-title",
            class_name="mt-5 mb-2 block text-xs text-[var(--vm-muted)]",
        ),
        rx.el.input(
            name="title",
            id="import-title",
            max_length=160,
            placeholder=tr("Give this thought a name…"),
            class_name=FIELD,
        ),
        rx.el.label(
            tr("Category"),
            html_for="import-category",
            class_name="mt-4 mb-2 block text-xs text-[var(--vm-muted)]",
        ),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    NotesState.categories,
                    lambda c: rx.el.option(tr(c), value=c),
                ),
                name="category",
                id="import-category",
                default_value="Personal",
                class_name="w-full appearance-none rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-field)] py-3 pr-10 pl-4 text-sm text-[var(--vm-ink)]",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute top-3 right-4 h-5 w-5 text-[var(--vm-muted)]",
            ),
            class_name="relative",
        ),
        rx.el.label(
            tr("Editable transcript"),
            html_for="import-text",
            class_name="mt-4 mb-2 block text-xs text-[var(--vm-muted)]",
        ),
        rx.el.textarea(
            name="content",
            id="import-text",
            default_value=ImportState.transcript,
            key=ImportState.revision,
            max_length=100000,
            disabled=NotesState.capture_saved_id != "",
            class_name="min-h-64 w-full rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-field)] p-4 text-base leading-8 text-[var(--vm-ink)]",
        ),
        rx.cond(
            NotesState.capture_saved_id != "",
            rx.el.button(
                tr("Open saved note"),
                type="button",
                on_click=NotesState.go(f"/notes/{NotesState.capture_saved_id}"),
                class_name=SECONDARY,
            ),
            rx.el.button(
                tr("Save transcript as note"),
                type="submit",
                disabled=NotesState.saving | NotesState.storage_invalid,
                class_name=PRIMARY,
            ),
        ),
        rx.el.p(
            rx.cond(
                SettingsState.language == "hi",
                "केवल पाठ सहेजा जाता है। सहेजना विफल हो तो यह पेज खुला रखें और फिर प्रयास करें। जाने पर बिना सहेजा प्रतिलेख खो जाता है।",
                "Only text is saved. Keep this page open if saving fails and retry. Leaving discards an unsaved transcript.",
            ),
            class_name="mt-4 text-xs leading-6 text-[var(--vm-muted)]",
        ),
        on_submit=ImportState.save,
        class_name="mt-6 rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-5 sm:p-7",
    )


def audio_import() -> rx.Component:
    return shell(
        rx.el.div(
            rx.el.h1(
                tr("Import audio"),
                class_name="font-['DM_Sans'] text-3xl font-semibold text-[var(--vm-ink)]",
            ),
            rx.el.p(
                tr("MP3, M4A, WAV, WebM or MP4 · maximum 20 MB"),
                class_name="mt-3 text-sm text-[var(--vm-muted)]",
            ),
            rx.el.section(
                rx.icon(
                    "file-audio",
                    class_name="mb-4 h-9 w-9 text-[var(--vm-accent)]",
                ),
                rx.el.label(
                    tr("Choose an audio file"),
                    html_for="audio-file",
                    class_name="mb-3 block text-sm font-semibold text-[var(--vm-ink)]",
                ),
                rx.el.input(
                    type="file",
                    id="audio-file",
                    accept=".mp3,.m4a,.wav,.webm,.mp4",
                    disabled=ImportState.unavailable != "",
                    class_name="w-full rounded-2xl border border-[var(--vm-border)] bg-[var(--vm-field)] p-4 text-sm text-[var(--vm-ink)] file:mr-4 file:rounded-xl file:border-0 file:bg-[var(--vm-lavender)] file:px-4 file:py-2 file:text-[var(--vm-accent)]",
                ),
                rx.el.p(
                    id="audio-client-status",
                    role="status",
                    aria_live="polite",
                    class_name="mt-3 break-words text-sm text-[var(--vm-accent)]",
                ),
                rx.el.p(
                    tr(
                        "Selection stays in your browser until you explicitly agree and send."
                    ),
                    class_name="mt-3 text-xs leading-6 text-[var(--vm-muted)]",
                ),
                rx.el.p(
                    rx.cond(
                        SettingsState.language == "hi",
                        "सहमत होकर भेजने पर पूरी ऑडियो फ़ाइल ऐप के सर्वर से बाहरी प्रतिलेखन प्रदाता को जाएगी। यह डिवाइस पर प्रसंस्करण नहीं है। प्रदाता अपनी नीति के अनुसार ऑडियो रख सकता है। संवेदनशील ऑडियो न भेजें। VoiceMate ऑडियो को डिस्क पर नहीं लिखता और न सहेजता है; अनुरोध के दौरान अस्थायी मेमोरी में प्रक्रिया होती है। हर प्रयास के लिए नई सहमति ज़रूरी है।",
                        "Agreeing and sending transmits the full audio through this app's server to its external transcription provider. This is not on-device processing. The provider may retain audio under its own policies; avoid sensitive recordings. VoiceMate does not write audio to disk or save it; audio is processed temporarily in memory during the request. Each retry needs fresh consent.",
                    ),
                    class_name="mt-4 text-sm leading-6 text-[var(--vm-muted)]",
                ),
                rx.cond(
                    ImportState.unavailable != "",
                    rx.el.p(
                        tr(ImportState.unavailable),
                        role="status",
                        class_name="mt-4 rounded-2xl bg-[var(--vm-lavender)] p-4 text-sm text-[var(--vm-accent)]",
                    ),
                ),
                rx.el.label(
                    rx.el.input(
                        type="checkbox",
                        id="audio-consent",
                        disabled=ImportState.unavailable != "",
                        class_name="h-5 w-5 accent-[#6757C8]",
                    ),
                    tr("I consent to send this audio for transcription"),
                    class_name="mt-5 flex items-start gap-3 text-sm text-[var(--vm-ink)]",
                ),
                rx.el.div(
                    rx.el.button(
                        rx.icon("upload", class_name="h-4 w-4"),
                        rx.cond(
                            ImportState.busy,
                            tr("Transcribing…"),
                            tr("Send audio & transcribe"),
                        ),
                        id="audio-send",
                        disabled=(ImportState.unavailable != "")
                        | ImportState.busy,
                        on_click=[
                            rx.call_script(
                                "(() => { const button = document.getElementById('audio-send'); if (button) button.disabled = true; })()"
                            ),
                            ImportState.begin,
                            rx.call_script(
                                f"(async () => {{ const TOKEN = {ImportState.token.to_string()}; const ENDPOINT = {ImportState.endpoint.to_string()}; const LANGUAGE = {SettingsState.language.to_string()}; const UNAVAILABLE = {ImportState.unavailable.to_string()}; {SEND_SCRIPT} }})()",
                                callback=ImportState.receive,
                            ),
                        ],
                        class_name=PRIMARY,
                    ),
                    rx.el.button(
                        tr("Clear selection"),
                        on_click=rx.call_script(
                            "(() => { if (window.vmAudioAbort) return; document.getElementById('audio-file').value = ''; document.getElementById('audio-consent').checked = false; document.getElementById('audio-client-status').textContent = ''; })()"
                        ),
                        class_name=SECONDARY,
                    ),
                    class_name="mt-5 flex flex-wrap gap-3",
                ),
                on_mount=rx.call_script(CLIENT_INIT),
                class_name="mt-6 rounded-3xl border border-[var(--vm-border)] bg-[var(--vm-card)] p-5 sm:p-7",
            ),
            rx.el.p(
                tr(ImportState.error),
                role="alert",
                class_name="mt-4 text-sm text-red-600",
            ),
            rx.el.p(
                tr(ImportState.feedback),
                role="status",
                class_name="mt-4 text-sm text-[var(--vm-accent)]",
            ),
            rx.cond(ImportState.transcript != "", import_transcript()),
            on_unmount=rx.call_script(
                "if (window.vmAudioAbort) { window.vmAudioAbort.abort(); window.vmAudioAbort = null; }"
            ),
        )
    )
