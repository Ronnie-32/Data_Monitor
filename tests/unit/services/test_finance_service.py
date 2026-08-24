from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pytest

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.models.profile import ProfileState
from deskboard.providers.base import NetworkItem
from deskboard.repositories.finance_repository import FinanceRepository
from deskboard.repositories.network_repository import NetworkRepository
from deskboard.repositories.profile_repository import ProfileRepository
from deskboard.repositories.settings_repository import SettingsRepository
from deskboard.services.finance_service import FinanceService
from deskboard.services.profile_service import ProfileService
from deskboard.services.status_service import StatusService


@dataclass
class FakeClock:
    current: datetime = datetime(2026, 8, 24, 9, 30)

    def now(self) -> datetime:
        return self.current


def make_service(tmp_path) -> tuple[FinanceService, object]:
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    return FinanceService(FinanceRepository(connection)), connection


def test_service_seeds_validated_catalog_and_global_order(tmp_path):
    service, _connection = make_service(tmp_path)

    assert [item.key for item in service.enabled_items()] == [
        "gold.au9999",
        "fx.usd_cny",
        "fx.eur_cny",
        "fx.jpy_cny",
        "fx.hkd_cny",
        "index.sse",
        "index.szse",
        "index.chinext",
        "index.csi300",
        "index.dow",
        "index.sp500",
        "index.nasdaq",
    ]


def test_service_rejects_arbitrary_keys_and_persists_enable_order_globally(tmp_path):
    service, connection = make_service(tmp_path)

    with pytest.raises(LookupError):
        service.set_enabled("user.entered.ticker", True)
    assert service.repository.get("user.entered.ticker") is None

    service.disable("gold.au9999")
    enabled_keys = [item.key for item in service.enabled_items()]
    service.reorder(list(reversed(enabled_keys)))

    reloaded = FinanceService(FinanceRepository(connection))
    assert [item.key for item in reloaded.enabled_items()] == list(reversed(enabled_keys))
    assert reloaded.is_enabled("gold.au9999") is False


def test_finance_preferences_are_not_profile_owned(tmp_path):
    service, connection = make_service(tmp_path)
    service.reorder([item.key for item in reversed(service.enabled_items())])
    expected = [item.key for item in service.enabled_items()]

    profiles = ProfileService(
        ProfileRepository(connection), FakeClock(), SettingsRepository(connection)
    )
    custom = profiles.save_as("Study", ProfileState())
    profiles.switch(custom.id)

    reloaded = FinanceService(FinanceRepository(connection))
    assert [item.key for item in reloaded.enabled_items()] == expected


def test_disabled_finance_items_are_not_enabled_for_global_network_status(tmp_path):
    service, connection = make_service(tmp_path)
    service.disable("gold.au9999")

    status = StatusService(
        NetworkRepository(connection), items=service.network_items()
    )

    assert "gold.au9999" not in status.snapshot().enabled_keys
    assert all(isinstance(item, NetworkItem) for item in service.network_items())
    assert "gold.au9999" not in {item.key for item in service.enabled_network_items()}


def test_market_payload_cache_remains_owned_by_network_repository(tmp_path):
    service, connection = make_service(tmp_path)
    network = NetworkRepository(connection)
    network.save_success("gold.au9999", {"value": 123.45}, FakeClock().now())

    assert network.get_cache("gold.au9999").payload == {"value": 123.45}
    assert all(
        item.item_key != "gold.au9999" or item.enabled
        for item in service.repository.list_preferences()
    )
    assert service.repository.list_preferences()[0].item_key == "gold.au9999"
