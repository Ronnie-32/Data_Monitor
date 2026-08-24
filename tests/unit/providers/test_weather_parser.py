from __future__ import annotations

from pathlib import Path

import pytest

from deskboard.models.weather import Weather
from deskboard.providers.errors import ProviderDataError, ProviderParseError
from deskboard.providers.weather.provider import WeatherProvider, parse_weather

FIXTURES = Path(__file__).parents[2] / "fixtures" / "providers"


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parse_validated_beijing_fixture_into_required_normalized_fields():
    weather = parse_weather(
        fixture("weather_com_cn_beijing.html"),
        fixture("weather_com_cn_beijing_forecast.html"),
        city_key="beijing",
    )

    assert isinstance(weather, Weather)
    assert weather.city == "北京"
    assert weather.condition == "多云"
    assert weather.current_temperature == pytest.approx(31.9)
    assert weather.high == pytest.approx(31.9)
    assert weather.low == pytest.approx(22)
    assert weather.wind == "南风 2级"
    assert weather.as_payload() == {
        "city": "北京",
        "condition": "多云",
        "current_temperature": 31.9,
        "high": 31.9,
        "low": 22.0,
        "wind": "南风 2级",
    }


def test_parse_validated_shanghai_fixture_and_do_not_require_optional_fields():
    weather = parse_weather(
        fixture("weather_com_cn_shanghai.html"),
        fixture("weather_com_cn_shanghai_forecast.html"),
        city_key="shanghai",
    )

    assert weather.city == "上海"
    assert weather.high >= weather.current_temperature >= weather.low
    assert set(weather.as_payload()) == {
        "city",
        "condition",
        "current_temperature",
        "high",
        "low",
        "wind",
    }


def test_parser_reports_bounded_parse_and_data_errors():
    forecast = fixture("weather_com_cn_beijing_forecast.html")

    with pytest.raises(ProviderParseError, match="dataSK"):
        parse_weather(b"var not_weather = {};", forecast, city_key="beijing")

    with pytest.raises(ProviderDataError, match="condition"):
        parse_weather(
            'var dataSK = {"temp":"20","WD":"北风","WS":"2级"};'.encode(
                "utf-8"
            ),
            forecast,
            city_key="beijing",
        )


class FakeWeatherHttpClient:
    def __init__(self):
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get_text(self, url: str, **kwargs: object) -> str:
        self.calls.append((url, kwargs))
        if "101010100" in url and "weather_index" in url:
            return fixture("weather_com_cn_beijing.html").decode("utf-8")
        if "101010100" in url:
            return fixture("weather_com_cn_beijing_forecast.html").decode("utf-8")
        if "101020100" in url and "weather_index" in url:
            return fixture("weather_com_cn_shanghai.html").decode("utf-8")
        if "101020100" in url:
            return fixture("weather_com_cn_shanghai_forecast.html").decode("utf-8")
        raise AssertionError(f"unexpected URL: {url}")


def test_provider_fetches_only_the_selected_fixed_source_and_returns_no_persistence_side_effect():
    client = FakeWeatherHttpClient()
    provider = WeatherProvider(http_client=client)

    result = provider.fetch()

    assert provider.group == "weather"
    assert [item.key for item in result.items] == ["beijing", "shanghai"]
    assert all(item.ok for item in result.items)
    assert result.items[0].payload["city"] == "北京"
    assert result.items[1].payload["city"] == "上海"
    assert len(client.calls) == 4
    assert all("Referer" in kwargs["headers"] for _url, kwargs in client.calls)
    assert all("weather.com.cn" in url for url, _kwargs in client.calls)
