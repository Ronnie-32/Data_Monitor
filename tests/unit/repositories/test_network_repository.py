from __future__ import annotations

from datetime import datetime, timedelta

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.repositories.network_repository import NetworkRepository

NOW = datetime(2026, 8, 21, 9, 30)


def make_repository(tmp_path) -> tuple[NetworkRepository, object]:
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    return NetworkRepository(connection), connection


def test_success_cache_and_attempt_state_are_separate(tmp_path):
    repository, _connection = make_repository(tmp_path)

    repository.save_success("weather", {"temperature": 25}, NOW)
    cached_before_failure = repository.get_cache("weather")
    state_before_failure = repository.get_state("weather")

    repository.record_failure("weather", NOW + timedelta(minutes=1), "timeout")

    assert repository.get_cache("weather") == cached_before_failure
    assert repository.get_cache("weather").payload == {"temperature": 25}
    assert repository.get_state("weather") != state_before_failure
    assert repository.get_state("weather").last_status == "error"
    assert repository.get_state("weather").last_error_summary == "timeout"


def test_success_replaces_payload_and_clears_previous_error(tmp_path):
    repository, _connection = make_repository(tmp_path)

    repository.save_success("gold", {"value": 1}, NOW)
    repository.record_failure("gold", NOW + timedelta(minutes=1), "parse error")
    repository.save_success("gold", {"value": 2}, NOW + timedelta(minutes=2))

    cache = repository.get_cache("gold")
    state = repository.get_state("gold")
    assert cache is not None
    assert cache.payload == {"value": 2}
    assert cache.success_at == NOW + timedelta(minutes=2)
    assert state is not None
    assert state.last_status == "success"
    assert state.last_attempt_at == NOW + timedelta(minutes=2)
    assert state.last_error_summary is None


def test_missing_cache_and_state_are_explicitly_unknown(tmp_path):
    repository, connection = make_repository(tmp_path)

    assert repository.get_cache("unknown") is None
    assert repository.get_state("unknown") is None
    cache_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(network_cache)")
    }
    state_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(network_state)")
    }
    assert "color" not in cache_columns | state_columns
