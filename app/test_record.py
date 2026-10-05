import reflex as rx

import asyncio
import json
import unittest
from inspect import getsource

from test_utils import run_event

from app.pages.record import capture_controls
from app.states.record_state import BROWSER_INIT, RecordState, speech_error


class SpeechCaptureTests(unittest.TestCase):
    def snapshot(self, **overrides):
        data = dict(
            token="session",
            supported=True,
            status="finished",
            error="",
            text="Hello नमस्ते",
            interim="",
            elapsed=12,
        )
        data.update(overrides)
        return json.dumps(data)

    def state(self):
        state = RecordState()
        state.token = "session"
        state.status = "listening"
        state.transcript = "Kept words"
        state.language = "en-US"
        return state

    def test_unsupported_probe(self):
        state = self.state()
        asyncio.run(
            run_event(
                state.receive,
                self.snapshot(
                    supported=False,
                    status="error",
                    error="unsupported",
                    text="",
                ),
            )
        )
        self.assertTrue(state.probed)
        self.assertFalse(state.supported)
        self.assertFalse(state.active)
        self.assertIn("isn't available", state.error)

    def test_final_words_kept_on_error(self):
        for code in (
            "not-allowed",
            "service-not-allowed",
            "audio-capture",
            "network",
            "no-speech",
            "aborted",
            "interrupted",
            "language-not-supported",
            "unknown",
        ):
            state = self.state()
            asyncio.run(
                run_event(
                    state.receive, self.snapshot(status="error", error=code)
                )
            )
            self.assertEqual(state.transcript, "Hello नमस्ते")
            self.assertTrue(state.error)
            self.assertFalse(state.active)

    def test_final_and_cancel(self):
        state = self.state()
        asyncio.run(run_event(state.receive, self.snapshot()))
        self.assertEqual(state.transcript, "Hello नमस्ते")
        self.assertEqual(state.timer_label, "00:12")
        self.assertGreater(state.revision, 0)
        asyncio.run(
            run_event(
                state.receive,
                self.snapshot(status="cancelled", text="", elapsed=0),
            )
        )
        self.assertEqual(state.transcript, "")
        self.assertEqual(state.elapsed, 0)

    def test_stale_callback_ignored(self):
        state = self.state()
        asyncio.run(
            run_event(state.receive, self.snapshot(token="old", text="wrong"))
        )
        self.assertEqual(state.transcript, "Kept words")
        asyncio.run(run_event(state.receive, ""))
        self.assertEqual(state.transcript, "Kept words")

    def test_language_guard(self):
        state = self.state()
        asyncio.run(run_event(state.choose_language, "hi-IN"))
        self.assertEqual(state.language, "en-US")
        state.status = "finished"
        state.choose_language("hi-IN")
        self.assertEqual(state.language, "hi-IN")
        asyncio.run(run_event(state.choose_language, "invalid"))
        self.assertEqual(state.language, "hi-IN")

    def test_start_control_calls_browser_directly_with_selected_language(self):
        source = getsource(capture_controls)
        start_control = source.split('tr("Start")', 1)[1].split(
            "rx.el.button(", 1
        )[0]
        self.assertIn("on_click=rx.call_script(", start_control)
        self.assertIn("window.vmSpeech", start_control)
        self.assertIn("!c || c.closed", start_control)
        self.assertIn(
            "c.start({RecordState.language.to_string()})", start_control
        )
        self.assertIn("callback=RecordState.receive", start_control)
        self.assertNotIn("RecordState.start", start_control)

    def test_start_control_renders_language_as_json_string(self):
        rendered = str(capture_controls().render())
        start_position = rendered.find("c.start(")
        self.assertGreaterEqual(start_position, 0)
        start_expression = rendered[
            start_position : rendered.find("c.snapshot()", start_position)
        ]
        self.assertIn("JSON.stringify(", start_expression)
        self.assertIn("language_rx_state_", start_expression)
        self.assertNotIn('c.start("+reflex___state', start_expression)

    def test_watchdog_and_error_finish_contract(self):
        self.assertIn("startWatchdog: null", BROWSER_INIT)
        self.assertIn("setTimeout(() =>", BROWSER_INIT)
        self.assertIn("}, 12000)", BROWSER_INIT)
        self.assertIn("this.clearStartWatchdog();", BROWSER_INIT)
        self.assertIn(
            "this.error = event.error || 'start-failed';", BROWSER_INIT
        )
        self.assertIn("this.finish();", BROWSER_INIT)
        self.assertIn("try { r.abort(); } catch (_) {}", BROWSER_INIT)

    def test_receive_starting_then_error_preserves_final_text(self):
        state = self.state()
        asyncio.run(
            run_event(
                state.receive,
                self.snapshot(
                    status="starting", text="Words already finalized"
                ),
            )
        )
        self.assertTrue(state.active)
        self.assertEqual(state.transcript, "Words already finalized")
        asyncio.run(
            run_event(
                state.receive,
                self.snapshot(
                    status="error",
                    error="start-failed",
                    text="Words already finalized",
                ),
            )
        )
        self.assertFalse(state.active)
        self.assertEqual(state.transcript, "Words already finalized")
        self.assertIn("couldn't start", state.error)

    def test_error_messages_and_native_contract(self):
        self.assertEqual(speech_error(""), "")
        self.assertIn("HTTPS", speech_error("insecure"))
        self.assertIn("window.webkitSpeechRecognition", BROWSER_INIT)
        self.assertIn("r.start()", BROWSER_INIT)
        self.assertIn("this.recognition.stop()", BROWSER_INIT)
        self.assertIn("r.onend", BROWSER_INIT)
        self.assertIn("visibilitychange", BROWSER_INIT)
        self.assertNotIn("getUserMedia", BROWSER_INIT)
        self.assertNotIn("MediaRecorder", BROWSER_INIT)


if __name__ == "__main__":
    unittest.main()
