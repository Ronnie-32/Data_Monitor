from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.infrastructure.workers import WorkerExecutor
from deskboard.providers.base import NetworkItem
from deskboard.providers.fx.provider import FXProvider
from deskboard.providers.gold.provider import GoldProvider
from deskboard.repositories.network_repository import NetworkRepository
from deskboard.services.refresh_service import DataRefreshService
from deskboard.services.status_service import StatusService

FIXTURES = Path(__file__).parents[1] / "fixtures" / "providers"


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
            except BaseException as error:  # noqa: BLE001 - test worker forwards job errors
                on_error(error)


class FixtureHttpClient:
    def __init__(self, *, gold: bytes, fx: bytes) -> None:
        self.gold = gold
        self.fx = fx

    def get_text(self, url: str, **_kwargs: object) -> str:
        if "sge.com.cn" in url:
            return self.gold.decode("utf-8")
        if "chinamoney.com.cn" in url:
            return self.fx.decode("utf-8")
        raise AssertionError(f"unexpected provider URL: {url}")


def make_refresh(tmp_path):
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    repository = NetworkRepository(connection)
    clock = FakeClock(datetime(2026, 8, 24, 9, 30))
    worker = ControlledWorker()
    client = FixtureHttpClient(
        gold=(FIXTURES / "sge_au9999_daily.html").read_bytes(),
        fx=(FIXTURES / "chinamoney_ccpr_his_new.json").read_bytes(),
    )
    gold = GoldProvider(
        http_client=client,
        as_of=date(2026, 8, 24),
        lookback_days=1,
    )
    fx = FXProvider(http_client=client, as_of=date(2026, 8, 24))
    items = (
        NetworkItem("gold.au9999", "gold"),
        NetworkItem("fx.usd_cny", "fx"),
        NetworkItem("fx.eur_cny", "fx"),
        NetworkItem("fx.jpy_cny", "fx"),
        NetworkItem("fx.hkd_cny", "fx"),
    )
    status = StatusService(repository, items=items)
    refresh = DataRefreshService(
        repository,
        clock,
        providers=[gold, fx],
        items=items,
        worker_executor=worker,
        status_service=status,
    )
    return refresh, repository, worker, status


def test_gold_and_fx_use_task15_cache_status_pipeline_independently(tmp_path):
    refresh, repository, worker, status = make_refresh(tmp_path)

    assert refresh.refresh_all() == ("fx", "gold")
    assert len(worker.jobs) == 2
    worker.resolve_all()

    assert repository.get_cache("gold.au9999").payload["value"] == 968.14
    assert repository.get_cache("fx.jpy_cny").payload["value"] == 0.042636
    assert repository.get_state("gold.au9999").last_status == "success"
    assert repository.get_state("fx.usd_cny").last_status == "success"
    assert status.color == "green"


def test_provider_failure_keeps_previous_finance_payload_and_marks_status_red(tmp_path):
    refresh, repository, worker, status = make_refresh(tmp_path)
    refresh.refresh_all()
    worker.resolve_all()
    before = repository.get_cache("fx.usd_cny").payload

    class BrokenFx:
        group = "fx"

        def fetch(self):
            raise RuntimeError("FX fixture unavailable")

    refresh.register_provider(
        BrokenFx(),
        items=[
            NetworkItem("fx.usd_cny", "fx"),
            NetworkItem("fx.eur_cny", "fx"),
            NetworkItem("fx.jpy_cny", "fx"),
            NetworkItem("fx.hkd_cny", "fx"),
        ],
    )
    assert refresh.refresh_group("fx") is True
    worker.resolve_all()

    assert repository.get_cache("fx.usd_cny").payload == before
    assert repository.get_state("fx.usd_cny").last_status == "error"
    assert status.color == "red"
