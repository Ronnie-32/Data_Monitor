from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.infrastructure.workers import QtThreadPoolExecutor
from deskboard.providers.base import NetworkItem, ProviderItemResult, ProviderResult
from deskboard.repositories.network_repository import NetworkRepository
from deskboard.services.refresh_service import (
    REFRESH_INTERVAL,
    DataRefreshService,
)
from deskboard.services.status_service import StatusService


@dataclass
class FakeClock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()

    def advance(self, **kwargs) -> None:
        self.current += timedelta(**kwargs)


class ControlledWorker:
    def __init__(self) -> None:
        self.jobs: list[tuple[object, object, object]] = []

    def submit(self, job, on_success, on_error):
        self.jobs.append((job, on_success, on_error))
        return object()

    def resolve_next(self, value=None, error: BaseException | None = None) -> None:
        job, on_success, on_error = self.jobs.pop(0)
        if error is not None:
            on_error(error)
        else:
            try:
                on_success(value if value is not None else job())
            except BaseException as job_error:
                on_error(job_error)


@dataclass
class FakeProvider:
    group: str
    response: object = None

    def fetch(self):
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


def make_service(tmp_path, *, provider, items, clock=None, worker=None):
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    repository = NetworkRepository(connection)
    selected_clock = clock or FakeClock(datetime(2026, 8, 21, 9, 30))
    selected_worker = worker or ControlledWorker()
    status = StatusService(repository, items=items)
    service = DataRefreshService(
        repository,
        selected_clock,
        providers=[provider],
        items=items,
        worker_executor=selected_worker,
        status_service=status,
    )
    return service, repository, selected_clock, selected_worker, status


def test_refresh_interval_is_fixed_and_visibility_does_not_stop_next_cycle(tmp_path):
    clock = FakeClock(datetime(2026, 8, 21, 9, 30))
    provider = FakeProvider(
        "weather",
        ProviderResult.success("weather", {"temperature": 25}),
    )
    service, _repository, _clock, worker, _status = make_service(
        tmp_path,
        provider=provider,
        items=[NetworkItem("weather", "weather")],
        clock=clock,
    )

    assert REFRESH_INTERVAL == timedelta(minutes=60)
    service.startup()
    worker.resolve_next()
    service.set_dashboard_visible(False)
    clock.advance(minutes=59)
    assert service.refresh_due() == ()
    clock.advance(minutes=1)
    assert service.refresh_due() == ("weather",)
    assert len(worker.jobs) == 1


def test_fresh_cache_is_returned_without_restart_refresh_and_restores_green(tmp_path):
    provider = FakeProvider("weather", ProviderResult.success("weather", {"new": 2}))
    service, repository, clock, worker, status = make_service(
        tmp_path,
        provider=provider,
        items=[NetworkItem("weather", "weather")],
    )
    repository.save_success("weather", {"old": 1}, clock.now() - timedelta(minutes=10))

    startup = service.startup()

    assert startup.cached_payloads == {"weather": {"old": 1}}
    assert startup.scheduled_groups == ()
    assert worker.jobs == []
    assert status.color == "green"


def test_fresh_cache_with_persisted_failure_is_red_without_restart_refresh(tmp_path):
    provider = FakeProvider("weather", ProviderResult.success("weather", {"new": 2}))
    service, repository, clock, worker, status = make_service(
        tmp_path,
        provider=provider,
        items=[NetworkItem("weather", "weather")],
    )
    repository.save_success("weather", {"old": 1}, clock.now() - timedelta(minutes=10))
    repository.record_failure("weather", clock.now() - timedelta(minutes=5), "offline")

    service.startup()

    assert worker.jobs == []
    assert status.color == "red"


def test_stale_cache_is_returned_immediately_and_group_refresh_is_scheduled(tmp_path):
    provider = FakeProvider("weather", ProviderResult.success("weather", {"new": 2}))
    service, repository, clock, worker, status = make_service(
        tmp_path,
        provider=provider,
        items=[NetworkItem("weather", "weather")],
    )
    repository.save_success("weather", {"old": 1}, clock.now() - REFRESH_INTERVAL)

    startup = service.startup()

    assert startup.cached_payloads == {"weather": {"old": 1}}
    assert startup.scheduled_groups == ("weather",)
    assert len(worker.jobs) == 1
    assert status.color == "grey"


def test_no_cache_schedules_background_refresh_without_a_connectivity_gate(tmp_path):
    provider = FakeProvider(
        "weather",
        ProviderResult.success("weather", {"temperature": 25}),
    )
    service, _repository, _clock, worker, _status = make_service(
        tmp_path,
        provider=provider,
        items=[NetworkItem("weather", "weather")],
    )

    startup = service.startup()

    assert startup.cached_payloads == {}
    assert startup.scheduled_groups == ("weather",)
    assert len(worker.jobs) == 1


def test_duplicate_group_refresh_is_ignored_without_a_queue(tmp_path):
    provider = FakeProvider("weather", ProviderResult.success("weather", {"ok": True}))
    service, _repository, _clock, worker, _status = make_service(
        tmp_path,
        provider=provider,
        items=[NetworkItem("weather", "weather")],
    )

    assert service.refresh_group("weather") is True
    assert service.refresh_group("weather") is False
    assert service.refresh_group("weather") is False
    assert len(worker.jobs) == 1
    assert service.active_groups == ("weather",)


def test_partial_success_commits_good_item_and_preserves_failed_item_cache(tmp_path):
    provider = FakeProvider("finance")
    items = [
        NetworkItem("gold", "finance"),
        NetworkItem("fx", "finance"),
    ]
    service, repository, clock, worker, status = make_service(
        tmp_path,
        provider=provider,
        items=items,
        clock=FakeClock(datetime(2026, 8, 21, 9, 30)),
    )
    repository.save_success("gold", {"value": 1}, clock.now() - timedelta(minutes=2))
    repository.save_success("fx", {"value": 2}, clock.now() - timedelta(minutes=2))
    provider.response = ProviderResult(
        (
            ProviderItemResult.success("gold", {"value": 3}),
            ProviderItemResult.failure("fx", "parse error"),
        )
    )

    assert service.refresh_group("finance") is True
    worker.resolve_next()

    assert repository.get_cache("gold").payload == {"value": 3}
    assert repository.get_cache("fx").payload == {"value": 2}
    assert repository.get_state("gold").last_status == "success"
    assert repository.get_state("fx").last_status == "error"
    assert status.color == "red"
    assert service.active_groups == ()


def test_group_failure_preserves_success_cache_and_has_no_short_retry(tmp_path):
    provider = FakeProvider("weather", RuntimeError("provider timeout"))
    service, repository, clock, worker, status = make_service(
        tmp_path,
        provider=provider,
        items=[NetworkItem("weather", "weather")],
    )
    repository.save_success("weather", {"old": 1}, clock.now() - timedelta(minutes=5))

    assert service.refresh_group("weather") is True
    worker.resolve_next()
    assert repository.get_cache("weather").payload == {"old": 1}
    assert repository.get_state("weather").last_status == "error"
    assert status.color == "red"

    clock.advance(minutes=1)
    assert service.refresh_due() == ()
    assert len(worker.jobs) == 0


def test_manual_and_automatic_refresh_share_the_same_group_path(tmp_path):
    provider = FakeProvider("weather", ProviderResult.success("weather", {"ok": True}))
    clock = FakeClock(datetime(2026, 8, 21, 9, 30))
    service, _repository, _clock, worker, _status = make_service(
        tmp_path,
        provider=provider,
        items=[NetworkItem("weather", "weather")],
        clock=clock,
    )
    service.startup()
    worker.resolve_next()
    clock.advance(minutes=60)

    assert service.refresh_due() == ("weather",)
    assert service.refresh_group("weather") is False
    assert len(worker.jobs) == 1


def test_two_items_in_one_group_use_one_underlying_worker(tmp_path):
    provider = FakeProvider("finance", ProviderResult.success("gold", {"value": 1}))
    items = [NetworkItem("gold", "finance"), NetworkItem("fx", "finance")]
    service, _repository, _clock, worker, _status = make_service(
        tmp_path,
        provider=provider,
        items=items,
    )

    assert service.refresh_all() == ("finance",)
    assert len(worker.jobs) == 1


def test_qt_worker_runs_job_off_the_calling_thread():
    executor = QtThreadPoolExecutor()
    caller = threading.get_ident()
    finished = threading.Event()
    observed: list[int] = []

    def job():
        observed.append(threading.get_ident())
        finished.set()

    executor.submit(job, lambda _result: None, lambda _error: None)

    assert finished.wait(2)
    assert observed and observed[0] != caller
