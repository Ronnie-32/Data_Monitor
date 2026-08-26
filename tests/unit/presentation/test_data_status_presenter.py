from __future__ import annotations

import sqlite3
from datetime import datetime

from deskboard.database.schema import migrate
from deskboard.presentation.data_status_presenter import (
    SourceMetadata,
    present_data_status,
)
from deskboard.providers.base import NetworkItem
from deskboard.repositories.network_repository import NetworkRepository

NOW = datetime(2026, 8, 25, 10, 30)


def test_data_status_rows_join_network_state_cache_and_source_metadata():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    repository = NetworkRepository(connection)
    repository.save_success("weather.beijing", {"temperature": 25}, NOW)
    repository.record_failure("gold.au9999", NOW, "上游暂时不可用")

    rows = present_data_status(
        [
            NetworkItem("weather.beijing", "weather"),
            NetworkItem("gold.au9999", "gold"),
            NetworkItem("fx.usd_cny", "fx", enabled=False),
        ],
        repository,
        source_metadata={
            "weather": SourceMetadata("中国天气网", "https://www.weather.com.cn/"),
            "gold": SourceMetadata("上海黄金交易所", "https://www.sge.com.cn/"),
        },
        active_groups=("fx",),
    )

    assert [row.key for row in rows] == [
        "weather.beijing",
        "gold.au9999",
        "fx.usd_cny",
    ]
    assert rows[0].status == "success"
    assert rows[0].last_attempt_at == NOW
    assert rows[0].last_success_at == NOW
    assert rows[0].source_name == "中国天气网"
    assert rows[0].refresh_available is True
    assert rows[1].status == "error"
    assert rows[1].last_success_at is None
    assert rows[1].last_error == "上游暂时不可用"
    assert rows[2].status == "disabled"
    assert rows[2].refresh_available is False

    payload = rows[0].as_dict()
    assert payload["group"] == "weather"
    assert payload["lastAttempt"] == NOW.isoformat()
    assert payload["lastSuccess"] == NOW.isoformat()
    assert payload["attribution"]["name"] == "中国天气网"
