from __future__ import annotations

from datetime import datetime

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.models.profile import ProfileState, ProfileWidgetState
from deskboard.repositories.profile_repository import ProfileRepository

NOW = datetime(2026, 8, 21, 9, 30)


def make_repository(tmp_path) -> tuple[ProfileRepository, object]:
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    return ProfileRepository(connection), connection


def sample_state() -> ProfileState:
    return ProfileState(
        window_x=40,
        window_y=60,
        window_width=960,
        window_height=720,
        theme_key="mint_breeze",
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


def test_repository_creates_default_and_round_trips_visual_state(tmp_path):
    repository, _connection = make_repository(tmp_path)

    default = repository.ensure_default(ProfileState(), NOW)
    user = repository.create("Study", sample_state(), NOW)

    assert default.name == "Default"
    assert default.is_builtin is True
    assert repository.list_profiles() == [default, user]
    assert repository.get(user.id) == user
    assert user.state == sample_state()


def test_repository_updates_state_and_delete_cascades_widget_rows(tmp_path):
    repository, connection = make_repository(tmp_path)
    user = repository.create("Study", ProfileState(), NOW)

    repository.save_state(user.id, sample_state(), NOW)
    assert repository.require(user.id).state == sample_state()

    repository.delete(user.id)

    assert repository.get(user.id) is None
    assert connection.execute(
        "SELECT COUNT(*) FROM profile_widgets WHERE profile_id = ?", (user.id,)
    ).fetchone()[0] == 0


def test_repository_reads_only_profile_tables():
    source = open("src/deskboard/repositories/profile_repository.py", encoding="utf-8").read()

    assert "profiles" in source
    assert "profile_widgets" in source
    for forbidden_table in (
        "todos",
        "semesters",
        "weather_cities",
        "finance_preferences",
        "network_cache",
        "network_state",
    ):
        assert forbidden_table not in source
