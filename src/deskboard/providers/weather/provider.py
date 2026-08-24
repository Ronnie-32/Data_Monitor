"""China Weather provider using the Task 1 validated fixed source."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable
from typing import Any

from deskboard.models.weather import DEFAULT_WEATHER_CITIES, Weather, WeatherCity
from deskboard.providers.base import NetworkItem, ProviderItemResult, ProviderResult
from deskboard.providers.errors import ProviderDataError, ProviderParseError
from deskboard.providers.http_client import HttpClient

WEATHER_GROUP = "weather"
WEATHER_INDEX_URL = "http://d1.weather.com.cn/weather_index/{city_id}.html"
WEATHER_FORECAST_URL = "http://www.weather.com.cn/weather/{city_id}.shtml"


def parse_weather(
    raw: bytes | str,
    forecast_raw: bytes | str,
    *,
    city_key: str | None = None,
    city: WeatherCity | None = None,
) -> Weather:
    """Parse the validated live-index and formal-daily-page pair."""

    text = _decode(raw)
    current = _weather_object(text, "dataSK")
    high, low = _forecast_temperatures(forecast_raw)
    current_temperature = _number(current.get("temp"), "current temperature")
    condition = _required_field(current.get("weather"), "condition")
    wind_direction = _required_field(current.get("WD"), "wind direction")
    wind_speed = _required_field(current.get("WS"), "wind speed")
    if city is None:
        city = _resolve_city(current, city_key)
    observed_high = max(high, current_temperature)
    observed_low = min(low, current_temperature)
    return Weather(
        city=city.display_name,
        condition=condition,
        current_temperature=current_temperature,
        high=observed_high,
        low=observed_low,
        wind=f"{wind_direction} {wind_speed}",
    )


class WeatherProvider:
    """Fetch one normalized item for each globally configured city.

    The provider has one fixed source strategy and never accesses SQLite, UI,
    refresh state, or a fallback source.
    """

    group = WEATHER_GROUP

    def __init__(
        self,
        http_client: HttpClient | None = None,
        cities: Iterable[WeatherCity] | None = None,
    ) -> None:
        self._http = http_client or HttpClient()
        selected = tuple(DEFAULT_WEATHER_CITIES if cities is None else cities)
        if not selected:
            raise ValueError("WeatherProvider requires at least one city")
        if len({city.city_key for city in selected}) != len(selected):
            raise ValueError("WeatherProvider city keys must be unique")
        self._cities = selected
        self.items = tuple(NetworkItem(city.city_key, self.group) for city in selected)

    @property
    def cities(self) -> tuple[WeatherCity, ...]:
        return self._cities

    def fetch(self) -> ProviderResult:
        outcomes: list[ProviderItemResult] = []
        for city in self._cities:
            try:
                weather = self._fetch_city(city)
            except Exception as error:  # noqa: BLE001 - preserve per-city failure state
                outcomes.append(ProviderItemResult.failure(city.city_key, error))
            else:
                outcomes.append(
                    ProviderItemResult.success(city.city_key, weather.as_payload())
                )
        return ProviderResult.partial(outcomes)

    def _fetch_city(self, city: WeatherCity) -> Weather:
        headers = {
            "Referer": f"http://www.weather.com.cn/weather1d/{city.source_city_id}.shtml"
        }
        current_raw = self._get_raw(
            WEATHER_INDEX_URL.format(city_id=city.source_city_id), headers
        )
        forecast_raw = self._get_raw(
            WEATHER_FORECAST_URL.format(city_id=city.source_city_id), headers
        )
        return parse_weather(current_raw, forecast_raw, city=city)

    def _get_raw(self, url: str, headers: dict[str, str]) -> bytes | str:
        """Prefer response bytes so source charset detection stays in the parser."""

        get = getattr(self._http, "get", None)
        if callable(get):
            response = get(url, headers=headers)
            content = getattr(response, "content", None)
            if isinstance(content, (bytes, bytearray)):
                return bytes(content)
            text = getattr(response, "text", None)
            if isinstance(text, str):
                return text
        get_text = getattr(self._http, "get_text", None)
        if callable(get_text):
            return get_text(url, headers=headers)
        raise TypeError("Weather HTTP client must provide get or get_text")


def _decode(raw: bytes | str) -> str:
    if isinstance(raw, str):
        return raw
    if not isinstance(raw, bytes):
        raise ProviderParseError("Weather response must be bytes or text")
    for encoding in ("utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ProviderParseError("Weather response is neither UTF-8 nor GB18030")


def _weather_object(text: str, variable: str) -> dict[str, Any]:
    match = re.search(rf"var\s+{variable}\s*=\s*(\{{.*?\}})\s*;", text, re.S)
    if not match:
        raise ProviderParseError(f"Weather response missing {variable}")
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError as error:
        raise ProviderParseError(f"Weather {variable} JSON is invalid") from error
    if not isinstance(value, dict):
        raise ProviderParseError(f"Weather {variable} is not an object")
    return value


def _forecast_temperatures(raw: bytes | str) -> tuple[float, float]:
    text = _decode(raw)
    list_start = text.find('<ul class="t clearfix">')
    first_day_end = text.find("</li>", list_start)
    if list_start < 0 or first_day_end < 0:
        raise ProviderParseError("Weather forecast page lacks today's row")
    today = text[list_start:first_day_end]
    match = re.search(
        r'<p class="tem">\s*<span>([-+]?\d+(?:\.\d+)?)</span>\s*/\s*'
        r'<i>([-+]?\d+(?:\.\d+)?)℃</i>',
        today,
        re.S,
    )
    if not match:
        raise ProviderParseError("Weather forecast page lacks today's high/low")
    return _number(match.group(1), "forecast high"), _number(match.group(2), "forecast low")


def _number(value: object, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ProviderDataError(f"Weather {field} is not numeric") from error
    if not math.isfinite(result):
        raise ProviderDataError(f"Weather {field} is not finite")
    return result


def _required_field(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProviderDataError(f"Weather response lacks {field}")
    return value.strip()


def _resolve_city(current: dict[str, Any], city_key: str | None) -> WeatherCity:
    if city_key is not None:
        for city in DEFAULT_WEATHER_CITIES:
            if city.city_key == city_key:
                return city
    city_name = current.get("cityname") or current.get("namecn")
    source_city_id = current.get("city")
    if not isinstance(city_name, str) or not city_name.strip():
        raise ProviderDataError("Weather response lacks city")
    if not isinstance(source_city_id, str) or not source_city_id.strip():
        source_city_id = "unknown"
    return WeatherCity(
        city_key=city_key or str(source_city_id),
        display_name=city_name.strip(),
        source_city_id=str(source_city_id).strip(),
        display_order=0,
        is_primary=False,
    )
