from deskboard.providers.weather.location_catalog import (
    WeatherLocation,
    WeatherLocationCatalog,
)


def test_location_catalog_matches_chinese_name_pinyin_and_trimmed_aliases():
    catalog = WeatherLocationCatalog(
        (
            WeatherLocation(
                source_city_id="101190401",
                display_name="苏州",
                region_name="江苏",
                pinyin="suzhou",
            ),
        )
    )

    assert catalog.search("苏州")[0].source_city_id == "101190401"
    assert catalog.search("suzhou")[0].display_name == "苏州"
    assert catalog.search(" 苏州市 ")[0].display_name == "苏州"
    assert catalog.search("江苏苏州")[0].source_city_id == "101190401"


def test_location_catalog_preserves_ambiguous_names_with_region_labels():
    catalog = WeatherLocationCatalog(
        (
            WeatherLocation("101010300", "朝阳", "北京", "chaoyang"),
            WeatherLocation("101071201", "朝阳", "辽宁", "chaoyang"),
        )
    )

    results = catalog.search("朝阳")

    assert [item.source_city_id for item in results] == ["101010300", "101071201"]
    assert [item.display_label for item in results] == ["朝阳 · 北京", "朝阳 · 辽宁"]


def test_bundled_weather_location_catalog_covers_districts_and_common_pinyin():
    from deskboard.providers.weather.location_catalog import WEATHER_LOCATION_CATALOG

    assert len(WEATHER_LOCATION_CATALOG) >= 2400
    assert WEATHER_LOCATION_CATALOG.search("suzhou")[0].source_city_id == "101190401"
    assert WEATHER_LOCATION_CATALOG.search("北京")[0].source_city_id == "101010100"
