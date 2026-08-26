"""Native Profile management page."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
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

from deskboard.models.profile import ProfileState, ProfileWidgetState
from deskboard.presentation.weather_presenter import (
    WEATHER_DISPLAY_MULTI_CITY,
    WEATHER_DISPLAY_SINGLE_CITY,
)
from deskboard.services.profile_service import ProfileError
from deskboard.ui.settings.i18n import SUPPORTED_LANGUAGES, translate_text

THEME_LABELS = {
    "mist_blue": "Mist Blue",
    "mint_breeze": "Mint Breeze",
    "almond_sand": "Almond Sand",
    "lavender_cloud": "Lavender Cloud",
    "ocean_night": "Ocean Night",
    "graphite_night": "Graphite Night",
    "rose_dusk": "Rose Dusk",
    "high_contrast": "High Contrast",
    "terra_signal": "Terra Signal",
    "endfield_industrial": "Frontier Foundry",
    "starrail_astral": "Astral Transit",
    "wuthering_tide": "Coastal Tide",
}
FONT_LABELS = {
    "system_ui": "System UI",
    "yahei": "Microsoft YaHei",
    "noto_sans": "Noto Sans",
    "source_han_sans": "Source Han Sans",
    "source_han_serif": "Source Han Serif",
}


class ProfilePage(QWidget):
    def __init__(
        self,
        profile_service: Any | None,
        *,
        on_profile_switched: Callable[[ProfileState], None] | None = None,
        on_profile_preview: Callable[[ProfileState], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = profile_service
        self._on_profile_switched = on_profile_switched
        self._on_profile_preview = on_profile_preview
        self._language = "zh_CN"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        heading = QLabel("Visual and spatial Dashboard Profiles", self)
        heading.setObjectName("settingsSectionTitle")
        layout.addWidget(heading)
        hint = QLabel(
            "Select a Profile first, then customize its Dashboard theme and font.",
            self,
        )
        hint.setObjectName("settingsSectionHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        profile_group = QGroupBox("Profiles", self)
        profile_layout = QVBoxLayout(profile_group)
        self.profile_list = QListWidget(self)
        self.profile_list.itemDoubleClicked.connect(lambda _item: self.switch_selected())
        self.profile_list.setMinimumHeight(108)
        self.profile_list.setMaximumHeight(170)
        self.profile_list.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        profile_layout.addWidget(self.profile_list)
        create_label = QLabel("New Profile name", profile_group)
        profile_layout.addWidget(create_label)
        create_row = QGridLayout()
        self.new_profile_name_input = QLineEdit(profile_group)
        self.new_profile_name_input.setPlaceholderText(
            "e.g. Work, Study, Evening"
        )
        self.create_profile_button = QPushButton("Create Profile", profile_group)
        self.create_profile_button.clicked.connect(
            lambda _checked=False: self.create_profile_from_input()
        )
        create_row.addWidget(self.new_profile_name_input, 0, 0)
        create_row.addWidget(self.create_profile_button, 0, 1)
        create_row.setColumnStretch(0, 1)
        profile_layout.addLayout(create_row)
        layout.addWidget(profile_group)

        appearance = QGroupBox("Dashboard theme and font", self)
        appearance.setObjectName("settingsAppearanceGroup")
        appearance_form = QFormLayout(appearance)
        self.theme_combo = QComboBox(appearance)
        self.theme_combo.setMinimumWidth(250)
        for key, label in THEME_LABELS.items():
            self.theme_combo.addItem(label, key)
        appearance_form.addRow("Theme", self.theme_combo)
        self.font_combo = QComboBox(appearance)
        self.font_combo.setMinimumWidth(250)
        for key, label in FONT_LABELS.items():
            self.font_combo.addItem(label, key)
        appearance_form.addRow("Font", self.font_combo)
        self.appearance_preview = QLabel(
            "Theme and font preview immediately; save Appearance to persist.",
            appearance,
        )
        self.appearance_preview.setWordWrap(True)
        appearance_form.addRow(self.appearance_preview)
        self.theme_combo.currentIndexChanged.connect(self._preview_appearance)
        self.font_combo.currentIndexChanged.connect(self._preview_appearance)
        layout.addWidget(appearance)
        self.save_appearance_button = QPushButton("Save Appearance", self)
        self.save_appearance_button.clicked.connect(
            lambda _checked=False: self.save_appearance()
        )
        self.save_appearance_button.setProperty("primary", True)
        layout.addWidget(self.save_appearance_button)

        weather_group = QGroupBox("Weather display mode for this Profile", self)
        weather_layout = QVBoxLayout(weather_group)
        self.weather_mode_combo = QComboBox(weather_group)
        self.weather_mode_combo.setMinimumWidth(250)
        self.weather_mode_combo.addItem(
            "Primary city detail",
            WEATHER_DISPLAY_SINGLE_CITY,
        )
        self.weather_mode_combo.addItem(
            "Multi-city summary",
            WEATHER_DISPLAY_MULTI_CITY,
        )
        weather_layout.addWidget(self.weather_mode_combo)
        self.save_weather_mode_button = QPushButton(
            "Save Weather Display", weather_group
        )
        self.save_weather_mode_button.clicked.connect(
            lambda _checked=False: self.save_weather_display_mode()
        )
        weather_layout.addWidget(self.save_weather_mode_button)
        layout.addWidget(weather_group)

        self.status_label = QLabel(self)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        actions_layout = QGridLayout()
        actions_layout.setHorizontalSpacing(8)
        actions_layout.setVerticalSpacing(8)
        buttons = (
            ("Switch", self.switch_selected),
            ("Save Current", self.save_current),
            ("Save As", self.save_as_profile),
            ("Rename", self.rename_profile),
            ("Delete", self.delete_selected),
            ("Restore Default", self.restore_default),
        )
        for index, (title, callback) in enumerate(buttons):
            button = QPushButton(title, self)
            button.clicked.connect(
                lambda _checked=False, callback=callback: callback()
            )
            actions_layout.addWidget(button, index // 2, index % 2)
        layout.addLayout(actions_layout)
        layout.addStretch(1)
        self.refresh()

    def refresh(self) -> None:
        if self._service is None:
            self.profile_list.clear()
            self.weather_mode_combo.setEnabled(False)
            self.save_weather_mode_button.setEnabled(False)
            self.save_appearance_button.setEnabled(False)
            self.new_profile_name_input.setEnabled(False)
            self.create_profile_button.setEnabled(False)
            self.status_label.setText(
                translate_text("Profile service unavailable", self._language)
            )
            return
        active_id = self._service.active_profile_id
        self.profile_list.clear()
        profiles = self._service.list_profiles()
        for profile in profiles:
            item = QListWidgetItem(profile.name, self.profile_list)
            item.setData(Qt.ItemDataRole.UserRole, profile.id)
            item.setToolTip(
                translate_text(
                    "Built-in Default" if profile.is_builtin else "User Profile",
                    self._language,
                )
            )
            if profile.id == active_id:
                self.profile_list.setCurrentItem(item)
        self.weather_mode_combo.setEnabled(True)
        self.save_weather_mode_button.setEnabled(True)
        self.save_appearance_button.setEnabled(True)
        self.new_profile_name_input.setEnabled(True)
        self.create_profile_button.setEnabled(True)
        state = self._service.current_profile.state
        self._set_weather_mode(self._weather_mode(state))
        self._set_visual_state(state)
        self._notify_profile_preview(state)
        self.status_label.setText(
            f"{len(profiles)} 个配置方案"
            if self._language == "zh_CN"
            else f"{len(profiles)} Profiles"
        )

    def set_language(self, language: str) -> None:
        if language not in SUPPORTED_LANGUAGES:
            return
        self._language = language
        self.refresh()

    def switch_selected(self) -> bool:
        profile = self._selected_profile()
        if profile is None:
            return False
        try:
            state = self._service.switch(profile.id)
        except (LookupError, TypeError, ValueError) as error:
            return self._failed(error)
        self._notify_profile_changed(state)
        self.refresh()
        return True

    def save_current(self) -> bool:
        if self._service is None:
            return False
        try:
            self._service.save_current(self._service.current_profile.state)
        except ProfileError:
            return self.save_as_profile(name=self._pending_profile_name())
        except (LookupError, TypeError, ValueError) as error:
            return self._failed(error)
        self.refresh()
        return True

    def save_as_profile(
        self,
        name: str | None = None,
        *,
        state: ProfileState | None = None,
    ) -> bool:
        if self._service is None:
            return False
        name = self._name_input("Save As Profile", name)
        if name is None:
            return False
        selected_state = state or self._service.current_profile.state
        try:
            profile = self._service.save_as(name, selected_state)
        except (LookupError, TypeError, ValueError) as error:
            return self._failed(error)
        self._notify_profile_changed(profile.state)
        self.new_profile_name_input.clear()
        self.refresh()
        return True

    def save_weather_display_mode(self) -> bool:
        if self._service is None:
            return False
        state = self._with_weather_mode(
            self._service.current_profile.state,
            self._selected_weather_mode(),
        )
        try:
            self._service.save_current(state)
        except ProfileError:
            return self.save_as_profile(
                name=self._pending_profile_name(),
                state=state,
            )
        except (LookupError, TypeError, ValueError) as error:
            return self._failed(error)
        self._notify_profile_changed(state)
        self.refresh()
        return True

    def save_appearance(self) -> bool:
        if self._service is None:
            return False
        state = replace(
            self._service.current_profile.state,
            theme_key=self._selected_theme(),
            font_key=self._selected_font(),
        )
        try:
            self._service.save_current(state)
        except ProfileError:
            return self.save_as_profile(
                name=self._pending_profile_name(),
                state=state,
            )
        except (LookupError, TypeError, ValueError) as error:
            return self._failed(error)
        self._notify_profile_changed(state)
        self.refresh()
        return True

    def create_profile_from_input(self) -> bool:
        """Create a user Profile without hiding the action behind a dialog."""

        if self._service is None:
            return False
        name = self._pending_profile_name()
        if name is None:
            self.status_label.setText(
                translate_text("Enter a name for the new Profile", self._language)
            )
            return False
        state = replace(
            self._service.current_profile.state,
            theme_key=self._selected_theme(),
            font_key=self._selected_font(),
        )
        return self.save_as_profile(name=name, state=state)

    def rename_profile(self, name: str | None = None) -> bool:
        profile = self._selected_profile()
        if profile is None or self._service is None:
            return False
        name = self._name_input("Rename Profile", name)
        if name is None:
            return False
        try:
            self._service.rename(profile.id, name)
        except (LookupError, TypeError, ValueError) as error:
            return self._failed(error)
        self.refresh()
        return True

    def delete_selected(self) -> bool:
        profile = self._selected_profile()
        if profile is None or self._service is None:
            return False
        answer = QMessageBox.question(
            self.window(),
            translate_text("Delete Profile", self._language),
            (
                f"删除配置方案 {profile.name}？"
                if self._language == "zh_CN"
                else f"Delete Profile {profile.name}?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return False
        try:
            self._service.delete(profile.id)
        except (LookupError, TypeError, ValueError) as error:
            return self._failed(error)
        self._notify_profile_changed(self._service.current_profile.state)
        self.refresh()
        return True

    def restore_default(self) -> bool:
        if self._service is None:
            return False
        try:
            state = self._service.restore_default()
        except (LookupError, TypeError, ValueError) as error:
            return self._failed(error)
        self._notify_profile_changed(state)
        self.refresh()
        return True

    def _selected_profile(self):
        if self._service is None or self.profile_list.currentItem() is None:
            return None
        profile_id = self.profile_list.currentItem().data(Qt.ItemDataRole.UserRole)
        return self._service.get(int(profile_id))

    def _name_input(self, title: str, name: str | None) -> str | None:
        if name is not None:
            return name.strip() or None
        value, accepted = QInputDialog.getText(
            self.window(),
            translate_text(title, self._language),
            translate_text("Profile name:", self._language),
        )
        return value.strip() if accepted and value.strip() else None

    def _pending_profile_name(self) -> str | None:
        value = self.new_profile_name_input.text().strip()
        return value or None

    def _notify_profile_changed(self, state: ProfileState) -> None:
        if self._on_profile_switched is not None:
            self._on_profile_switched(state)

    def _notify_profile_preview(self, state: ProfileState) -> None:
        if self._on_profile_preview is None:
            return
        try:
            self._on_profile_preview(state)
        except Exception as error:  # noqa: BLE001 - keep Settings usable
            self.status_label.setText(
                f"{translate_text('Dashboard preview failed', self._language)}: {error}"
            )

    def _preview_appearance(self, _index: int) -> None:
        if self._service is None or not hasattr(self, "status_label"):
            return
        state = replace(
            self._service.current_profile.state,
            theme_key=self._selected_theme(),
            font_key=self._selected_font(),
        )
        self._notify_profile_preview(state)
        self.status_label.setText(
            translate_text(
                "Preview applied; click Save Appearance to persist.", self._language
            )
        )

    def _selected_weather_mode(self) -> str:
        value = self.weather_mode_combo.currentData()
        return (
            value
            if isinstance(value, str)
            and value in {WEATHER_DISPLAY_SINGLE_CITY, WEATHER_DISPLAY_MULTI_CITY}
            else WEATHER_DISPLAY_SINGLE_CITY
        )

    def _set_weather_mode(self, mode: str) -> None:
        index = self.weather_mode_combo.findData(mode)
        self.weather_mode_combo.setCurrentIndex(index if index >= 0 else 0)

    def _set_visual_state(self, state: ProfileState) -> None:
        theme_index = self.theme_combo.findData(state.theme_key)
        font_index = self.font_combo.findData(state.font_key)
        with QSignalBlocker(self.theme_combo), QSignalBlocker(self.font_combo):
            self.theme_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)
            self.font_combo.setCurrentIndex(font_index if font_index >= 0 else 0)

    def _selected_theme(self) -> str:
        value = self.theme_combo.currentData()
        return value if isinstance(value, str) and value in THEME_LABELS else "mist_blue"

    def _selected_font(self) -> str:
        value = self.font_combo.currentData()
        return value if isinstance(value, str) and value in FONT_LABELS else "system_ui"

    @staticmethod
    def _weather_mode(state: ProfileState) -> str:
        for widget in state.widgets:
            if widget.widget_key != "weather":
                continue
            value = widget.config.get("displayMode", widget.config.get("display_mode"))
            if isinstance(value, str) and value in {
                WEATHER_DISPLAY_SINGLE_CITY,
                WEATHER_DISPLAY_MULTI_CITY,
            }:
                return value
        return WEATHER_DISPLAY_SINGLE_CITY

    @staticmethod
    def _with_weather_mode(state: ProfileState, mode: str) -> ProfileState:
        widgets = []
        found = False
        for widget in state.widgets:
            if widget.widget_key != "weather":
                widgets.append(widget)
                continue
            config = dict(widget.config)
            config["displayMode"] = mode
            widgets.append(replace(widget, config=config))
            found = True
        if not found:
            widgets.append(
                ProfileWidgetState(
                    widget_key="weather",
                    visible=True,
                    x=0,
                    y=12,
                    w=48,
                    h=3,
                    config={"displayMode": mode},
                )
            )
        return replace(state, widgets=tuple(widgets))

    def _failed(self, error: Exception) -> bool:
        self.status_label.setText(str(error))
        return False
