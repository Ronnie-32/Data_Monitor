"""Small application-setting decisions shared by services and Settings UI."""

from __future__ import annotations

from deskboard.repositories.settings_repository import SettingsRepository

AUTO_REFRESH_INTERVAL_MINUTES = 60


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


def _network_enabled_key(item_key: str) -> str:
    if not isinstance(item_key, str) or not item_key.strip():
        raise ValueError("network item key must not be empty")
    return f"network.enabled.{item_key.strip()}"

