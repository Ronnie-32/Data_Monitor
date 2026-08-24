"""Validated mainland-China Weather provider."""

from deskboard.providers.weather.provider import (
    WEATHER_FORECAST_URL,
    WEATHER_INDEX_URL,
    WeatherProvider,
    parse_weather,
)

__all__ = [
    "WEATHER_FORECAST_URL",
    "WEATHER_INDEX_URL",
    "WeatherProvider",
    "parse_weather",
]
