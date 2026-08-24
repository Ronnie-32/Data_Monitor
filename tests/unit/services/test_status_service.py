from __future__ import annotations

from datetime import datetime

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.providers.base import NetworkItem
from deskboard.repositories.network_repository import NetworkRepository
from deskboard.services.status_service import StatusService

NOW = datetime(2026, 8, 21, 9, 30)


def make_status(tmp_path, items: list[NetworkItem]):
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    repository = NetworkRepository(connection)
    status = StatusService(repository, items=items)
    return status, repository


def test_zero_enabled_or_unknown_network_data_is_grey(tmp_path):
    status, repository = make_status(
        tmp_path,
        [NetworkItem("weather", "weather", enabled=False)],
    )

    assert status.color == "grey"
    status.configure_items([])
    assert status.color == "grey"
    assert repository.get_state("weather") is None


def test_success_and_failure_are_derived_only_from_enabled_items(tmp_path):
    status, repository = make_status(
        tmp_path,
        [
            NetworkItem("weather", "weather"),
            NetworkItem("disabled-finance", "finance", enabled=False),
        ],
    )

    repository.save_success("weather", {"ok": True}, NOW)
    repository.record_failure("disabled-finance", NOW, "ignored")
    assert status.color == "green"

    repository.record_failure("weather", NOW, "provider failed")
    assert status.color == "red"


def test_refreshing_applicable_group_is_grey_until_all_enabled_items_resolve(tmp_path):
    status, repository = make_status(
        tmp_path,
        [
            NetworkItem("gold", "finance"),
            NetworkItem("fx", "finance"),
        ],
    )
    repository.save_success("gold", {"value": 1}, NOW)
    repository.save_success("fx", {"value": 2}, NOW)
    assert status.color == "green"

    status.begin_refresh("finance")
    assert status.color == "grey"
    status.end_refresh("finance")
    assert status.color == "green"


def test_unknown_enabled_item_is_grey_even_when_another_item_succeeds(tmp_path):
    status, repository = make_status(
        tmp_path,
        [NetworkItem("weather", "weather"), NetworkItem("gold", "finance")],
    )
    repository.save_success("weather", {"ok": True}, NOW)

    assert status.color == "grey"


def test_persisted_failure_is_restored_without_persisting_dot_color(tmp_path):
    status, repository = make_status(tmp_path, [NetworkItem("weather", "weather")])
    repository.record_failure("weather", NOW, "offline")
    assert status.color == "red"

    reloaded = StatusService(repository, items=[NetworkItem("weather", "weather")])
    assert reloaded.color == "red"
    assert not hasattr(reloaded, "persisted_color")
