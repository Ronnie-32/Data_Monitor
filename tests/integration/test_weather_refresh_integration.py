from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.infrastructure.workers import WorkerExecutor
from deskboard.models.weather import Weather
from deskboard.presentation.weather_presenter import (
    WEATHER_DISPLAY_MULTI_CITY,
    WeatherPresenter,
)
from deskboard.providers.base import NetworkItem, ProviderItemResult, ProviderResult
from deskboard.repositories.network_repository import NetworkRepository
from deskboard.repositories.weather_repository import WeatherRepository
from deskboard.services.refresh_service import DataRefreshService
from deskboard.services.status_service import StatusService
from deskboard.services.weather_service import WeatherService
from deskboard.ui.dashboard.bridge import DashboardBridge


@dataclass
class FakeClock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()

    def advance(self, **kwargs) -> None:
        self.current += timedelta(**kwargs)


class ControlledWorker(WorkerExecutor):
    def __init__(self) -> None:
        self.jobs: list[tuple[object, object, object]] = []

    def submit(self, job, on_success, on_error):
        self.jobs.append((job, on_success, on_error))
        return object()

    def resolve_next(self, value=None, error: BaseException | None = None) -> None:
        job, on_success, on_error = self.jobs.pop(0)
        if error is not None:
            on_error(error)
            return
        try:
            on_success(value if value is not None else job())
        except BaseException as job_error:
            on_error(job_error)


@dataclass
class FakeProvider:
    group: str
    response: object

    def fetch(self):
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


def make_weather_refresh(tmp_path, provider):
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    network_repository = NetworkRepository(connection)
    weather_service = WeatherService(WeatherRepository(connection))
    cities = weather_service.list_cities()
    items = [NetworkItem(city.city_key, "weather") for city in cities]
    clock = FakeClock(datetime(2026, 8, 24, 9, 30))
    worker = ControlledWorker()
    status = StatusService(network_repository, items=items)
    refresh = DataRefreshService(
        network_repository,
        clock,
        providers=[provider],
        items=items,
        worker_executor=worker,
        status_service=status,
    )
    presenter = WeatherPresenter(weather_service, refresh)
    return refresh, presenter, network_repository, worker, status


def weather(city: str, current: float) -> dict[str, object]:
    return Weather(city, "晴", current, current + 5, current - 5, "北风 2级").as_payload()


def test_weather_success_uses_network_cache_and_status_for_dashboard_data(tmp_path):
    provider = FakeProvider(
        "weather",
        ProviderResult.partial(
            [
                ProviderItemResult.success("beijing", weather("北京", 26)),
                ProviderItemResult.success("shanghai", weather("上海", 28)),
            ]
        ),
    )
    refresh, presenter, repository, worker, status = make_weather_refresh(tmp_path, provider)

    assert presenter.present(display_mode=WEATHER_DISPLAY_MULTI_CITY)["cities"] == []
    assert refresh.refresh_group("weather") is True
    worker.resolve_next()

    view_model = presenter.present(display_mode=WEATHER_DISPLAY_MULTI_CITY)
    assert [city["city"] for city in view_model["cities"]] == ["北京", "上海"]
    assert repository.get_cache("beijing").payload["current_temperature"] == 26.0
    assert repository.get_cache("shanghai").payload["current_temperature"] == 28.0
    assert status.color == "green"


def test_weather_failure_preserves_last_successful_payload_and_marks_global_status_red(
    tmp_path,
):
    provider = FakeProvider("weather", None)
    refresh, presenter, repository, worker, status = make_weather_refresh(tmp_path, provider)
    clock = refresh._clock
    repository.save_success("beijing", weather("北京", 25), clock.now())
    repository.save_success("shanghai", weather("上海", 27), clock.now())
    provider.response = ProviderResult.partial(
        [
            ProviderItemResult.success("beijing", weather("北京", 30)),
            ProviderItemResult.failure("shanghai", "forecast parse error"),
        ]
    )

    assert refresh.refresh_group("weather") is True
    worker.resolve_next()

    view_model = presenter.present(display_mode=WEATHER_DISPLAY_MULTI_CITY)
    assert [city["currentTemperature"] for city in view_model["cities"]] == [30.0, 27.0]
    assert repository.get_cache("shanghai").payload["current_temperature"] == 27.0
    assert repository.get_state("shanghai").last_status == "error"
    assert status.color == "red"


def test_refresh_completion_republishes_weather_and_status_to_dashboard_bridge(tmp_path):
    provider = FakeProvider(
        "weather",
        ProviderResult.partial(
            [
                ProviderItemResult.success("beijing", weather("北京", 26)),
                ProviderItemResult.success("shanghai", weather("上海", 28)),
            ]
        ),
    )
    refresh, presenter, _repository, worker, status = make_weather_refresh(tmp_path, provider)
    bridge = DashboardBridge(
        clock=FakeClock(datetime(2026, 8, 24, 9, 30)),
        weather_presenter=presenter,
        network_status_service=status,
        refresh_service=refresh,
    )
    states: list[dict[str, object]] = []
    bridge.stateChanged.connect(states.append)

    bridge.requestInitialState()
    assert states[-1]["networkStatus"] == {"state": "grey"}
    assert refresh.refresh_group("weather") is True
    worker.resolve_next()

    assert len(states) == 2
    assert [city["city"] for city in states[-1]["weather"]["cities"]] == ["北京"]
    assert states[-1]["networkStatus"] == {"state": "green"}
