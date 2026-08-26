import sqlite3

from PySide6.QtWidgets import QApplication, QPushButton

from deskboard.app.modes import AppMode
from deskboard.database.schema import migrate
from deskboard.infrastructure.clock import SystemClock
from deskboard.models.profile import ProfileState
from deskboard.presentation.weather_presenter import WEATHER_DISPLAY_MULTI_CITY
from deskboard.providers.weather.location_catalog import (
    WeatherLocation,
    WeatherLocationCatalog,
)
from deskboard.repositories.finance_repository import FinanceRepository
from deskboard.repositories.profile_repository import ProfileRepository
from deskboard.repositories.settings_repository import SettingsRepository
from deskboard.repositories.weather_repository import WeatherRepository
from deskboard.services.finance_service import FinanceService
from deskboard.services.profile_service import ProfileService
from deskboard.services.settings_service import SettingsService
from deskboard.services.weather_service import WeatherService
from deskboard.ui.settings.profile_page import ProfilePage
from deskboard.ui.settings.weather_page import WeatherPage
from deskboard.ui.settings.window import SettingsWindow


class FakeAutostart:
    def __init__(self) -> None:
        self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled


def _services():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    return (
        connection,
        SettingsService(SettingsRepository(connection)),
        ProfileService(
            ProfileRepository(connection), SystemClock(), SettingsRepository(connection)
        ),
        WeatherService(WeatherRepository(connection)),
        FinanceService(FinanceRepository(connection)),
    )


def test_task24_settings_window_mounts_native_pages_and_actions_use_services():
    app = QApplication.instance() or QApplication([])
    connection, settings, profiles, weather, finance = _services()
    modes: list[AppMode] = []
    autostart = FakeAutostart()
    window = SettingsWindow(
        modes.append,
        lambda: None,
        lambda: None,
        lambda: None,
        settings_service=settings,
        profile_service=profiles,
        weather_service=weather,
        finance_service=finance,
        autostart=autostart,
    )

    assert window.pages.widget(0).widget() is window.general_page
    assert window.pages.widget(1).widget() is window.profile_page
    assert window.pages.widget(2).widget() is window.weather_page
    assert window.pages.widget(3).widget() is window.finance_page

    general = window.general_page
    general.autostart_checkbox.setChecked(True)
    general.interaction_button.click()
    assert autostart.enabled is True
    assert modes == [AppMode.INTERACTION]

    weather_page = window.weather_page
    weather_page.set_primary_key("shanghai")
    assert weather.get_primary_city().city_key == "shanghai"

    finance_page = window.finance_page
    first_key = finance.list_preferences()[0].item_key
    finance_page.set_item_enabled(first_key, False)
    assert finance.is_enabled(first_key) is False

    profile_page = window.profile_page
    profile_page.save_as_profile("Study")
    assert profiles.current_profile.name == "Study"

    window.close()
    connection.close()
    del app


def test_weather_settings_notifies_runtime_when_city_configuration_changes():
    app = QApplication.instance() or QApplication([])
    connection, _settings, _profiles, weather, _finance = _services()
    changes: list[bool] = []
    page = WeatherPage(weather, on_cities_changed=changes.append)

    assert page.add_city("suzhou", "苏州", "suzhou") is True
    assert weather.get_city("suzhou").source_city_id == "101190401"
    assert page.set_primary_key("suzhou") is True

    assert changes == [True, False]
    page.close()
    connection.close()
    del app


def test_weather_settings_searches_and_adds_a_catalog_location_with_source_id():
    app = QApplication.instance() or QApplication([])
    connection, _settings, _profiles, weather, _finance = _services()
    changes: list[bool] = []
    catalog = WeatherLocationCatalog(
        (
            WeatherLocation("101190401", "苏州", "江苏", "suzhou"),
        )
    )
    page = WeatherPage(
        weather,
        location_catalog=catalog,
        on_cities_changed=changes.append,
    )

    page.location_search_input.setText("suzhou")

    assert page.location_search_results.count() == 1
    assert page.location_search_results.item(0).text() == "苏州 · 江苏"
    assert page.add_selected_location() is True
    assert weather.get_city("weather_101190401").source_city_id == "101190401"
    assert changes == [True]

    page.close()
    connection.close()
    del app


def test_weather_settings_uses_compact_search_and_two_column_actions():
    app = QApplication.instance() or QApplication([])
    connection, _settings, _profiles, weather, _finance = _services()
    page = WeatherPage(weather)

    assert page.location_search_row.count() == 2
    assert page.city_list.minimumHeight() >= 220
    assert page.action_grid.columnCount() == 2
    assert page.action_grid.itemAtPosition(0, 0) is not None
    assert page.action_grid.itemAtPosition(0, 1) is not None

    page.close()
    connection.close()
    del app


def test_profile_settings_can_persist_multi_city_weather_display_mode():
    app = QApplication.instance() or QApplication([])
    connection, _settings, profiles, _weather, _finance = _services()
    profiles.save_as("Study", ProfileState())
    page = ProfilePage(profiles)
    page.weather_mode_combo.setCurrentIndex(
        page.weather_mode_combo.findData(WEATHER_DISPLAY_MULTI_CITY)
    )

    assert page.save_weather_display_mode() is True
    weather_widget = next(
        widget for widget in profiles.current_profile.state.widgets
        if widget.widget_key == "weather"
    )
    assert weather_widget.config["displayMode"] == WEATHER_DISPLAY_MULTI_CITY
    page.close()
    connection.close()
    del app


def test_profile_page_previews_visual_choices_and_creates_profile_inline():
    app = QApplication.instance() or QApplication([])
    connection, _settings, profiles, _weather, _finance = _services()
    previews: list[ProfileState] = []
    page = ProfilePage(profiles, on_profile_preview=previews.append)

    page.theme_combo.setCurrentIndex(page.theme_combo.findData("ocean_night"))
    page.font_combo.setCurrentIndex(page.font_combo.findData("yahei"))

    assert previews
    assert previews[-1].theme_key == "ocean_night"
    assert previews[-1].font_key == "yahei"

    page.new_profile_name_input.setText("Evening")
    assert page.create_profile_from_input() is True
    assert profiles.current_profile.name == "Evening"
    assert profiles.current_profile.state.theme_key == "ocean_night"
    assert profiles.current_profile.state.font_key == "yahei"
    assert page.new_profile_name_input.text() == ""

    page.close()
    connection.close()
    del app


def test_profile_save_as_button_does_not_pass_qt_checked_state_as_profile_name(
    monkeypatch,
):
    app = QApplication.instance() or QApplication([])
    connection, _settings, profiles, _weather, _finance = _services()
    page = ProfilePage(profiles)
    seen: list[object] = []

    def fake_name_input(_title: str, name: object) -> str:
        seen.append(name)
        assert name is None
        return "Study"

    monkeypatch.setattr(page, "_name_input", fake_name_input)
    save_as = next(
        button for button in page.findChildren(QPushButton) if button.text() == "Save As"
    )

    save_as.click()

    assert seen == [None]
    assert profiles.current_profile.name == "Study"
    page.close()
    connection.close()
    del app
