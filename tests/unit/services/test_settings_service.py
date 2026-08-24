from __future__ import annotations

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.repositories.settings_repository import SettingsRepository
from deskboard.services.settings_service import (
    AUTO_REFRESH_INTERVAL_MINUTES,
    SettingsService,
)


def test_settings_service_keeps_network_enablement_in_sqlite_and_interval_fixed(tmp_path):
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    service = SettingsService(SettingsRepository(connection))

    assert service.auto_refresh_interval_minutes == AUTO_REFRESH_INTERVAL_MINUTES == 60
    assert service.is_network_item_enabled("gold") is True
    service.set_network_item_enabled("gold", False)
    assert service.is_network_item_enabled("gold") is False
    assert service.get("network.enabled.gold") == "false"


def test_settings_service_uses_default_for_unrecognized_boolean_value(tmp_path):
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    service = SettingsService(SettingsRepository(connection))
    service.set("network.enabled.fx", "maybe")

    assert service.is_network_item_enabled("fx", default=True) is True
    assert service.is_network_item_enabled("fx", default=False) is False
