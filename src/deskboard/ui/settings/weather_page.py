"""Native global Weather-city Settings page."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from deskboard.providers.weather.location_catalog import (
    WEATHER_LOCATION_CATALOG,
    WeatherLocation,
    WeatherLocationCatalog,
)
from deskboard.ui.settings.i18n import SUPPORTED_LANGUAGES, translate_text


class WeatherPage(QWidget):
    def __init__(
        self,
        weather_service: Any | None,
        *,
        location_catalog: WeatherLocationCatalog | None = None,
        on_cities_changed: Callable[[bool], object] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = weather_service
        self._location_catalog = (
            WEATHER_LOCATION_CATALOG if location_catalog is None else location_catalog
        )
        self._on_cities_changed = on_cities_changed
        self._language = "zh_CN"
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Global weather cities", self))
        layout.addWidget(QLabel("Search mainland-China locations (Chinese / pinyin):", self))
        self.location_search_input = QLineEdit(self)
        self.location_search_input.setPlaceholderText(
            "e.g. Suzhou, suzhou, Chaoyang"
        )
        self.location_search_input.textChanged.connect(self.search_city_locations)
        self.location_search_row = QHBoxLayout()
        self.location_search_row.setContentsMargins(0, 0, 0, 0)
        self.location_search_row.addWidget(self.location_search_input, 1)
        self.add_location_button = QPushButton("Add Selected Location", self)
        self.add_location_button.setMinimumWidth(160)
        self.add_location_button.clicked.connect(
            lambda _checked=False: self.add_selected_location()
        )
        self.location_search_row.addWidget(self.add_location_button)
        layout.addLayout(self.location_search_row)
        self.location_search_results = QListWidget(self)
        self.location_search_results.setMinimumHeight(96)
        self.location_search_results.setMaximumHeight(180)
        self.location_search_results.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.location_search_results.itemDoubleClicked.connect(
            lambda _item: self.add_selected_location()
        )
        layout.addWidget(self.location_search_results)
        layout.addWidget(QLabel("Configured global cities", self))
        self.city_list = QListWidget(self)
        self.city_list.setMinimumHeight(220)
        self.city_list.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.city_list.setAlternatingRowColors(True)
        layout.addWidget(self.city_list, 1)
        primary_row = QHBoxLayout()
        primary_row.setContentsMargins(0, 0, 0, 0)
        primary_row.addWidget(QLabel("Primary city", self))
        self.primary_combo = QComboBox(self)
        self.primary_combo.currentIndexChanged.connect(self._primary_changed)
        primary_row.addWidget(self.primary_combo, 1)
        layout.addLayout(primary_row)
        self.action_grid = QGridLayout()
        self.action_grid.setHorizontalSpacing(8)
        self.action_grid.setVerticalSpacing(8)
        for title, callback in (
            ("Move Up", lambda: self.move_selected(-1)),
            ("Move Down", lambda: self.move_selected(1)),
            ("Add City", self.add_city_from_dialog),
            ("Remove City", self.remove_selected),
        ):
            button = QPushButton(title, self)
            button.clicked.connect(callback)
            self.action_grid.addWidget(
                button,
                self.action_grid.count() // 2,
                self.action_grid.count() % 2,
            )
        layout.addLayout(self.action_grid)
        self.status_label = QLabel(self)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        self.refresh()

    def search_city_locations(self, query: str | None = None) -> tuple[WeatherLocation, ...]:
        if query is None:
            query = self.location_search_input.text()
        results = self._location_catalog.search(query)
        with QSignalBlocker(self.location_search_results):
            self.location_search_results.clear()
            for location in results:
                item = QListWidgetItem(location.display_label, self.location_search_results)
                item.setData(Qt.ItemDataRole.UserRole, location.source_city_id)
            if results:
                self.location_search_results.setCurrentRow(0)
        if hasattr(self, "status_label") and query.strip():
            if results:
                self.status_label.setText(
                    (
                        f"找到 {len(results)} 个匹配城市，请选择后添加"
                        if self._language == "zh_CN"
                        else f"Found {len(results)} matching locations; select one to add"
                    )
                )
            else:
                self.status_label.setText(
                    translate_text("No matching weather location", self._language)
                )
        return results

    def add_selected_location(self) -> bool:
        if self._service is None:
            return False
        item = self.location_search_results.currentItem()
        if item is None:
            return False
        source_city_id = item.data(Qt.ItemDataRole.UserRole)
        if source_city_id is None:
            return False
        location = self._location_catalog.get(str(source_city_id))
        if location is None:
            self.status_label.setText(
                translate_text(
                    "Selected weather location is no longer available", self._language
                )
            )
            return False
        existing = self._service.get_city_by_source_city_id(location.source_city_id)
        if existing is not None:
            self._select_city(existing.city_key)
            self.status_label.setText(
                (
                    f"城市已添加：{existing.display_name}"
                    if self._language == "zh_CN"
                    else f"Location already added: {existing.display_name}"
                )
            )
            return False
        added = self.add_city(
            location.city_key,
            location.display_name,
            location.source_city_id,
        )
        if added:
            self._select_city(location.city_key)
        return added

    def refresh(self) -> None:
        if self._service is None:
            self.city_list.clear()
            self.primary_combo.clear()
            self.status_label.setText(
                translate_text("Weather service unavailable", self._language)
            )
            return
        cities = self._service.list_cities()
        selected_key = self._selected_key()
        with QSignalBlocker(self.city_list), QSignalBlocker(self.primary_combo):
            self.city_list.clear()
            self.primary_combo.clear()
            for city in cities:
                item = QListWidgetItem(city.display_name, self.city_list)
                item.setData(Qt.ItemDataRole.UserRole, city.city_key)
                combo_index = self.primary_combo.count()
                self.primary_combo.addItem(city.display_name, city.city_key)
                if city.is_primary:
                    self.primary_combo.setCurrentIndex(combo_index)
                if city.city_key == selected_key:
                    self.city_list.setCurrentItem(item)
        self.status_label.setText(
            (
                f"共 {len(cities)} 个城市；主城市为全局设置"
                if self._language == "zh_CN"
                else f"{len(cities)} cities; primary is global"
            )
        )

    def set_language(self, language: str) -> None:
        if language not in SUPPORTED_LANGUAGES:
            return
        self._language = language
        self.refresh()

    def set_primary_key(self, city_key: str) -> bool:
        if self._service is None:
            return False
        try:
            self._service.set_primary_city(city_key)
        except (LookupError, TypeError, ValueError) as error:
            self.status_label.setText(str(error))
            return False
        self.refresh()
        self._notify_cities_changed(requires_refresh=False)
        return True

    def move_selected(self, delta: int) -> bool:
        if self._service is None or self.city_list.currentRow() < 0:
            return False
        row = self.city_list.currentRow()
        target = row + delta
        if target < 0 or target >= self.city_list.count():
            return False
        keys = [
            self.city_list.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(self.city_list.count())
        ]
        keys[row], keys[target] = keys[target], keys[row]
        try:
            self._service.reorder_cities(keys)
        except (LookupError, TypeError, ValueError) as error:
            self.status_label.setText(str(error))
            return False
        self.refresh()
        self.city_list.setCurrentRow(target)
        self._notify_cities_changed(requires_refresh=False)
        return True

    def add_city(self, city_key: str, display_name: str, source_city_id: str) -> bool:
        if self._service is None:
            return False
        try:
            self._service.add_city(city_key, display_name, source_city_id)
        except (LookupError, TypeError, ValueError) as error:
            self.status_label.setText(str(error))
            return False
        self.refresh()
        self._notify_cities_changed(requires_refresh=True)
        return True

    def add_city_from_dialog(self) -> bool:
        values: list[str] = []
        for title, label in (
            ("Add Weather City", "City key:"),
            ("Add Weather City", "Display name:"),
            (
                "Add Weather City",
                "Weather source city ID (numeric; Suzhou also accepts suzhou):",
            ),
        ):
            value, accepted = QInputDialog.getText(
                self.window(),
                translate_text(title, self._language),
                translate_text(label, self._language),
            )
            if not accepted or not value.strip():
                return False
            values.append(value.strip())
        return self.add_city(*values)

    def remove_selected(self) -> bool:
        if self._service is None or self.city_list.currentItem() is None:
            return False
        city_key = self._selected_key()
        if city_key is None:
            return False
        if (
            QMessageBox.question(
                self.window(),
                translate_text("Remove Weather City", self._language),
                translate_text("Remove the selected weather city?", self._language),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return False
        try:
            self._service.delete_city(city_key)
        except (LookupError, TypeError, ValueError) as error:
            self.status_label.setText(str(error))
            return False
        self.refresh()
        self._notify_cities_changed(requires_refresh=True)
        return True

    def _primary_changed(self, index: int) -> None:
        if index < 0 or self._service is None:
            return
        city_key = self.primary_combo.itemData(index)
        if city_key is not None:
            self.set_primary_key(str(city_key))

    def _selected_key(self) -> str | None:
        item = self.city_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return None if value is None else str(value)

    def _select_city(self, city_key: str) -> None:
        for row in range(self.city_list.count()):
            item = self.city_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == city_key:
                self.city_list.setCurrentRow(row)
                return

    def _notify_cities_changed(self, *, requires_refresh: bool) -> None:
        if self._on_cities_changed is None:
            return
        try:
            self._on_cities_changed(requires_refresh)
        except Exception as error:  # noqa: BLE001 - keep the Settings page usable
            self.status_label.setText(
                f"{translate_text('Weather data source sync failed', self._language)}: {error}"
            )
