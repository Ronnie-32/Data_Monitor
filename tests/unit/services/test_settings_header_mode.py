from __future__ import annotations

import sqlite3

import pytest

from deskboard.database.schema import migrate
from deskboard.repositories.settings_repository import SettingsRepository
from deskboard.services.settings_service import SettingsService


def test_timetable_header_mode_is_validated_and_persisted_in_sqlite():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    service = SettingsService(SettingsRepository(connection))

    assert service.timetable_header_mode == "weekday_date"
    assert service.set_timetable_header_mode("date-only") == "date"
    assert service.timetable_header_mode == "date"

    with pytest.raises(ValueError):
        service.set_timetable_header_mode("arbitrary")
    assert service.timetable_header_mode == "date"
