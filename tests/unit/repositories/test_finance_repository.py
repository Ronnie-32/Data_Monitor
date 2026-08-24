from __future__ import annotations

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.repositories.finance_repository import FinanceRepository


def make_repository(tmp_path) -> tuple[FinanceRepository, object]:
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    return FinanceRepository(connection), connection


def test_repository_persists_global_enabled_order_preferences(tmp_path):
    repository, connection = make_repository(tmp_path)
    repository.ensure_items(("gold.au9999", "fx.usd_cny", "index.sse"))

    assert [item.item_key for item in repository.list_preferences()] == [
        "gold.au9999",
        "fx.usd_cny",
        "index.sse",
    ]

    disabled = repository.set_enabled("gold.au9999", False)
    assert disabled.enabled is False
    repository.reorder(("index.sse", "fx.usd_cny", "gold.au9999"))

    reloaded = FinanceRepository(connection)
    assert [item.item_key for item in reloaded.list_preferences()] == [
        "index.sse",
        "fx.usd_cny",
        "gold.au9999",
    ]
    assert reloaded.require("gold.au9999").enabled is False


def test_repository_owns_preferences_only_and_never_market_payload_cache(tmp_path):
    repository, connection = make_repository(tmp_path)
    repository.ensure_items(("gold.au9999",))

    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(finance_preferences)")
    }
    assert columns == {"item_key", "enabled", "display_order"}
    assert not hasattr(repository, "save_success")
    assert connection.execute("SELECT COUNT(*) FROM network_cache").fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM network_state").fetchone()[0] == 0
