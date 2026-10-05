import reflex as rx

import logging as stdlib_logging


_SAFE_CODES: dict[str, str] = {
    "provider_error": "provider_error",
    "provider_response_invalid": "provider_response_invalid",
    "provider_rate_limit": "provider_rate_limit",
    "insufficient_credits": "insufficient_credits",
    "rate_limited": "rate_limited",
    "timeout": "timeout",
    "offline": "offline",
    "provider_auth": "provider_auth",
    "unsupported_transcription": "unsupported_transcription",
    "audio_request_failed": "audio_request_failed",
    "import_failed": "import_failed",
    "invalid_input": "invalid_input",
    "result_storage_failed": "result_storage_failed",
    "ai_request_failed": "ai_request_failed",
}


def _safe_code(code: object) -> str:
    if type(code) is not str:
        return "provider_error"
    return _SAFE_CODES.get(code, "provider_error")


class SafeLog:
    def exception(
        self, message: object, *args: object, **kwargs: object
    ) -> None:
        stdlib_logging.warning("provider_error")

    def warning(self, code: object, *args: object, **kwargs: object) -> None:
        stdlib_logging.warning(_safe_code(code))

    def error(self, code: object, *args: object, **kwargs: object) -> None:
        stdlib_logging.error(_safe_code(code))

    def debug(self, code: object, *args: object, **kwargs: object) -> None:
        stdlib_logging.debug(_safe_code(code))


safe_log = SafeLog()
