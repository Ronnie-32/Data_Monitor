from __future__ import annotations

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.repositories.weather_repository import WeatherRepository


def make_repository(tmp_path) -> tuple[WeatherRepository, object]:
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    return WeatherRepository(connection), connection


def add_city(repository: WeatherRepository, key: str, order: int, primary: bool = False):
    return repository.create_city(
        city_key=key,
        display_name=key.title(),
        source_city_id=f"source-{key}",
        display_order=order,
        is_primary=primary,
    )


def test_weather_repository_owns_city_configuration_only(tmp_path):
    repository, connection = make_repository(tmp_path)

    beijing = add_city(repository, "beijing", 0, primary=True)
    add_city(repository, "shanghai", 1)

    assert repository.list_cities() == [beijing, repository.get_city("shanghai")]
    assert repository.get_city("beijing") == beijing
    assert repository.get_city("missing") is None
    assert repository.connection is connection
    assert not hasattr(repository, "save_weather")
    assert connection.execute("SELECT COUNT(*) FROM network_cache").fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM network_state").fetchone()[0] == 0


def test_repository_preserves_order_and_exactly_one_primary_when_cities_exist(tmp_path):
    repository, _connection = make_repository(tmp_path)
    add_city(repository, "beijing", 0, primary=True)
    add_city(repository, "shanghai", 1)
    add_city(repository, "guangzhou", 2)

    repository.set_primary("shanghai")
    repository.reorder_cities(("guangzhou", "shanghai", "beijing"))
    assert [city.city_key for city in repository.list_cities()] == [
        "guangzhou",
        "shanghai",
        "beijing",
    ]
    assert [city.city_key for city in repository.list_cities() if city.is_primary] == [
        "shanghai"
    ]

    repository.delete_city("shanghai")
    remaining = repository.list_cities()
    assert [city.city_key for city in remaining] == ["guangzhou", "beijing"]
    assert [city.city_key for city in remaining if city.is_primary] == ["guangzhou"]


def test_repository_updates_city_metadata_without_payload_columns(tmp_path):
    repository, connection = make_repository(tmp_path)
    add_city(repository, "beijing", 0, primary=True)

    updated = repository.update_city(
        "beijing",
        display_name="北京市",
        source_city_id="101010100",
    )

    assert updated.display_name == "北京市"
    assert updated.source_city_id == "101010100"
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(weather_cities)")
    }
    assert columns == {
        "city_key",
        "display_name",
        "source_city_id",
        "display_order",
        "is_primary",
    }
