from __future__ import annotations

import os
import sqlite3

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QGroupBox, QScrollArea

from deskboard.database.schema import migrate
from deskboard.infrastructure.clock import SystemClock
from deskboard.models.profile import ProfileState
from deskboard.repositories.profile_repository import ProfileRepository
from deskboard.repositories.settings_repository import SettingsRepository
from deskboard.services.profile_service import ProfileService
from deskboard.services.settings_service import SettingsService
from deskboard.ui.settings.window import SettingsWindow


def test_task30_settings_defaults_to_chinese_switches_to_english_and_saves_visuals():
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    settings = SettingsService(SettingsRepository(connection))
    profiles = ProfileService(
        ProfileRepository(connection), SystemClock(), SettingsRepository(connection)
    )
    window = SettingsWindow(
        lambda _mode: None,
        lambda: None,
        lambda: None,
        lambda: None,
        settings_service=settings,
        profile_service=profiles,
    )

    assert settings.ui_language == "zh_CN"
    assert window.navigation.item(0).text() == "常规"
    assert window.header_title.text() == "DeskBoard 设置"
    assert window.profile_page.theme_combo.itemText(0) == "雾蓝晨光"
    assert (
        window.profile_page.findChild(QGroupBox, "settingsAppearanceGroup").title()
        == "看板主题与字体"
    )
    assert window.profile_page.theme_combo.findText("大地信号") >= 0

    window.language_combo.setCurrentIndex(window.language_combo.findData("en_US"))
    assert settings.ui_language == "en_US"
    assert window.navigation.item(0).text() == "General"
    assert window.header_title.text() == "DeskBoard Settings"

    profiles.save_as("Study", ProfileState())
    window.profile_page.refresh()
    window.profile_page.theme_combo.setCurrentIndex(
        window.profile_page.theme_combo.findData("ocean_night")
    )
    window.profile_page.font_combo.setCurrentIndex(
        window.profile_page.font_combo.findData("yahei")
    )
    assert window.profile_page.save_appearance() is True
    assert profiles.current_profile.state.theme_key == "ocean_night"
    assert profiles.current_profile.state.font_key == "yahei"

    window.close()
    connection.close()
    del app


def test_task30_settings_pages_scroll_and_ignore_system_dark_palette():
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    settings = SettingsService(SettingsRepository(connection))
    profiles = ProfileService(
        ProfileRepository(connection), SystemClock(), SettingsRepository(connection)
    )
    window = SettingsWindow(
        lambda _mode: None,
        lambda: None,
        lambda: None,
        lambda: None,
        settings_service=settings,
        profile_service=profiles,
    )

    assert window.pages.count() == len(window.PAGE_TITLES)
    assert all(
        isinstance(window.pages.widget(index), QScrollArea)
        for index in range(window.pages.count())
    )
    assert window.pages.widget(1).widget() is window.profile_page
    assert window.profile_page.theme_combo.findData("ocean_night") >= 0
    assert window.profile_page.font_combo.findData("source_han_sans") >= 0
    assert window.palette().color(QPalette.ColorRole.Window).name() == "#edf2f7"
    assert window.palette().color(QPalette.ColorRole.Base).name() == "#ffffff"

    window.close()
    connection.close()
    del app
