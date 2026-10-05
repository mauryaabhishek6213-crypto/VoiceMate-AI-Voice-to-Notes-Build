import reflex as rx

import json
import logging
from typing import Any
from uuid import uuid4


ERROR_MESSAGES = {
    "not-allowed": "Microphone permission was denied. Allow microphone access in your browser's site settings, then try again.",
    "service-not-allowed": "This browser's speech service is unavailable or blocked. Try another supported browser or type your note instead.",
    "audio-capture": "No working microphone was found. Check your microphone and browser settings.",
    "network": "The browser's speech service couldn't be reached. Check your connection and try again.",
    "no-speech": "No speech was recognized. Try again and speak clearly after listening starts.",
    "aborted": "Speech capture was interrupted. Any final recognized words have been kept.",
    "interrupted": "Capture stopped because this page was hidden. Any final recognized words have been kept.",
    "language-not-supported": "This browser's speech service doesn't support the selected language. Try the other language or another browser.",
    "unsupported": "Speech recognition isn't available in this browser. Try a browser with Web Speech support, or create a text note.",
    "insecure": "Microphone capture needs a secure HTTPS page (or localhost). Open this app securely to try again.",
    "start-failed": "Speech capture couldn't start. Check your microphone and browser speech service, then retry.",
}


BROWSER_INIT = r"""(() => {
    if (window.vmSpeech) window.vmSpeech.cleanup();
    const Constructor = window.SpeechRecognition || window.webkitSpeechRecognition;
    const c = {
        token: TOKEN, supported: !!Constructor && window.isSecureContext,
        status: 'idle', error: '', text: '', interim: '', elapsed: 0,
        recognition: null, clock: null, startWatchdog: null, started: 0, closed: false,
        snapshot() {
            return JSON.stringify({token: this.token, supported: this.supported,
                status: this.status, error: this.error, text: this.text,
                interim: this.interim, elapsed: this.elapsed});
        },
        clearClock() { clearInterval(this.clock); this.clock = null; },
        clearStartWatchdog() {
            clearTimeout(this.startWatchdog); this.startWatchdog = null;
        },
        stop() {
            if (!this.recognition || !['starting', 'listening'].includes(this.status)) return;
            this.status = 'stopping';
            try { this.recognition.stop(); }
            catch (_) { this.error = 'aborted'; this.finish(); }
        },
        finish() {
            this.clearStartWatchdog(); this.clearClock(); this.interim = '';
            if (!this.error && !this.sessionText.trim()) this.error = 'no-speech';
            this.status = this.error ? 'error' : 'finished';
            this.recognition = null;
        },
        detach() {
            const r = this.recognition;
            this.recognition = null;
            if (r) {
                r.onstart = r.onresult = r.onerror = r.onend = null;
                try { r.abort(); } catch (_) {}
            }
            this.clearStartWatchdog(); this.clearClock();
        },
        cancel() {
            this.detach();
            this.text = ''; this.interim = ''; this.elapsed = 0;
            this.error = ''; this.status = 'cancelled';
        },
        start(language) {
            if (this.closed || this.recognition || !this.supported) return;
            this.error = ''; this.interim = ''; this.elapsed = 0;
            const field = document.getElementById('capture-text');
            this.base = field ? field.value : this.text;
            this.sessionText = ''; this.text = this.base;
            this.status = 'starting';
            try {
                const r = new Constructor(); this.recognition = r;
                r.lang = language; r.continuous = true; r.interimResults = true;
                r.onstart = () => {
                    if (this.closed || this.recognition !== r) return;
                    this.clearStartWatchdog();
                    if (this.status !== 'stopping') this.status = 'listening';
                    this.started = Date.now();
                    this.clock = setInterval(() => {
                        this.elapsed = Math.floor((Date.now() - this.started) / 1000);
                        if (window.location.pathname !== '/record') this.cleanup();
                    }, 250);
                };
                r.onresult = event => {
                    if (this.closed || this.recognition !== r) return;
                    let final = '', interim = '';
                    for (let i = 0; i < event.results.length; i++) {
                        const result = event.results[i];
                        if (result.isFinal) final += result[0].transcript + ' ';
                        else interim += result[0].transcript + ' ';
                    }
                    this.sessionText = final.trim();
                    this.text = [this.base.trim(), this.sessionText].filter(Boolean).join('\n');
                    this.interim = interim.trim();
                };
                r.onerror = event => {
                    if (this.closed || this.recognition !== r) return;
                    this.error = event.error || 'start-failed';
                    this.detach();
                    this.finish();
                };
                r.onend = () => {
                    if (!this.closed && this.recognition === r) this.finish();
                };
                this.startWatchdog = setTimeout(() => {
                    if (this.closed || this.recognition !== r || this.status !== 'starting') return;
                    this.error = 'start-failed';
                    this.detach();
                    this.finish();
                }, 12000);
                r.start();
            } catch (e) {
                this.error = e.name === 'NotAllowedError' ? 'not-allowed' :
                    e.name === 'NotFoundError' ? 'audio-capture' : 'start-failed';
                this.detach(); this.status = 'error';
            }
        },
        cleanup() {
            this.closed = true; this.detach();
            window.removeEventListener('pagehide', pagehide);
            document.removeEventListener('visibilitychange', visibility);
            clearInterval(routeWatch);
        }
    };
    if (!c.supported) { c.status = 'error'; c.error = Constructor ? 'insecure' : 'unsupported'; }
    const pagehide = () => c.cleanup();
    const visibility = () => {
        if (document.hidden && c.recognition) { c.error = 'interrupted'; c.stop(); }
    };
    const routeWatch = setInterval(() => {
        if (window.location.pathname !== '/record') c.cleanup();
    }, 250);
    window.addEventListener('pagehide', pagehide);
    document.addEventListener('visibilitychange', visibility);
    window.vmSpeech = c;
    return c.snapshot();
})()"""

POLL_SCRIPT = "new Promise(resolve => setTimeout(() => resolve(window.vmSpeech && !window.vmSpeech.closed ? window.vmSpeech.snapshot() : ''), 1000))"
CLEANUP_SCRIPT = "if (window.vmSpeech) { window.vmSpeech.cleanup(); window.vmSpeech = null; }"


def speech_error(code: str) -> str:
    return (
        ERROR_MESSAGES.get(
            code,
            "Speech recognition stopped unexpectedly. Any final recognized words have been kept. Try again or edit the text below.",
        )
        if code
        else ""
    )


class RecordState(rx.State):
    token: str = ""
    supported: bool = False
    probed: bool = False
    status: str = "idle"
    language: str = "en-US"
    transcript: str = ""
    interim: str = ""
    elapsed: int = 0
    error: str = ""
    revision: int = 0

    @rx.var
    def active(self) -> bool:
        return self.status in ("starting", "listening", "stopping")

    @rx.var
    def timer_label(self) -> str:
        return f"{self.elapsed // 60:02d}:{self.elapsed % 60:02d}"

    @rx.var
    def status_label(self) -> str:
        return {
            "idle": "Ready when you are",
            "starting": "Waiting for microphone / speech service…",
            "listening": "Listening…",
            "stopping": "Finishing recognized words…",
            "finished": "Capture complete · review your text",
            "error": "Capture unavailable or interrupted",
            "cancelled": "Session discarded",
        }.get(self.status, "Checking your browser…")

    @rx.event
    async def load_record(self):
        from app.states.notes_state import NotesState

        notes = await self.get_state(NotesState)
        notes.load_record()
        from app.states.settings_state import SettingsState

        settings = await self.get_state(SettingsState)
        self.language = settings.preferences["speech"]
        self.token = str(uuid4())
        self.probed = False
        self.supported = False
        self.status = "idle"
        self.transcript = ""
        self.interim = ""
        self.error = ""
        self.elapsed = 0
        self.revision += 1
        return rx.call_script(
            BROWSER_INIT.replace("TOKEN", json.dumps(self.token)),
            callback=RecordState.receive,
        )

    @rx.event
    def choose_language(self, language: str):
        if not self.active and language in ("en-US", "hi-IN"):
            self.language = language

    @rx.event
    def start(self):
        if self.active or not self.supported:
            return
        self.status = "starting"
        self.error = ""
        return rx.call_script(
            f"(() => {{ const c = window.vmSpeech; if (!c || c.closed) return ''; c.start({json.dumps(self.language)}); return c.snapshot(); }})()",
            callback=RecordState.receive,
        )

    @rx.event
    def stop(self):
        return rx.call_script(
            "(() => { const c = window.vmSpeech; if (!c || c.closed) return ''; c.stop(); return c.snapshot(); })()",
            callback=RecordState.receive,
        )

    @rx.event
    def cancel(self):
        return rx.call_script(
            "(() => { const c = window.vmSpeech; if (!c || c.closed) return ''; c.cancel(); return c.snapshot(); })()",
            callback=RecordState.receive,
        )

    @rx.event
    def receive(self, raw: str):
        if not raw:
            return
        try:
            data = json.loads(raw)
            if not isinstance(data, dict) or data.get("token") != self.token:
                return
            previous_active = self.active
            self.probed = True
            self.supported = data.get("supported") is True
            self.status = str(data.get("status", "error"))
            self.error = speech_error(str(data.get("error", "")))
            self.elapsed = max(0, int(data.get("elapsed", 0)))
            self.interim = str(data.get("interim", ""))
            self.transcript = str(data.get("text", ""))
            if (
                previous_active
                and not self.active
                or self.status == "cancelled"
            ):
                self.revision += 1
        except (ValueError, TypeError) as e:
            logging.exception(f"Error: {e}")
            self.status = "error"
            self.error = speech_error("start-failed")
            return rx.call_script(CLEANUP_SCRIPT)
        if self.active:
            return rx.call_script(POLL_SCRIPT, callback=RecordState.receive)

    @rx.event
    async def save(self, form_data: dict[str, Any]):
        from app.states.notes_state import NotesState

        notes = await self.get_state(NotesState)
        if self.active or notes.saving or notes.capture_saved_id:
            return
        self.transcript = str(form_data.get("content", ""))
        if not self.transcript.strip():
            self.error = (
                "Add recognized words or edit the transcript before saving."
            )
            return
        self.error = ""
        return NotesState.save_transcript(
            str(form_data.get("title", "")),
            self.transcript,
            str(form_data.get("category", "Personal")),
        )
