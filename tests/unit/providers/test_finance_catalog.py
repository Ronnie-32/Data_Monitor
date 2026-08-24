from __future__ import annotations

from deskboard.providers.catalog import FINANCE_CATALOG, FinanceCatalog

VALIDATED_KEYS = {
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
}


def test_catalog_contains_only_task1_validated_fixed_items():
    assert set(FINANCE_CATALOG.keys) == VALIDATED_KEYS
    assert len(FINANCE_CATALOG) == len(VALIDATED_KEYS)
    assert all("ticker" not in item.key for item in FINANCE_CATALOG)


def test_catalog_entries_expose_metadata_and_share_source_groups():
    gold = FINANCE_CATALOG.require("gold.au9999")
    usd = FINANCE_CATALOG.require("fx.usd_cny")
    sse = FINANCE_CATALOG.require("index.sse")
    sp500 = FINANCE_CATALOG.require("index.sp500")

    assert (gold.display_name, gold.category, gold.unit) == ("Au99.99", "gold", "CNY/g")
    assert usd.provider_group == "fx"
    assert usd.provider_internal_key == "USD"
    assert usd.source_name == "中国外汇交易中心"
    assert usd.source_homepage == "https://www.chinamoney.com.cn/"
    assert sse.provider_group == sp500.provider_group == "indices"
    assert sse.provider_internal_key == "s_sh000001"
    assert sp500.provider_internal_key == "us.INX"
    assert all(item.value_format and item.change_format for item in FINANCE_CATALOG)
    assert all(
        item.source_name and item.source_homepage.startswith("https://") for item in FINANCE_CATALOG
    )


def test_catalog_marks_us_widget_unavailable_when_no_validated_us_item_exists():
    mainland_only = FinanceCatalog(
        item for item in FINANCE_CATALOG if item.category != "us_indices"
    )

    assert mainland_only.is_category_available("china_indices") is True
    assert mainland_only.is_category_available("us_indices") is False
    assert mainland_only.items_for_category("us_indices") == ()
