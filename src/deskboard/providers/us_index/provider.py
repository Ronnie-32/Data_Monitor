"""U.S. index provider using the validated Tencent quote endpoint."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping

from deskboard.providers.base import NetworkItem, ProviderItemResult, ProviderResult
from deskboard.providers.errors import ProviderDataError, ProviderParseError
from deskboard.providers.http_client import HttpClient

US_INDEX_GROUP = "us_indices"
US_INDEX_URL = "https://qt.gtimg.cn/q=us.DJI,us.INX,us.IXIC"
US_INDEX_ITEM_KEYS = (
    "index.dow",
    "index.sp500",
    "index.nasdaq",
)

# Tencent's U.S. index records expose current value at position 3 and the
# change/change-percent fields at positions 31/32.
_SOURCE_FIELDS: Mapping[str, tuple[str, str, int, int, int]] = {
    "v_us.DJI": ("index.dow", "道琼斯", 3, 31, 32),
    "v_us.INX": ("index.sp500", "标普500", 3, 31, 32),
    "v_us.IXIC": ("index.nasdaq", "纳斯达克综合", 3, 31, 32),
}
_ASSIGNMENT_RE = re.compile(r'(v_[A-Za-z0-9_.]+)\s*=\s*"([^"]*)"\s*;')


def parse_us_indices(raw: bytes | str) -> dict[str, dict[str, object]]:
    """Parse all three fixed U.S. index quotes into normalized payloads."""

    text = _decode(raw)
    assignments = {name: value for name, value in _ASSIGNMENT_RE.findall(text)}
    missing = [name for name in _SOURCE_FIELDS if name not in assignments]
    if missing:
        raise ProviderParseError(
            "U.S. index response missing quote(s): " + ", ".join(missing)
        )

    parsed: dict[str, dict[str, object]] = {}
    for source_name, (item_key, display_name, value_i, change_i, percent_i) in (
        _SOURCE_FIELDS.items()
    ):
        fields = assignments[source_name].split("~")
        max_index = max(value_i, change_i, percent_i)
        if len(fields) <= max_index:
            raise ProviderParseError(
                f"U.S. index quote fields are incomplete: {display_name}"
            )
        value = _positive_number(fields[value_i], f"{display_name} value")
        change = _number(fields[change_i], f"{display_name} change")
        change_percent = _number(
            fields[percent_i], f"{display_name} change percent"
        )
        parsed[item_key] = {
            "key": item_key,
            "name": display_name,
            "value": value,
            "change": change,
            "change_percent": change_percent,
            "unit": "index points",
        }
    return parsed


class USIndexProvider:
    """Fetch the fixed, validated set of major U.S. indices."""

    group = US_INDEX_GROUP

    def __init__(self, http_client: HttpClient | None = None) -> None:
        self._http = http_client or HttpClient()
        self.items = tuple(
            NetworkItem(item_key, self.group) for item_key in US_INDEX_ITEM_KEYS
        )

    def fetch(self) -> ProviderResult:
        parsed = parse_us_indices(self._get_raw(US_INDEX_URL))
        return ProviderResult.partial(
            [ProviderItemResult.success(item.key, parsed[item.key]) for item in self.items]
        )

    def _get_raw(self, url: str) -> bytes | str:
        get = getattr(self._http, "get", None)
        if callable(get):
            response = get(url, headers={"Accept": "text/plain"})
            content = getattr(response, "content", None)
            if isinstance(content, (bytes, bytearray)):
                return bytes(content)
            text = getattr(response, "text", None)
            if isinstance(text, str):
                return text
        get_text = getattr(self._http, "get_text", None)
        if callable(get_text):
            return get_text(url, headers={"Accept": "text/plain"})
        raise TypeError("USIndex HTTP client must provide get or get_text")


def _decode(raw: bytes | str) -> str:
    if isinstance(raw, str):
        return raw
    if not isinstance(raw, bytes):
        raise ProviderParseError("U.S. index response must be bytes or text")
    for encoding in ("utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ProviderParseError("U.S. index response is neither UTF-8 nor GB18030")


def _number(value: object, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ProviderDataError(f"U.S. index {field} is not numeric") from error
    if not math.isfinite(result):
        raise ProviderDataError(f"U.S. index {field} is not finite")
    return result


def _positive_number(value: object, field: str) -> float:
    result = _number(value, field)
    if result <= 0:
        raise ProviderDataError(f"U.S. index {field} must be positive")
    return result
