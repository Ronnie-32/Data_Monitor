from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.infrastructure.workers import WorkerExecutor
from deskboard.providers.base import NetworkItem
from deskboard.providers.china_index.provider import ChinaIndexProvider
from deskboard.repositories.network_repository import NetworkRepository
from deskboard.services.refresh_service import DataRefreshService
from deskboard.services.status_service import StatusService

FIXTURES = Path(__file__).parents[1] / "fixtures" / "providers"
CHINA_INDEX_ITEMS = (
    NetworkItem("index.sse", "indices"),
    NetworkItem("index.szse", "indices"),
    NetworkItem("index.chinext", "indices"),
    NetworkItem("index.csi300", "indices"),
)


@dataclass
class FakeClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


class ControlledWorker(WorkerExecutor):
    def __init__(self) -> None:
        self.jobs: list[tuple[object, object, object]] = []

    def submit(self, job, on_success, on_error):
        self.jobs.append((job, on_success, on_error))
        return object()

    def resolve_all(self) -> None:
        while self.jobs:
            job, on_success, on_error = self.jobs.pop(0)
            try:
                on_success(job())
            except BaseException as error:  # noqa: BLE001 - test worker forwards failures
                on_error(error)


class FixtureHttpClient:
    def __init__(self, response: bytes) -> None:
        self.response = response

    def get(self, _url: str, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(content=self.response)


def make_refresh(tmp_path):
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    repository = NetworkRepository(connection)
    worker = ControlledWorker()
    status = StatusService(repository, items=CHINA_INDEX_ITEMS)
    provider = ChinaIndexProvider(
        http_client=FixtureHttpClient(
            (FIXTURES / "tencent_indices_gbk.txt").read_bytes()
        )
    )
    refresh = DataRefreshService(
        repository,
        FakeClock(datetime(2026, 8, 24, 9, 30)),
        providers=[provider],
        items=CHINA_INDEX_ITEMS,
        worker_executor=worker,
        status_service=status,
    )
    return refresh, repository, worker, status


def test_china_indices_use_task15_cache_status_pipeline(tmp_path):
    refresh, repository, worker, status = make_refresh(tmp_path)

    assert refresh.refresh_group("indices") is True
    assert len(worker.jobs) == 1
    worker.resolve_all()

    assert repository.get_cache("index.sse").payload["value"] == 3903.72
    assert repository.get_cache("index.csi300").payload["change_percent"] == 0.09
    assert all(
        repository.get_state(item.key).last_status == "success"
        for item in CHINA_INDEX_ITEMS
    )
    assert status.color == "green"


def test_failed_china_index_refresh_preserves_previous_payload_and_marks_red(tmp_path):
    refresh, repository, worker, status = make_refresh(tmp_path)
    refresh.refresh_group("indices")
    worker.resolve_all()
    before = repository.get_cache("index.sse").payload

    class BrokenChinaIndexProvider:
        group = "indices"

        def fetch(self):
            raise RuntimeError("Tencent index fixture unavailable")

    refresh.register_provider(
        BrokenChinaIndexProvider(),
        items=CHINA_INDEX_ITEMS,
    )
    assert refresh.refresh_group("indices") is True
    worker.resolve_all()

    assert repository.get_cache("index.sse").payload == before
    assert repository.get_state("index.sse").last_status == "error"
    assert status.color == "red"
