from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

import pytest

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.models.profile import (
    PROFILE_THEME_KEYS,
    ProfileState,
    ProfileWidgetState,
)
from deskboard.repositories.profile_repository import ProfileRepository
from deskboard.repositories.settings_repository import SettingsRepository
from deskboard.services.profile_service import (
    BuiltinProfileError,
    ProfileLimitError,
    ProfileService,
)


@dataclass
class FakeClock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()


@pytest.fixture
def resources(tmp_path):
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    clock = FakeClock(datetime(2026, 8, 21, 9, 30))
    service = ProfileService(
        ProfileRepository(connection), clock, SettingsRepository(connection)
    )
    return service, connection, clock


def sample_state(*, theme_key: str = "mint_breeze") -> ProfileState:
    return ProfileState(
        window_x=40,
        window_y=60,
        window_width=960,
        window_height=720,
        theme_key=theme_key,
        panel_opacity=0.82,
        widgets=(
            ProfileWidgetState(
                widget_key="weather",
                visible=True,
                x=1,
                y=2,
                w=5,
                h=4,
                config={"display_mode": "expanded"},
            ),
        ),
    )


def test_default_is_created_and_cannot_be_overwritten_or_deleted(resources):
    service, _connection, _clock = resources
    default = service.current_profile

    assert default.name == "Default"
    assert default.is_builtin is True

    with pytest.raises(BuiltinProfileError, match="Default"):
        service.save_current(sample_state())
    with pytest.raises(BuiltinProfileError, match="Default"):
        service.delete(default.id)


def test_save_as_switches_and_persists_visual_state(resources):
    service, connection, clock = resources
    created = service.save_as("Study", sample_state())

    assert service.current_profile.id == created.id
    assert service.current_profile.state == sample_state()

    reloaded = ProfileService(
        ProfileRepository(connection), clock, SettingsRepository(connection)
    )
    assert reloaded.current_profile.id == created.id
    assert reloaded.current_profile.state == sample_state()


def test_save_current_rename_switch_delete_and_restore_default(resources):
    service, _connection, _clock = resources
    first = service.save_as("First", ProfileState())
    second = service.save_as("Second", sample_state())

    service.switch(first.id)
    service.save_current(sample_state(theme_key="lavender_cloud"))
    service.rename(first.id, "Renamed")
    assert service.current_profile.name == "Renamed"
    assert service.current_profile.state.theme_key == "lavender_cloud"

    service.delete(first.id)
    assert service.current_profile.name == "Default"
    assert service.get(second.id).name == "Second"

    service.switch(second.id)
    restored = service.restore_default()
    assert restored == service.get(service.default_profile.id).state
    assert service.current_profile.name == "Default"


def test_eight_user_limit_excludes_default(resources):
    service, _connection, _clock = resources

    for index in range(8):
        service.save_as(f"Profile {index}", ProfileState())

    with pytest.raises(ProfileLimitError, match="8"):
        service.save_as("Ninth", ProfileState())

    assert len([profile for profile in service.list_profiles() if not profile.is_builtin]) == 8


def test_duplicate_widget_and_invalid_profile_data_are_rejected(resources):
    service, _connection, _clock = resources
    with pytest.raises(ValueError, match="widget"):
        service.save_as(
            "Duplicate",
            ProfileState(
                widgets=(
                    ProfileWidgetState("weather", True, 0, 0, 4, 3),
                    ProfileWidgetState("weather", True, 4, 0, 4, 3),
                )
            ),
        )
    with pytest.raises(ValueError, match="theme"):
        service.save_as("Bad theme", ProfileState(theme_key="dark"))


def test_profile_state_does_not_capture_global_data_and_themes_are_exact():
    assert PROFILE_THEME_KEYS == (
        "mist_blue",
        "mint_breeze",
        "almond_sand",
        "lavender_cloud",
    )
    state = ProfileState()
    assert not hasattr(state, "todos")
    assert not hasattr(state, "weather_cities")
    assert not hasattr(state, "finance_preferences")
    assert not hasattr(state, "network_cache")
