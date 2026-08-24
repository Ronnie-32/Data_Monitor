"""China A-share index provider using the validated Tencent quote endpoint."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping

from deskboard.providers.base import NetworkItem, ProviderItemResult, ProviderResult
from deskboard.providers.errors import ProviderDataError, ProviderParseError
from deskboard.providers.http_client import HttpClient

CHINA_INDEX_GROUP = "indices"
CHINA_INDEX_URL = (
    "https://qt.gtimg.cn/q=s_sh000001,s_sz399001,s_sz399006,sh000300"
)
CHINA_INDEX_ITEM_KEYS = (
    "index.sse",
    "index.szse",
    "index.chinext",
    "index.csi300",
)

# Tencent's first three A-share records use current/change/change-percent at
# positions 3/4/5. The CSI 300 record keeps its change fields at 31/32.
_SOURCE_FIELDS: Mapping[str, tuple[str, str, int, int, int]] = {
    "v_s_sh000001": ("index.sse", "上证指数", 3, 4, 5),
    "v_s_sz399001": ("index.szse", "深证成指", 3, 4, 5),
    "v_s_sz399006": ("index.chinext", "创业板指", 3, 4, 5),
    "v_sh000300": ("index.csi300", "沪深300", 3, 31, 32),
}
_ASSIGNMENT_RE = re.compile(r'(v_[A-Za-z0-9_.]+)\s*=\s*"([^"]*)"\s*;')


def parse_china_indices(raw: bytes | str) -> dict[str, dict[str, object]]:
    """Parse all four fixed A-share quotes into DeskBoard-owned payloads."""

    text = _decode(raw)
    assignments = {name: value for name, value in _ASSIGNMENT_RE.findall(text)}
    missing = [name for name in _SOURCE_FIELDS if name not in assignments]
    if missing:
        raise ProviderParseError(
            "China index response missing A-share quote(s): "
            + ", ".join(missing)
        )

    parsed: dict[str, dict[str, object]] = {}
    for source_name, (item_key, display_name, value_i, change_i, percent_i) in (
        _SOURCE_FIELDS.items()
    ):
        fields = assignments[source_name].split("~")
        max_index = max(value_i, change_i, percent_i)
        if len(fields) <= max_index:
            raise ProviderParseError(
                f"China index quote fields are incomplete: {display_name}"
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


class ChinaIndexProvider:
    """Fetch the fixed, validated set of major A-share indices."""

    group = CHINA_INDEX_GROUP

    def __init__(self, http_client: HttpClient | None = None) -> None:
        self._http = http_client or HttpClient()
        self.items = tuple(
            NetworkItem(item_key, self.group) for item_key in CHINA_INDEX_ITEM_KEYS
        )

    def fetch(self) -> ProviderResult:
        parsed = parse_china_indices(self._get_raw(CHINA_INDEX_URL))
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
        raise TypeError("ChinaIndex HTTP client must provide get or get_text")


def _decode(raw: bytes | str) -> str:
    if isinstance(raw, str):
        return raw
    if not isinstance(raw, bytes):
        raise ProviderParseError("China index response must be bytes or text")
    for encoding in ("utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ProviderParseError("China index response is neither UTF-8 nor GB18030")


def _number(value: object, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ProviderDataError(f"China index {field} is not numeric") from error
    if not math.isfinite(result):
        raise ProviderDataError(f"China index {field} is not finite")
    return result


def _positive_number(value: object, field: str) -> float:
    result = _number(value, field)
    if result <= 0:
        raise ProviderDataError(f"China index {field} must be positive")
    return result
