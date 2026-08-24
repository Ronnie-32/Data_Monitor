"""Code-owned FinanceCatalog for the Task 1 validated source whitelist."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from deskboard.models.finance import FinanceCatalogItem, FinanceCategory

_SGE_HOME = "https://www.sge.com.cn/"
_CHINAMONEY_HOME = "https://www.chinamoney.com.cn/"
_TENCENT_HOME = "https://finance.qq.com/"


VALIDATED_FINANCE_ITEMS = (
    FinanceCatalogItem(
        key="gold.au9999",
        display_name="Au99.99",
        category="gold",
        unit="CNY/g",
        value_format="{:.2f}",
        change_format="{:+.2f}",
        provider_group="gold",
        provider_internal_key="gold_au9999",
        source_name="上海黄金交易所",
        source_homepage=_SGE_HOME,
    ),
    FinanceCatalogItem(
        key="fx.usd_cny",
        display_name="美元/人民币",
        category="fx",
        unit="CNY/1 USD",
        value_format="{:.4f}",
        change_format="{:+.4f}",
        provider_group="fx",
        provider_internal_key="USD",
        source_name="中国外汇交易中心",
        source_homepage=_CHINAMONEY_HOME,
    ),
    FinanceCatalogItem(
        key="fx.eur_cny",
        display_name="欧元/人民币",
        category="fx",
        unit="CNY/1 EUR",
        value_format="{:.4f}",
        change_format="{:+.4f}",
        provider_group="fx",
        provider_internal_key="EUR",
        source_name="中国外汇交易中心",
        source_homepage=_CHINAMONEY_HOME,
    ),
    FinanceCatalogItem(
        key="fx.jpy_cny",
        display_name="日元/人民币",
        category="fx",
        unit="CNY/1 JPY",
        value_format="{:.4f}",
        change_format="{:+.4f}",
        provider_group="fx",
        provider_internal_key="JPY",
        source_name="中国外汇交易中心",
        source_homepage=_CHINAMONEY_HOME,
    ),
    FinanceCatalogItem(
        key="fx.hkd_cny",
        display_name="港元/人民币",
        category="fx",
        unit="CNY/1 HKD",
        value_format="{:.4f}",
        change_format="{:+.4f}",
        provider_group="fx",
        provider_internal_key="HKD",
        source_name="中国外汇交易中心",
        source_homepage=_CHINAMONEY_HOME,
    ),
    FinanceCatalogItem(
        key="index.sse",
        display_name="上证指数",
        category="china_indices",
        unit="index points",
        value_format="{:.2f}",
        change_format="{:+.2f}",
        provider_group="indices",
        provider_internal_key="s_sh000001",
        source_name="腾讯行情",
        source_homepage=_TENCENT_HOME,
    ),
    FinanceCatalogItem(
        key="index.szse",
        display_name="深证成指",
        category="china_indices",
        unit="index points",
        value_format="{:.2f}",
        change_format="{:+.2f}",
        provider_group="indices",
        provider_internal_key="s_sz399001",
        source_name="腾讯行情",
        source_homepage=_TENCENT_HOME,
    ),
    FinanceCatalogItem(
        key="index.chinext",
        display_name="创业板指",
        category="china_indices",
        unit="index points",
        value_format="{:.2f}",
        change_format="{:+.2f}",
        provider_group="indices",
        provider_internal_key="s_sz399006",
        source_name="腾讯行情",
        source_homepage=_TENCENT_HOME,
    ),
    FinanceCatalogItem(
        key="index.csi300",
        display_name="沪深300",
        category="china_indices",
        unit="index points",
        value_format="{:.2f}",
        change_format="{:+.2f}",
        provider_group="indices",
        provider_internal_key="sh000300",
        source_name="腾讯行情",
        source_homepage=_TENCENT_HOME,
    ),
    FinanceCatalogItem(
        key="index.dow",
        display_name="道琼斯",
        category="us_indices",
        unit="index points",
        value_format="{:.2f}",
        change_format="{:+.2f}",
        provider_group="indices",
        provider_internal_key="us.DJI",
        source_name="腾讯行情",
        source_homepage=_TENCENT_HOME,
    ),
    FinanceCatalogItem(
        key="index.sp500",
        display_name="标普500",
        category="us_indices",
        unit="index points",
        value_format="{:.2f}",
        change_format="{:+.2f}",
        provider_group="indices",
        provider_internal_key="us.INX",
        source_name="腾讯行情",
        source_homepage=_TENCENT_HOME,
    ),
    FinanceCatalogItem(
        key="index.nasdaq",
        display_name="纳斯达克综合",
        category="us_indices",
        unit="index points",
        value_format="{:.2f}",
        change_format="{:+.2f}",
        provider_group="indices",
        provider_internal_key="us.IXIC",
        source_name="腾讯行情",
        source_homepage=_TENCENT_HOME,
    ),
)


class FinanceCatalog:
    """Immutable-in-use collection of approved finance catalog entries."""

    def __init__(self, items: Iterable[FinanceCatalogItem] = VALIDATED_FINANCE_ITEMS) -> None:
        entries = tuple(items)
        if any(not isinstance(item, FinanceCatalogItem) for item in entries):
            raise TypeError("FinanceCatalog items must be FinanceCatalogItem values")
        keys = [item.key for item in entries]
        if len(keys) != len(set(keys)):
            raise ValueError("FinanceCatalog item keys must be unique")
        self._items = entries
        self._by_key = {item.key: item for item in entries}

    @property
    def items(self) -> tuple[FinanceCatalogItem, ...]:
        return self._items

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(item.key for item in self._items)

    @property
    def available_categories(self) -> tuple[FinanceCategory, ...]:
        return tuple(
            category
            for category in ("gold", "fx", "china_indices", "us_indices")
            if self.is_category_available(category)
        )  # type: ignore[return-value]

    def get(self, key: str) -> FinanceCatalogItem | None:
        return self._by_key.get(_validated_lookup_key(key))

    def require(self, key: str) -> FinanceCatalogItem:
        normalized = _validated_lookup_key(key)
        item = self._by_key.get(normalized)
        if item is None:
            raise LookupError(f"Finance catalog item {normalized} does not exist")
        return item

    def items_for_category(self, category: str) -> tuple[FinanceCatalogItem, ...]:
        return tuple(item for item in self._items if item.category == category)

    def is_category_available(self, category: str) -> bool:
        return bool(self.items_for_category(category))

    def __iter__(self) -> Iterator[FinanceCatalogItem]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)


FINANCE_CATALOG = FinanceCatalog()
DEFAULT_FINANCE_CATALOG = FINANCE_CATALOG


def _validated_lookup_key(key: object) -> str:
    if not isinstance(key, str):
        raise TypeError("Finance catalog key must be a string")
    normalized = key.strip()
    if not normalized:
        raise ValueError("Finance catalog key must not be empty")
    return normalized
