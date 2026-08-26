from __future__ import annotations

from deskboard.presentation.finance_presenter import FinancePresenter
from deskboard.providers.catalog import FINANCE_CATALOG


class FakeFinanceService:
    def __init__(self) -> None:
        self.items = [
            FINANCE_CATALOG.require("gold.au9999"),
            FINANCE_CATALOG.require("fx.usd_cny"),
            FINANCE_CATALOG.require("fx.jpy_cny"),
            FINANCE_CATALOG.require("index.sse"),
        ]

    def enabled_items(self):
        return list(self.items)


class FakeCache:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.payloads = {
            "gold.au9999": {
                "key": "gold.au9999",
                "value": 968.14,
                "change_percent": -0.21,
                "market_state": "closed",
            },
            "fx.usd_cny": {"key": "fx.usd_cny", "value": 6.7808},
            "fx.jpy_cny": {"key": "fx.jpy_cny", "value": 0.042636},
            "index.sse": {
                "key": "index.sse",
                "value": 3903.72,
                "change_percent": 0.09,
            },
        }

    def read_cached_payload(self, cache_key: str):
        self.calls.append(cache_key)
        return self.payloads.get(cache_key)


def test_presenter_keeps_global_order_filters_category_and_formats_fx_basis():
    cache = FakeCache()
    presenter = FinancePresenter(FakeFinanceService(), cache)

    state = presenter.present()
    assert [item["key"] for item in state["items"]] == [
        "gold.au9999",
        "fx.usd_cny",
        "fx.jpy_cny",
        "index.sse",
    ]
    assert state["items"][1]["valueText"] == "1 USD = 6.7808 CNY"
    assert state["items"][2]["valueText"] == "1 CNY = 23.4544 JPY"
    assert state["items"][3]["valueText"] == "3903.72"
    assert cache.calls == [
        "gold.au9999",
        "fx.usd_cny",
        "fx.jpy_cny",
        "index.sse",
    ]

    fx = presenter.present(category="fx", max_items=1)
    assert [item["key"] for item in fx["items"]] == ["fx.usd_cny"]


def test_presenter_exposes_direction_and_only_reliable_closed_label():
    presenter = FinancePresenter(FakeFinanceService(), FakeCache())
    state = presenter.present()

    gold = state["items"][0]
    assert gold["direction"] == "down"
    assert gold["changePercentText"] == "-0.21%"
    assert gold["marketState"] == "closed"
    assert gold["secondaryText"] == "上一交易日收盘"

    usd = state["items"][1]
    assert usd["direction"] == "unknown"
    assert usd["marketState"] == "unknown"
    assert "secondaryText" not in usd


def test_presenter_does_not_expose_cache_or_provider_fields():
    state = FinancePresenter(FakeFinanceService(), FakeCache()).present()
    item = state["items"][0]

    assert set(item) == {
        "key",
        "category",
        "name",
        "valueText",
        "changePercentText",
        "direction",
        "marketState",
        "secondaryText",
    }
