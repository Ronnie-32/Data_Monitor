"""Gold provider using the validated Shanghai Gold Exchange daily page."""

from __future__ import annotations

import html
import math
import re
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

from deskboard.providers.base import NetworkItem, ProviderResult
from deskboard.providers.errors import ProviderDataError, ProviderError, ProviderParseError
from deskboard.providers.http_client import HttpClient

GOLD_GROUP = "gold"
GOLD_ITEM_KEY = "gold.au9999"
GOLD_PROVIDER_KEY = "gold_au9999"
GOLD_DAILY_URL = "https://www.sge.com.cn/sjzx/quotation_daily_new"
SGE_DAILY_URL = GOLD_DAILY_URL
GOLD_LOOKBACK_DAYS = 10


def parse_gold(raw: bytes | str) -> dict[str, object]:
    """Parse the validated SGE table into one Au99.99 daily quote.

    The parser deliberately selects the ``Au99.99`` contract row rather than
    relying on the row position, which is not a stable source contract.
    """

    text = _decode(raw)
    for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", text, re.IGNORECASE | re.DOTALL):
        cells = [
            _cell_text(cell)
            for cell in re.findall(
                r"<td\b[^>]*>(.*?)</td>", row, re.IGNORECASE | re.DOTALL
            )
        ]
        contract_indexes = [
            index
            for index, value in enumerate(cells)
            if value.replace(" ", "") == "Au99.99"
        ]
        if not contract_indexes:
            continue
        contract_index = contract_indexes[0]
        if contract_index < 1 or len(cells) <= contract_index + 6:
            continue
        trade_date = _required_text(cells[contract_index - 1], "Au99.99 date")
        close = _positive_number(
            cells[contract_index + 4].replace(",", ""),
            field="Au99.99 close",
        )
        change = _number(
            cells[contract_index + 5].replace(",", ""),
            field="Au99.99 change",
        )
        change_percent = _number(
            cells[contract_index + 6].rstrip("%").replace(",", ""),
            field="Au99.99 change percent",
        )
        return {
            "key": GOLD_PROVIDER_KEY,
            "date": trade_date,
            "name": "Au99.99",
            "value": close,
            "change": change,
            "change_percent": change_percent,
            "unit": "CNY/g",
            "price_field": "daily close",
        }
    raise ProviderParseError("SGE response lacks a usable Au99.99 daily row")


class GoldProvider:
    """Fetch one normalized Gold item from the selected SGE source."""

    group = GOLD_GROUP

    def __init__(
        self,
        http_client: HttpClient | None = None,
        *,
        as_of: date | None = None,
        lookback_days: int = GOLD_LOOKBACK_DAYS,
    ) -> None:
        self._http = http_client or HttpClient()
        self._as_of = _validate_date(as_of or date.today())
        if isinstance(lookback_days, bool) or not isinstance(lookback_days, int):
            raise TypeError("Gold lookback_days must be an integer")
        if lookback_days < 1:
            raise ValueError("Gold lookback_days must be positive")
        self._lookback_days = lookback_days
        self.items = (NetworkItem(GOLD_ITEM_KEY, self.group),)

    def fetch(self) -> ProviderResult:
        """Fetch the latest usable same-source daily row.

        The bounded date lookback handles weekends/holidays without adding a
        second source or a refresh retry chain.
        """

        last_error: BaseException | None = None
        for offset in range(self._lookback_days):
            target = self._as_of - timedelta(days=offset)
            url = _daily_url(target)
            try:
                parsed = parse_gold(self._get_raw(url))
            except (ProviderError, ValueError) as error:
                last_error = error
                continue
            payload = {
                "key": GOLD_ITEM_KEY,
                "date": parsed["date"],
                "name": parsed["name"],
                "value": parsed["value"],
                "change": parsed["change"],
                "change_percent": parsed["change_percent"],
                "unit": parsed["unit"],
                "price_field": parsed["price_field"],
            }
            return ProviderResult.success(GOLD_ITEM_KEY, payload)

        detail = str(last_error) if last_error is not None else "no usable response"
        raise ProviderDataError(
            f"SGE Au99.99 unavailable in {self._lookback_days}-day lookback: {detail}"
        )

    def _get_raw(self, url: str) -> bytes | str:
        get = getattr(self._http, "get", None)
        if callable(get):
            response = get(url, headers={"Accept": "text/html"})
            content = getattr(response, "content", None)
            if isinstance(content, (bytes, bytearray)):
                return bytes(content)
            text = getattr(response, "text", None)
            if isinstance(text, str):
                return text
        get_text = getattr(self._http, "get_text", None)
        if callable(get_text):
            return get_text(url, headers={"Accept": "text/html"})
        raise TypeError("Gold HTTP client must provide get or get_text")


def _daily_url(target: date) -> str:
    query = urlencode(
        {"start_date": target.isoformat(), "end_date": target.isoformat()}
    )
    return f"{GOLD_DAILY_URL}?{query}"


def _decode(raw: bytes | str) -> str:
    if isinstance(raw, str):
        return raw
    if not isinstance(raw, bytes):
        raise ProviderParseError("Gold response must be bytes or text")
    for encoding in ("utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ProviderParseError("Gold response is neither UTF-8 nor GB18030")


def _cell_text(cell: str) -> str:
    without_tags = re.sub(r"<[^>]+>", "", cell)
    return " ".join(html.unescape(without_tags).split())


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProviderDataError(f"{field} is missing")
    return value.strip()


def _number(value: object, *, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ProviderDataError(f"{field} is not numeric") from error
    if not math.isfinite(result):
        raise ProviderDataError(f"{field} is not finite")
    return result


def _positive_number(value: object, *, field: str) -> float:
    result = _number(value, field=field)
    if result <= 0:
        raise ProviderDataError(f"{field} must be positive")
    return result


def _validate_date(value: object) -> date:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise TypeError("Gold as_of must be a date")
    return value
