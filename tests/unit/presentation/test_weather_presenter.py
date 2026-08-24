from __future__ import annotations

from deskboard.models.weather import BEIJING, SHANGHAI, Weather
from deskboard.presentation.weather_presenter import (
    WEATHER_DISPLAY_MULTI_CITY,
    WEATHER_DISPLAY_SINGLE_CITY,
    WeatherPresenter,
)


class FakeWeatherService:
    def __init__(self) -> None:
        self.cities = [BEIJING, SHANGHAI]

    def list_cities(self):
        return list(self.cities)

    def get_primary_city(self):
        return self.cities[0]


class FakeCache:
    def __init__(self) -> None:
        self.payloads = {
            "beijing": Weather("北京", "晴", 26, 31, 22, "北风 3级").as_payload(),
            "shanghai": Weather("上海", "多云", 28, 33, 24, "东风 2级").as_payload(),
        }

    def read_cached_payload(self, cache_key: str):
        return self.payloads.get(cache_key)


def test_compact_weather_prioritizes_primary_city_and_exposes_only_approved_fields():
    view_model = WeatherPresenter(FakeWeatherService(), FakeCache()).present()

    assert view_model == {
        "displayMode": WEATHER_DISPLAY_SINGLE_CITY,
        "cities": [
            {
                "city": "北京",
                "condition": "晴",
                "currentTemperature": 26.0,
                "high": 31.0,
                "low": 22.0,
                "wind": "北风 3级",
            }
        ],
    }


def test_expanded_single_city_detail_still_uses_primary_city():
    view_model = WeatherPresenter(FakeWeatherService(), FakeCache()).present(
        display_mode=WEATHER_DISPLAY_SINGLE_CITY,
    )

    assert [city["city"] for city in view_model["cities"]] == ["北京"]


def test_expanded_multi_city_follows_global_order_and_truncates_capacity():
    view_model = WeatherPresenter(FakeWeatherService(), FakeCache()).present(
        display_mode=WEATHER_DISPLAY_MULTI_CITY,
        max_cities=1,
    )

    assert view_model["displayMode"] == WEATHER_DISPLAY_MULTI_CITY
    assert [city["city"] for city in view_model["cities"]] == ["北京"]

    full_view_model = WeatherPresenter(FakeWeatherService(), FakeCache()).present(
        display_mode=WEATHER_DISPLAY_MULTI_CITY,
    )
    assert [city["city"] for city in full_view_model["cities"]] == ["北京", "上海"]
