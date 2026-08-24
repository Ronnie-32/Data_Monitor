"""Business rules for the global Weather city list."""

from __future__ import annotations

from collections.abc import Iterable

from deskboard.models.weather import DEFAULT_WEATHER_CITIES, WeatherCity
from deskboard.repositories.weather_repository import WeatherRepository


class WeatherService:
    """Keep city order and the primary-city invariant outside persistence/UI."""

    def __init__(self, repository: WeatherRepository) -> None:
        self._repository = repository
        self._ensure_initial_configuration()

    @property
    def repository(self) -> WeatherRepository:
        return self._repository

    @staticmethod
    def default_cities() -> tuple[WeatherCity, ...]:
        return DEFAULT_WEATHER_CITIES

    def list_cities(self) -> list[WeatherCity]:
        return self._repository.list_cities()

    def get_city(self, city_key: str) -> WeatherCity | None:
        return self._repository.get_city(city_key)

    def require_city(self, city_key: str) -> WeatherCity:
        return self._repository.require_city(city_key)

    def get_primary_city(self) -> WeatherCity | None:
        return self._repository.get_primary()

    def add_city(
        self,
        city_key: str,
        display_name: str,
        source_city_id: str,
        *,
        display_order: int | None = None,
        is_primary: bool = False,
    ) -> WeatherCity:
        cities = self.list_cities()
        if display_order is None:
            display_order = (
                max((city.display_order for city in cities), default=-1) + 1
            )
        if not cities:
            is_primary = True
        return self._repository.create_city(
            city_key=city_key,
            display_name=display_name,
            source_city_id=source_city_id,
            display_order=display_order,
            is_primary=is_primary,
        )

    create_city = add_city

    def update_city(
        self,
        city_key: str,
        *,
        display_name: str | None = None,
        source_city_id: str | None = None,
        display_order: int | None = None,
    ) -> WeatherCity:
        return self._repository.update_city(
            city_key,
            display_name=display_name,
            source_city_id=source_city_id,
            display_order=display_order,
        )

    def set_primary_city(self, city_key: str) -> WeatherCity:
        return self._repository.set_primary(city_key)

    set_primary = set_primary_city

    def reorder_cities(self, ordered_keys: Iterable[str]) -> list[WeatherCity]:
        return self._repository.reorder_cities(tuple(ordered_keys))

    reorder = reorder_cities

    def delete_city(self, city_key: str) -> None:
        self._repository.delete_city(city_key)

    remove_city = delete_city

    def _ensure_initial_configuration(self) -> None:
        cities = self.list_cities()
        if not cities:
            for city in DEFAULT_WEATHER_CITIES:
                self._repository.create_city(
                    city_key=city.city_key,
                    display_name=city.display_name,
                    source_city_id=city.source_city_id,
                    display_order=city.display_order,
                    is_primary=city.is_primary,
                )
            return
        if self._repository.get_primary() is None:
            self._repository.set_primary(cities[0].city_key)
