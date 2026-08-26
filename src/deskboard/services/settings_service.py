"""Small application-setting decisions shared by services and Settings UI."""

from __future__ import annotations

from deskboard.repositories.settings_repository import SettingsRepository

AUTO_REFRESH_INTERVAL_MINUTES = 60
TIMETABLE_HEADER_MODE_KEY = "timetable.header_mode"
DEFAULT_TIMETABLE_HEADER_MODE = "weekday_date"
TIMETABLE_HEADER_MODES = ("weekday", "weekday_date", "date")
UI_LANGUAGE_KEY = "ui.language"
DEFAULT_UI_LANGUAGE = "zh_CN"
UI_LANGUAGES = ("zh_CN", "en_US")


class SettingsService:
    """Keep DeskBoard-owned settings in SQLite through ``SettingsRepository``."""

    def __init__(self, repository: SettingsRepository) -> None:
        self._repository = repository

    def get(self, key: str, default: str | None = None) -> str | None:
        value = self._repository.get(key)
        return default if value is None else value

    def set(self, key: str, value: str) -> None:
        self._repository.set(key, value)

    def delete(self, key: str) -> bool:
        return self._repository.delete(key)

    @property
    def auto_refresh_interval_minutes(self) -> int:
        """Return the spec-fixed interval; this is not user-configurable in V1."""

        return AUTO_REFRESH_INTERVAL_MINUTES

    @property
    def ui_language(self) -> str:
        """Return the persisted native Settings language, defaulting to Chinese."""

        value = self._repository.get(UI_LANGUAGE_KEY)
        if value in UI_LANGUAGES:
            return value
        return DEFAULT_UI_LANGUAGE

    def set_ui_language(self, language: str) -> str:
        """Persist and return one of the supported native Settings languages."""

        if not isinstance(language, str):
            raise TypeError("language must be a string")
        normalized = language.strip()
        if normalized not in UI_LANGUAGES:
            raise ValueError(f"Unsupported Settings language: {language}")
        self._repository.set(UI_LANGUAGE_KEY, normalized)
        return normalized

    def is_network_item_enabled(self, item_key: str, *, default: bool = True) -> bool:
        value = self._repository.get(_network_enabled_key(item_key))
        if value is None:
            return default
        normalized = value.strip().casefold()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return default

    def set_network_item_enabled(self, item_key: str, enabled: bool) -> None:
        if type(enabled) is not bool:
            raise TypeError("network item enabled must be a bool")
        self._repository.set(_network_enabled_key(item_key), "true" if enabled else "false")

    @property
    def timetable_header_mode(self) -> str:
        value = self._repository.get(TIMETABLE_HEADER_MODE_KEY)
        if value is None:
            return DEFAULT_TIMETABLE_HEADER_MODE
        try:
            return normalize_timetable_header_mode(value)
        except ValueError:
            return DEFAULT_TIMETABLE_HEADER_MODE

    def set_timetable_header_mode(self, mode: str) -> str:
        normalized = normalize_timetable_header_mode(mode)
        self._repository.set(TIMETABLE_HEADER_MODE_KEY, normalized)
        return normalized


def _network_enabled_key(item_key: str) -> str:
    if not isinstance(item_key, str) or not item_key.strip():
        raise ValueError("network item key must not be empty")
    return f"network.enabled.{item_key.strip()}"


def normalize_timetable_header_mode(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("timetable header mode must be a string")
    aliases = {
        "weekday": "weekday",
        "weekday_only": "weekday",
        "weekday-only": "weekday",
        "weekday_date": "weekday_date",
        "weekday+date": "weekday_date",
        "weekday_date_combined": "weekday_date",
        "date": "date",
        "date_only": "date",
        "date-only": "date",
    }
    try:
        return aliases[value.strip().casefold()]
    except KeyError as error:
        raise ValueError(f"Unsupported timetable header mode: {value}") from error
