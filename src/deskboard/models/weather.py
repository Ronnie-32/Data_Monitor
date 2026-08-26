"""Normalized Weather values and global weather-city configuration values."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Weather:
    """The small normalized payload shared by providers and later presenters."""

    city: str
    condition: str
    current_temperature: float
    high: float
    low: float
    wind: str

    def __post_init__(self) -> None:
        for field_name in ("city", "condition", "wind"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Weather {field_name} must not be empty")
        for field_name in ("current_temperature", "high", "low"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"Weather {field_name} must be numeric")
            if not math.isfinite(float(value)):
                raise ValueError(f"Weather {field_name} must be finite")
        if self.low > self.current_temperature or self.current_temperature > self.high:
            raise ValueError("Weather temperatures must satisfy low <= current <= high")

    def as_payload(self) -> dict[str, object]:
        """Return a JSON-safe payload with only V1-required fields."""

        return {
            "city": self.city,
            "condition": self.condition,
            "current_temperature": float(self.current_temperature),
            "high": float(self.high),
            "low": float(self.low),
            "wind": self.wind,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "Weather":
        if not isinstance(payload, Mapping):
            raise TypeError("Weather payload must be a mapping")
        required = ("city", "condition", "current_temperature", "high", "low", "wind")
        missing = [field for field in required if field not in payload]
        if missing:
            raise ValueError("Weather payload missing: " + ", ".join(missing))
        return cls(
            city=str(payload["city"]),
            condition=str(payload["condition"]),
            current_temperature=float(payload["current_temperature"]),
            high=float(payload["high"]),
            low=float(payload["low"]),
            wind=str(payload["wind"]),
        )

    def __getitem__(self, field: str) -> object:
        """Offer read-only mapping-style access for cache/presenter adapters."""

        return self.as_payload()[field]


@dataclass(frozen=True, slots=True)
class WeatherCity:
    """One globally ordered city used by the Weather provider."""

    city_key: str
    display_name: str
    source_city_id: str
    display_order: int
    is_primary: bool = False

    def __post_init__(self) -> None:
        for field_name in ("city_key", "display_name", "source_city_id"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Weather city {field_name} must not be empty")
        if any(char.isspace() or char in "/\\" for char in self.city_key):
            raise ValueError("Weather city key must not contain whitespace or path separators")
        if isinstance(self.display_order, bool) or not isinstance(self.display_order, int):
            raise TypeError("Weather city display_order must be an integer")
        if self.display_order < 0:
            raise ValueError("Weather city display_order must not be negative")
        if type(self.is_primary) is not bool:
            raise TypeError("Weather city is_primary must be a bool")


BEIJING = WeatherCity("beijing", "北京", "101010100", 0, True)
SHANGHAI = WeatherCity("shanghai", "上海", "101020100", 1, False)
DEFAULT_WEATHER_CITIES = (BEIJING, SHANGHAI)

WEATHER_SOURCE_CITY_ID_ALIASES = {
    "suzhou": "101190401",
    "苏州": "101190401",
}


def resolve_weather_source_city_id(source_city_id: str) -> str:
    """Resolve a friendly city alias to the fixed weather.com.cn source ID."""

    value = source_city_id.strip()
    return WEATHER_SOURCE_CITY_ID_ALIASES.get(value.casefold(), value)
