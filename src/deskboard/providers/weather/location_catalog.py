"""Offline searchable mainland-China weather location catalog."""

from __future__ import annotations

import base64
import re
import zlib
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from deskboard.providers.weather.location_catalog_data import (
    CATALOG_DATA_B64,
    CATALOG_SNAPSHOT_DATE,
    CATALOG_SOURCE,
)

_LOCATION_SUFFIXES = (
    "自治州",
    "地区",
    "新区",
    "市",
    "县",
    "区",
    "旗",
)
_NON_ALPHANUMERIC = re.compile(r"[^0-9a-zA-Z\u3400-\u9fff\u3040-\u30ff]+")


@dataclass(frozen=True, slots=True)
class WeatherLocation:
    """One searchable weather.com.cn location."""

    source_city_id: str
    display_name: str
    region_name: str
    pinyin: str = ""
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("source_city_id", "display_name", "region_name"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Weather location {field_name} must not be empty")
        if not isinstance(self.pinyin, str):
            raise TypeError("Weather location pinyin must be a string")
        if any(not isinstance(alias, str) or not alias.strip() for alias in self.aliases):
            raise TypeError("Weather location aliases must be non-empty strings")

    @property
    def city_key(self) -> str:
        """Return a stable configuration key independent of the display language."""

        return f"weather_{self.source_city_id.strip()}"

    @property
    def display_label(self) -> str:
        """Include the region so same-named locations remain distinguishable."""

        return f"{self.display_name} · {self.region_name}"


class WeatherLocationCatalog:
    """Immutable-in-use collection used by the native Weather Settings page."""

    def __init__(self, locations: Iterable[WeatherLocation] = ()) -> None:
        entries = tuple(locations)
        if any(not isinstance(location, WeatherLocation) for location in entries):
            raise TypeError("WeatherLocationCatalog entries must be WeatherLocation values")
        source_ids = [location.source_city_id for location in entries]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("WeatherLocationCatalog source city IDs must be unique")
        self._locations = entries
        self._by_source_id = {location.source_city_id: location for location in entries}

    @property
    def locations(self) -> tuple[WeatherLocation, ...]:
        return self._locations

    def get(self, source_city_id: str) -> WeatherLocation | None:
        if not isinstance(source_city_id, str):
            raise TypeError("Weather location source city ID must be a string")
        return self._by_source_id.get(source_city_id.strip())

    def search(self, query: str, *, limit: int = 50) -> tuple[WeatherLocation, ...]:
        if not isinstance(query, str):
            raise TypeError("Weather location search query must be a string")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("Weather location search limit must be a positive integer")
        query_forms = _query_forms(query)
        if not query_forms:
            return ()

        ranked: list[tuple[int, int, WeatherLocation]] = []
        for index, location in enumerate(self._locations):
            rank = _match_rank(location, query_forms)
            if rank is not None:
                ranked.append((rank, index, location))
        ranked.sort(key=lambda item: (item[0], item[1]))
        return tuple(item[2] for item in ranked[:limit])

    def __iter__(self) -> Iterator[WeatherLocation]:
        return iter(self._locations)

    def __len__(self) -> int:
        return len(self._locations)


def _match_rank(location: WeatherLocation, query_forms: tuple[str, ...]) -> int | None:
    values = [location.source_city_id, location.display_name, location.region_name]
    values.extend(location.aliases)
    if location.pinyin:
        values.append(location.pinyin)
    values.extend(
        (
            f"{location.region_name}{location.display_name}",
            f"{location.region_name}{_strip_location_suffix(location.display_name)}",
        )
    )
    normalized_values = []
    for value in values:
        normalized = _normalize(value)
        if normalized:
            normalized_values.extend((normalized, _strip_location_suffix(normalized)))

    best: int | None = None
    for query in query_forms:
        for value in normalized_values:
            if value == query:
                rank = 0
            elif value.startswith(query):
                rank = 1
            elif query in value:
                rank = 2
            else:
                continue
            best = rank if best is None else min(best, rank)
    return best


def _query_forms(query: str) -> tuple[str, ...]:
    normalized = _normalize(query)
    if not normalized:
        return ()
    short = _strip_location_suffix(normalized)
    return (normalized,) if short == normalized else (normalized, short)


def _normalize(value: str) -> str:
    return _NON_ALPHANUMERIC.sub("", value.strip().casefold())


def _strip_location_suffix(value: str) -> str:
    for suffix in _LOCATION_SUFFIXES:
        if value.endswith(suffix) and len(value) > len(suffix):
            return value[: -len(suffix)]
    return value


def _load_locations() -> tuple[WeatherLocation, ...]:
    raw = zlib.decompress(base64.b64decode(CATALOG_DATA_B64)).decode("utf-8")
    locations: list[WeatherLocation] = []
    for line in raw.splitlines():
        source_city_id, display_name, region_name, pinyin = line.split("\t")
        locations.append(
            WeatherLocation(
                source_city_id=source_city_id,
                display_name=display_name,
                region_name=region_name,
                pinyin=pinyin,
            )
        )
    return tuple(locations)


WEATHER_LOCATION_CATALOG = WeatherLocationCatalog(_load_locations())

__all__ = [
    "CATALOG_SNAPSHOT_DATE",
    "CATALOG_SOURCE",
    "WEATHER_LOCATION_CATALOG",
    "WeatherLocation",
    "WeatherLocationCatalog",
]
