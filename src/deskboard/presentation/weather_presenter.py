"""Convert cached normalized Weather values into Dashboard-owned ViewModels."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Protocol, TypedDict

from deskboard.models.weather import Weather, WeatherCity

WEATHER_DISPLAY_SINGLE_CITY = "single-city detail"
WEATHER_DISPLAY_MULTI_CITY = "multi-city summary"


class WeatherCityViewModel(TypedDict):
    city: str
    condition: str
    currentTemperature: float
    high: float
    low: float
    wind: str


class WeatherViewModel(TypedDict):
    displayMode: str
    cities: list[WeatherCityViewModel]


class WeatherServiceLike(Protocol):
    def list_cities(self) -> list[WeatherCity]: ...

    def get_primary_city(self) -> WeatherCity | None: ...


class WeatherCacheReader(Protocol):
    def read_cached_payload(self, cache_key: str) -> object | None: ...


class WeatherPresenter:
    """Read global city configuration and Task 15 cache through service APIs."""

    def __init__(
        self,
        weather_service: WeatherServiceLike,
        cache_reader: WeatherCacheReader | None = None,
        *,
        refresh_service: WeatherCacheReader | None = None,
    ) -> None:
        if cache_reader is not None and refresh_service is not None:
            raise TypeError("provide cache_reader or refresh_service, not both")
        self._weather_service = weather_service
        self._cache_reader = cache_reader or refresh_service

    def present(
        self,
        *,
        display_mode: str | None = None,
        max_cities: int | None = None,
    ) -> WeatherViewModel:
        cities = tuple(self._weather_service.list_cities())
        primary = self._weather_service.get_primary_city()
        payloads: dict[str, Weather] = {}
        for city in cities:
            raw = self._read_cached_payload(city.city_key)
            if raw is None:
                continue
            try:
                payloads[city.city_key] = _as_weather(raw)
            except (TypeError, ValueError):
                # A corrupt cache must not make the Dashboard bridge fail.
                continue
        return present_weather(
            payloads,
            cities=cities,
            primary_city_key=primary.city_key if primary is not None else None,
            display_mode=display_mode,
            max_cities=max_cities,
        )

    present_weather = present

    def _read_cached_payload(self, cache_key: str) -> object | None:
        if self._cache_reader is None:
            return None
        reader = getattr(self._cache_reader, "read_cached_payload", None)
        if not callable(reader):
            raise TypeError("Weather cache reader must expose read_cached_payload")
        return reader(cache_key)


def present_weather(
    weather_by_city: Mapping[str, Weather | Mapping[str, object]],
    *,
    cities: Iterable[WeatherCity] = (),
    primary_city_key: str | None = None,
    display_mode: str | None = None,
    max_cities: int | None = None,
) -> WeatherViewModel:
    """Present Weather in global city order without upstream/provider fields."""

    mode = normalize_weather_display_mode(display_mode)
    ordered_cities = tuple(cities)
    normalized: dict[str, Weather] = {
        str(key): _as_weather(value) for key, value in weather_by_city.items()
    }

    if ordered_cities:
        ordered_keys = [city.city_key for city in ordered_cities]
    else:
        ordered_keys = list(normalized)

    if mode == WEATHER_DISPLAY_SINGLE_CITY:
        selected_key = primary_city_key or (ordered_keys[0] if ordered_keys else None)
        selected_keys = [] if selected_key is None else [selected_key]
    else:
        selected_keys = ordered_keys

    selected = [normalized[key] for key in selected_keys if key in normalized]
    if max_cities is not None:
        _validate_max_cities(max_cities)
        selected = selected[:max_cities]

    return {
        "displayMode": mode,
        "cities": [_present_weather_value(value) for value in selected],
    }


present_weather_state = present_weather


def normalize_weather_display_mode(value: str | None) -> str:
    if value is None:
        return WEATHER_DISPLAY_SINGLE_CITY
    if not isinstance(value, str):
        raise TypeError("Weather display mode must be a string")
    aliases = {
        "compact": WEATHER_DISPLAY_SINGLE_CITY,
        "primary": WEATHER_DISPLAY_SINGLE_CITY,
        "single": WEATHER_DISPLAY_SINGLE_CITY,
        "single-city": WEATHER_DISPLAY_SINGLE_CITY,
        "single_city": WEATHER_DISPLAY_SINGLE_CITY,
        "single_city_detail": WEATHER_DISPLAY_SINGLE_CITY,
        WEATHER_DISPLAY_SINGLE_CITY: WEATHER_DISPLAY_SINGLE_CITY,
        "multi": WEATHER_DISPLAY_MULTI_CITY,
        "multi-city": WEATHER_DISPLAY_MULTI_CITY,
        "multi_city": WEATHER_DISPLAY_MULTI_CITY,
        "multi_city_summary": WEATHER_DISPLAY_MULTI_CITY,
        WEATHER_DISPLAY_MULTI_CITY: WEATHER_DISPLAY_MULTI_CITY,
    }
    try:
        return aliases[value.strip().lower()]
    except KeyError as error:
        raise ValueError(f"Unsupported Weather display mode: {value}") from error


def _as_weather(value: object) -> Weather:
    if isinstance(value, Weather):
        return value
    if isinstance(value, Mapping):
        return Weather.from_payload(value)
    raise TypeError("Weather cache payload must be a Weather value or mapping")


def _present_weather_value(value: Weather) -> WeatherCityViewModel:
    return {
        "city": value.city,
        "condition": value.condition,
        "currentTemperature": float(value.current_temperature),
        "high": float(value.high),
        "low": float(value.low),
        "wind": value.wind,
    }


def _validate_max_cities(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("Weather max_cities must be an integer")
    if value < 0:
        raise ValueError("Weather max_cities must not be negative")
