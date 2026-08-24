"""CNY FX provider using the validated China Money CcprHisNew source."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

from deskboard.providers.base import NetworkItem, ProviderItemResult, ProviderResult
from deskboard.providers.errors import ProviderDataError, ProviderParseError
from deskboard.providers.http_client import HttpClient

FX_GROUP = "fx"
CHINAMONEY_URL = "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-ccpr/CcprHisNew"
FX_LOOKBACK_DAYS = 14
FX_CURRENCIES = ("USD", "EUR", "JPY", "HKD")
FX_ITEM_KEYS = {
    "USD": "fx.usd_cny",
    "EUR": "fx.eur_cny",
    "JPY": "fx.jpy_cny",
    "HKD": "fx.hkd_cny",
}
FX_QUOTATIONS = {
    "USD": (("USD/CNY", 1.0),),
    "EUR": (("EUR/CNY", 1.0),),
    "JPY": (("100JPY/CNY", 0.01), ("JPY/CNY", 1.0)),
    "HKD": (("HKD/CNY", 1.0),),
}


def parse_fx(raw: bytes | str) -> dict[str, object]:
    """Parse and normalize the latest CNY reference-rate record.

    The quotation label controls normalization.  This keeps the selected
    source's ``100JPY/CNY`` convention correct while accepting an equivalent
    per-one-unit record without dividing it a second time.
    """

    payload = _load_json(raw)
    data = payload.get("data")
    records = payload.get("records")
    if not isinstance(data, Mapping) or not isinstance(records, list) or not records:
        raise ProviderParseError("FX response shape is invalid")
    labels = data.get("searchlist")
    if not isinstance(labels, list):
        raise ProviderParseError("FX response shape is invalid: searchlist")
    latest = records[0]
    if not isinstance(latest, Mapping):
        raise ProviderParseError("FX response shape is invalid: latest record")
    values = latest.get("values")
    if not isinstance(values, list) or len(labels) != len(values):
        raise ProviderParseError("FX labels and values are inconsistent")
    date_text = latest.get("date")
    if not isinstance(date_text, str) or not date_text.strip():
        raise ProviderDataError("FX latest record date is missing")

    upstream: dict[str, object] = {}
    for label, value in zip(labels, values, strict=True):
        if not isinstance(label, str) or not label.strip():
            raise ProviderParseError("FX quotation label is invalid")
        if label in upstream:
            raise ProviderParseError(f"FX quotation label is duplicated: {label}")
        upstream[label] = value

    items: dict[str, dict[str, object]] = {}
    for currency in FX_CURRENCIES:
        quotation, multiplier = _select_quotation(currency, upstream)
        raw_value = _positive_number(upstream[quotation], field=quotation)
        items[currency] = {
            "value": raw_value * multiplier,
            "unit": f"CNY/1 {currency}",
            "upstream_quotation": quotation,
            "upstream_value": raw_value,
        }
    return {
        "date": date_text.strip(),
        "basis": "CNY per 1 foreign-currency unit",
        "items": items,
    }


class FXProvider:
    """Fetch fixed USD/EUR/JPY/HKD items from one selected FX source."""

    group = FX_GROUP

    def __init__(
        self,
        http_client: HttpClient | None = None,
        *,
        as_of: date | None = None,
    ) -> None:
        self._http = http_client or HttpClient()
        self._as_of = _validate_date(as_of or date.today())
        self.items = tuple(
            NetworkItem(FX_ITEM_KEYS[currency], self.group)
            for currency in FX_CURRENCIES
        )

    def fetch(self) -> ProviderResult:
        parsed = parse_fx(self._get_raw(_fx_url(self._as_of)))
        parsed_items = parsed["items"]
        if not isinstance(parsed_items, Mapping):
            raise ProviderDataError("FX normalized items are invalid")
        outcomes: list[ProviderItemResult] = []
        for currency in FX_CURRENCIES:
            item = parsed_items.get(currency)
            if not isinstance(item, Mapping):
                raise ProviderDataError(f"FX normalized item is missing: {currency}")
            item_key = FX_ITEM_KEYS[currency]
            outcomes.append(
                ProviderItemResult.success(
                    item_key,
                    {
                        "key": item_key,
                        "date": parsed["date"],
                        "value": item["value"],
                        "unit": item["unit"],
                        "basis": parsed["basis"],
                    },
                )
            )
        return ProviderResult.partial(outcomes)

    def _get_raw(self, url: str) -> bytes | str:
        get = getattr(self._http, "get", None)
        if callable(get):
            response = get(url, headers={"Accept": "application/json"})
            content = getattr(response, "content", None)
            if isinstance(content, (bytes, bytearray)):
                return bytes(content)
            text = getattr(response, "text", None)
            if isinstance(text, str):
                return text
        get_text = getattr(self._http, "get_text", None)
        if callable(get_text):
            return get_text(url, headers={"Accept": "application/json"})
        raise TypeError("FX HTTP client must provide get or get_text")


def _fx_url(as_of: date) -> str:
    params = {
        "startDate": (as_of - timedelta(days=FX_LOOKBACK_DAYS)).isoformat(),
        "endDate": as_of.isoformat(),
        "currency": "USD/CNY,EUR/CNY,100JPY/CNY,HKD/CNY",
        "pageNum": "1",
        "pageSize": "20",
    }
    return f"{CHINAMONEY_URL}?{urlencode(params)}"


def _load_json(raw: bytes | str) -> Mapping[str, object]:
    text = _decode(raw)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise ProviderParseError("FX response is not valid JSON") from error
    if not isinstance(payload, Mapping):
        raise ProviderParseError("FX response shape is invalid")
    return payload


def _decode(raw: bytes | str) -> str:
    if isinstance(raw, str):
        return raw
    if not isinstance(raw, bytes):
        raise ProviderParseError("FX response must be bytes or text")
    for encoding in ("utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ProviderParseError("FX response is neither UTF-8 nor GB18030")


def _select_quotation(currency: str, upstream: Mapping[str, object]) -> tuple[str, float]:
    for quotation, multiplier in FX_QUOTATIONS[currency]:
        if quotation in upstream:
            return quotation, multiplier
    expected = ", ".join(quotation for quotation, _multiplier in FX_QUOTATIONS[currency])
    raise ProviderParseError(f"FX record missing {expected}")


def _positive_number(value: object, *, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ProviderDataError(f"{field} is not numeric") from error
    if not math.isfinite(result):
        raise ProviderDataError(f"{field} is not finite")
    if result <= 0:
        raise ProviderDataError(f"{field} must be positive")
    return result


def _validate_date(value: object) -> date:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise TypeError("FX as_of must be a date")
    return value
