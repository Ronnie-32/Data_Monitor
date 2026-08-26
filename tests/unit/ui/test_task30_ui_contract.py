from __future__ import annotations

from datetime import datetime

import pytest

from deskboard.database.connection import connect_database
from deskboard.database.schema import get_schema_version, migrate
from deskboard.models.profile import (
    PROFILE_FONT_KEYS,
    PROFILE_THEME_KEYS,
    ProfileState,
)
from deskboard.presentation.layout_state import present_profile_state
from deskboard.repositories.profile_repository import ProfileRepository
from deskboard.repositories.settings_repository import SettingsRepository
from deskboard.services.settings_service import SettingsService
from deskboard.ui.settings.i18n import translate_text


def test_task30_theme_catalog_and_font_catalog_are_explicit_and_include_accessible_modes():
    assert len(PROFILE_THEME_KEYS) >= 12
    assert {
        "mist_blue",
        "ocean_night",
        "high_contrast",
        "terra_signal",
        "endfield_industrial",
        "starrail_astral",
        "wuthering_tide",
    } <= set(PROFILE_THEME_KEYS)
    assert {"system_ui", "yahei", "source_han_sans"} <= set(PROFILE_FONT_KEYS)

    state = ProfileState(theme_key="ocean_night", font_key="source_han_sans")
    assert state.theme_key == "ocean_night"
    assert state.font_key == "source_han_sans"
    assert present_profile_state(state)["fontKey"] == "source_han_sans"

    with pytest.raises(ValueError, match="font"):
        ProfileState(font_key="missing-font")


def test_task30_profile_font_round_trips_through_sqlite():
    connection = connect_database(":memory:")
    migrate(connection)
    repository = ProfileRepository(connection)

    created = repository.create(
        "Night study",
        ProfileState(theme_key="graphite_night", font_key="yahei"),
        datetime(2026, 8, 25, 9, 30),
    )

    assert repository.require(created.id).state.font_key == "yahei"
    assert "font_key" in {
        row[1] for row in connection.execute("PRAGMA table_info(profiles)")
    }
    assert get_schema_version(connection) >= 3


def test_task30_settings_language_defaults_to_chinese_and_persists():
    connection = connect_database(":memory:")
    migrate(connection)
    service = SettingsService(SettingsRepository(connection))

    assert service.ui_language == "zh_CN"
    assert service.set_ui_language("en_US") == "en_US"
    assert service.ui_language == "en_US"
    assert service.get("ui.language") == "en_US"

    with pytest.raises(ValueError, match="language"):
        service.set_ui_language("fr_FR")


def test_task30_translation_pairs_are_bidirectional_for_settings_shell():
    assert translate_text("General", "zh_CN") == "常规"
    assert translate_text("常规", "en_US") == "General"
    assert translate_text("Profiles", "zh_CN") == "配置方案"
    assert translate_text("配置方案", "en_US") == "Profiles"
