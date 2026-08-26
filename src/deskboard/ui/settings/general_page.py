"""Native General Settings page."""

from __future__ import annotations

from typing import Protocol

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from deskboard.app.modes import AppMode
from deskboard.ui.settings.i18n import (
    SUPPORTED_LANGUAGES,
    current_mode_text,
    translate_text,
)


class AutostartLike(Protocol):
    def is_enabled(self) -> bool: ...

    def set_enabled(self, enabled: bool) -> None: ...


class GeneralPage(QWidget):
    language_changed = Signal(str)

    def __init__(
        self,
        set_mode,
        show_dashboard,
        hide_dashboard,
        exit_application,
        *,
        autostart: AutostartLike | None = None,
        settings_service=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._set_mode = set_mode
        self._autostart = autostart
        self._settings_service = settings_service
        stored_language = getattr(settings_service, "ui_language", "zh_CN")
        self._language = (
            stored_language if stored_language in SUPPORTED_LANGUAGES else "zh_CN"
        )
        self._mode = AppMode.INTERACTION
        self._autostart_status_key = "Autostart unavailable"
        self._autostart_error: str | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Dashboard visibility and daily mode", self))

        visibility = QGroupBox("Dashboard", self)
        visibility_layout = QVBoxLayout(visibility)
        show_button = QPushButton("Show Dashboard", visibility)
        show_button.clicked.connect(show_dashboard)
        hide_button = QPushButton("Hide Dashboard", visibility)
        hide_button.clicked.connect(hide_dashboard)
        visibility_layout.addWidget(show_button)
        visibility_layout.addWidget(hide_button)
        layout.addWidget(visibility)

        modes = QGroupBox("Mode", self)
        mode_form = QFormLayout(modes)
        self.locked_button = QRadioButton("Locked", modes)
        self.interaction_button = QRadioButton("Interaction", modes)
        self.locked_button.clicked.connect(lambda: self._set_mode(AppMode.LOCKED))
        self.interaction_button.clicked.connect(lambda: self._set_mode(AppMode.INTERACTION))
        mode_form.addRow(self.locked_button)
        mode_form.addRow(self.interaction_button)
        self.mode_label = QLabel(
            current_mode_text(AppMode.INTERACTION, self._language), modes
        )
        mode_form.addRow(self.mode_label)
        layout.addWidget(modes)

        preferences = QGroupBox("Preferences", self)
        preferences_form = QFormLayout(preferences)
        self.language_combo = QComboBox(preferences)
        self.language_combo.addItem("简体中文", "zh_CN")
        self.language_combo.addItem("English", "en_US")
        if settings_service is not None:
            stored_language = settings_service.ui_language
            index = self.language_combo.findData(stored_language)
            with QSignalBlocker(self.language_combo):
                self.language_combo.setCurrentIndex(index if index >= 0 else 0)
        self.language_combo.currentIndexChanged.connect(self._language_toggled)
        preferences_form.addRow("Language", self.language_combo)
        layout.addWidget(preferences)

        self.layout_edit_button = QPushButton("Enter Layout Edit", self)
        self.layout_edit_button.clicked.connect(lambda: self._set_mode(AppMode.LAYOUT_EDIT))
        layout.addWidget(self.layout_edit_button)

        self.autostart_checkbox = QCheckBox("Start DeskBoard with Windows", self)
        self.autostart_status = QLabel(self)
        self.autostart_checkbox.toggled.connect(self._autostart_toggled)
        layout.addWidget(self.autostart_checkbox)
        layout.addWidget(self.autostart_status)
        if autostart is None:
            self.autostart_checkbox.setEnabled(False)
            self._set_autostart_status()
        else:
            self.autostart_checkbox.setChecked(bool(autostart.is_enabled()))
            self._autostart_status_key = (
                "Autostart enabled"
                if self.autostart_checkbox.isChecked()
                else "Autostart disabled"
            )
            self._set_autostart_status()

        self.exit_button = QPushButton("Exit DeskBoard", self)
        self.exit_button.clicked.connect(exit_application)
        layout.addWidget(self.exit_button)
        layout.addStretch(1)

    def set_mode_state(self, mode: AppMode) -> None:
        if not isinstance(mode, AppMode):
            raise TypeError("mode must be an AppMode")
        self._mode = mode
        self._set_mode_label(mode)
        self.locked_button.setChecked(mode is AppMode.LOCKED)
        self.interaction_button.setChecked(mode is AppMode.INTERACTION)

    def set_language(self, language: str) -> None:
        index = self.language_combo.findData(language)
        if index < 0:
            return
        self._language = language
        with QSignalBlocker(self.language_combo):
            self.language_combo.setCurrentIndex(index)
        self._set_mode_label(self._mode)
        self._set_autostart_status()

    def _language_toggled(self, _index: int) -> None:
        language = self.language_combo.currentData()
        if not isinstance(language, str):
            return
        try:
            if self._settings_service is not None:
                language = self._settings_service.set_ui_language(language)
        except (TypeError, ValueError) as error:
            self._autostart_error = str(error)
            self._set_autostart_status()
            return
        self.language_changed.emit(language)

    def _autostart_toggled(self, enabled: bool) -> None:
        if self._autostart is None:
            return
        previous = not enabled
        try:
            self._autostart.set_enabled(enabled)
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            with QSignalBlocker(self.autostart_checkbox):
                self.autostart_checkbox.setChecked(previous)
            self._autostart_status_key = "Autostart unavailable"
            self._autostart_error = str(error)
        else:
            self._autostart_status_key = (
                "Autostart enabled" if enabled else "Autostart disabled"
            )
            self._autostart_error = None
        self._set_autostart_status()

    def _set_mode_label(self, mode: AppMode) -> None:
        source = f"Current mode: {mode.value}"
        self.mode_label.setProperty("_deskboard_i18n_source", source)
        self.mode_label.setText(current_mode_text(mode, self._language))

    def _set_autostart_status(self) -> None:
        message = translate_text(self._autostart_status_key, self._language)
        if self._autostart_error:
            message = f"{message}: {self._autostart_error}"
        self.autostart_status.setProperty("_deskboard_i18n_source", None)
        self.autostart_status.setText(message)
