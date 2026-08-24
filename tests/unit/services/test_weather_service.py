from __future__ import annotations

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.repositories.weather_repository import WeatherRepository
from deskboard.services.weather_service import WeatherService


def make_service(tmp_path) -> tuple[WeatherService, WeatherRepository]:
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    repository = WeatherRepository(connection)
    return WeatherService(repository), repository


def test_service_seeds_first_priority_mainland_cities_with_one_primary(tmp_path):
    service, _repository = make_service(tmp_path)

    cities = service.list_cities()

    assert [city.city_key for city in cities] == ["beijing", "shanghai"]
    assert [city.display_name for city in cities] == ["北京", "上海"]
    assert [city.city_key for city in cities if city.is_primary] == ["beijing"]
    assert [city.source_city_id for city in cities] == ["101010100", "101020100"]


def test_service_global_order_primary_update_delete_and_recovery(tmp_path):
    service, _repository = make_service(tmp_path)

    service.reorder_cities(["shanghai", "beijing"])
    service.set_primary_city("shanghai")
    service.add_city("guangzhou", "广州", "101280101")
    service.update_city("guangzhou", display_name="广州市")

    assert [city.city_key for city in service.list_cities()] == [
        "shanghai",
        "beijing",
        "guangzhou",
    ]
    assert service.get_primary_city().city_key == "shanghai"

    service.delete_city("shanghai")
    assert service.get_primary_city().city_key == "beijing"

    service.delete_city("beijing")
    service.delete_city("guangzhou")
    assert service.list_cities() == []

    restored = service.add_city("nanjing", "南京", "101190101")
    assert restored.is_primary is True
    assert service.get_primary_city() == restored


def test_service_rejects_invalid_or_incomplete_global_configuration(tmp_path):
    service, _repository = make_service(tmp_path)

    try:
        service.reorder_cities(["beijing"])
    except ValueError as error:
        assert "exactly" in str(error)
    else:
        raise AssertionError("incomplete reorder should fail")

    try:
        service.set_primary_city("missing")
    except LookupError as error:
        assert "missing" in str(error)
    else:
        raise AssertionError("unknown primary city should fail")


def test_city_configuration_is_not_profile_owned(tmp_path):
    service, repository = make_service(tmp_path)
    service.add_city("guangzhou", "广州", "101280101")

    reloaded = WeatherService(WeatherRepository(repository.connection))

    assert [city.city_key for city in reloaded.list_cities()] == [
        "beijing",
        "shanghai",
        "guangzhou",
    ]
