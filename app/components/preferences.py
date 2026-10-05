import reflex as rx

from app.states.settings_state import SettingsState


def tr(text: str | rx.Var) -> rx.Var:
    return SettingsState.labels.get(text, text)
