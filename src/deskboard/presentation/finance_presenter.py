"""Convert normalized Finance cache payloads into Dashboard ViewModels."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from math import isfinite
from typing import Protocol, TypedDict

from deskboard.models.finance import FinanceCatalogItem, FinanceCategory
from deskboard.providers.catalog import DEFAULT_FINANCE_CATALOG

FINANCE_DISPLAY_CATEGORIES = frozenset(
    {"gold", "fx", "china_indices", "us_indices"}
)
FINANCE_MARKET_STATES = frozenset({"open", "closed", "unknown"})


class FinanceItemViewModel(TypedDict, total=False):
    key: str
    category: FinanceCategory
    name: str
    valueText: str
    changePercentText: str
    direction: str
    marketState: str
    secondaryText: str


class FinanceViewModel(TypedDict):
    items: list[FinanceItemViewModel]


class FinanceServiceLike(Protocol):
    def enabled_items(self) -> list[FinanceCatalogItem]: ...


class FinanceCacheReader(Protocol):
    def read_cached_payload(self, cache_key: str) -> object | None: ...


class FinancePresenter:
    """Read global Finance preferences and one shared cache path."""

    def __init__(
        self,
        finance_service: FinanceServiceLike,
        cache_reader: FinanceCacheReader | None = None,
        *,
        refresh_service: FinanceCacheReader | None = None,
    ) -> None:
        if cache_reader is not None and refresh_service is not None:
            raise TypeError("provide cache_reader or refresh_service, not both")
        self._finance_service = finance_service
        self._cache_reader = cache_reader or refresh_service

    def present(
        self,
        *,
        category: str | None = None,
        max_items: int | None = None,
    ) -> FinanceViewModel:
        selected_category = normalize_finance_category(category)
        if max_items is not None:
            _validate_max_items(max_items)

        ordered_items = self._enabled_items()
        payloads: dict[str, object] = {}
        for item in ordered_items:
            if selected_category is not None and item.category != selected_category:
                continue
            payload = self._read_cached_payload(item.key)
            if payload is not None:
                payloads[item.key] = payload

        return present_finance(
            payloads,
            items=ordered_items,
            category=selected_category,
            max_items=max_items,
        )

    present_finance = present

    def _enabled_items(self) -> tuple[FinanceCatalogItem, ...]:
        method = getattr(self._finance_service, "enabled_items", None)
        if not callable(method):
            method = getattr(self._finance_service, "list_enabled_items", None)
        if not callable(method):
            raise TypeError("Finance service must expose enabled_items")
        items = tuple(method())
        if any(not isinstance(item, FinanceCatalogItem) for item in items):
            raise TypeError("Finance service enabled_items must contain catalog items")
        return items

    def _read_cached_payload(self, cache_key: str) -> object | None:
        if self._cache_reader is None:
            return None
        reader = getattr(self._cache_reader, "read_cached_payload", None)
        if not callable(reader):
            raise TypeError("Finance cache reader must expose read_cached_payload")
        return reader(cache_key)


def present_finance(
    finance_by_key: Mapping[str, object],
    *,
    items: Iterable[FinanceCatalogItem] | None = None,
    catalog: Iterable[FinanceCatalogItem] | None = None,
    category: str | None = None,
    max_items: int | None = None,
) -> FinanceViewModel:
    """Present cached items in the supplied global catalog order."""

    selected_category = normalize_finance_category(category)
    if max_items is not None:
        _validate_max_items(max_items)
    if items is not None and catalog is not None:
        raise TypeError("provide items or catalog, not both")
    selected_items = items if items is not None else catalog
    if selected_items is None:
        selected_items = DEFAULT_FINANCE_CATALOG
    ordered_items = tuple(selected_items)
    if any(not isinstance(item, FinanceCatalogItem) for item in ordered_items):
        raise TypeError("Finance items must be FinanceCatalogItem values")

    view_items: list[FinanceItemViewModel] = []
    for item in ordered_items:
        if selected_category is not None and item.category != selected_category:
            continue
        payload = finance_by_key.get(item.key)
        if payload is None:
            continue
        view_item = present_finance_item(item, payload)
        if view_item is not None:
            view_items.append(view_item)
        if max_items is not None and len(view_items) >= max_items:
            break
    return {"items": view_items}


present_finance_state = present_finance


def present_finance_item(
    item: FinanceCatalogItem,
    payload: object,
) -> FinanceItemViewModel | None:
    """Present one normalized cache payload without leaking provider fields."""

    if not isinstance(item, FinanceCatalogItem):
        raise TypeError("Finance item must be a FinanceCatalogItem")
    if not isinstance(payload, Mapping):
        return None
    value = _finite_number(payload.get("value"))
    if value is None or value <= 0:
        return None

    view_item: FinanceItemViewModel = {
        "key": item.key,
        "category": item.category,
        "name": item.display_name,
        "valueText": _value_text(item, value),
        "direction": "unknown",
        "marketState": _market_state(payload),
    }

    change_percent = _finite_number(
        payload.get("change_percent", payload.get("changePercent"))
    )
    if change_percent is not None:
        view_item["changePercentText"] = _format_number(
            item.change_percent_format, change_percent
        )
        view_item["direction"] = _direction(change_percent)

    if view_item["marketState"] == "closed":
        view_item["secondaryText"] = "上一交易日收盘"
    return view_item


def normalize_finance_category(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("Finance category must be a string")
    normalized = value.strip().lower()
    if normalized in {"", "overview", "finance_overview"}:
        return None
    if normalized not in FINANCE_DISPLAY_CATEGORIES:
        raise ValueError(f"Unsupported Finance category: {value}")
    return normalized


def _value_text(item: FinanceCatalogItem, value: float) -> str:
    formatted = _format_number(item.value_format, value)
    if item.category != "fx":
        return formatted
    foreign_unit = item.provider_internal_key
    if value >= 1:
        return f"1 {foreign_unit} = {formatted} CNY"
    reciprocal = _format_number(item.value_format, 1 / value)
    return f"1 CNY = {reciprocal} {foreign_unit}"


def _market_state(payload: Mapping[str, object]) -> str:
    value = payload.get("market_state", payload.get("marketState"))
    if not isinstance(value, str):
        return "unknown"
    normalized = value.strip().lower()
    return normalized if normalized in FINANCE_MARKET_STATES else "unknown"


def _direction(change_percent: float) -> str:
    if change_percent > 0:
        return "up"
    if change_percent < 0:
        return "down"
    return "flat"


def _format_number(format_string: str, value: float) -> str:
    try:
        return format_string.format(value)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return f"{value:g}"


def _finite_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if isfinite(result) else None


def _validate_max_items(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("Finance max_items must be an integer")
    if value < 0:
        raise ValueError("Finance max_items must not be negative")
