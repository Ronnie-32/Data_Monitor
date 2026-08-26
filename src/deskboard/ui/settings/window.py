"""Native eight-page Settings shell."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from deskboard.app.modes import AppMode
from deskboard.ui.settings.about_page import AboutPage
from deskboard.ui.settings.course_page import CoursePage
from deskboard.ui.settings.data_status_page import DataStatusPage
from deskboard.ui.settings.finance_page import FinancePage
from deskboard.ui.settings.general_page import GeneralPage
from deskboard.ui.settings.i18n import (
    SUPPORTED_LANGUAGES,
    translate_text,
    translate_widget_tree,
)
from deskboard.ui.settings.profile_page import ProfilePage
from deskboard.ui.settings.style import (
    settings_palette,
    settings_stylesheet,
)
from deskboard.ui.settings.weather_page import WeatherPage

if TYPE_CHECKING:
    from deskboard.infrastructure.clock import Clock
    from deskboard.ui.settings.todo_page import TodoManagementService, TodoPage


class SettingsWindow(QMainWindow):
    PAGE_TITLES = (
        "General",
        "Profiles",
        "Weather",
        "Finance",
        "Todo",
        "Courses",
        "Data Status",
        "About",
    )

    def __init__(
        self,
        set_mode: Callable[[AppMode], None],
        show_dashboard: Callable[[], None],
        hide_dashboard: Callable[[], None],
        exit_application: Callable[[], None],
        *,
        todo_service: TodoManagementService | None = None,
        clock: Clock | None = None,
        on_todos_changed: Callable[[], None] | None = None,
        settings_service=None,
        profile_service=None,
        weather_service=None,
        finance_service=None,
        course_service=None,
        refresh_service=None,
        log_directory=None,
        source_metadata=None,
        display_names=None,
        autostart=None,
        on_profile_switched=None,
        on_profile_preview=None,
        on_language_changed=None,
        on_weather_cities_changed: Callable[[bool], object] | None = None,
        on_course_data_changed: Callable[[], object] | None = None,
        weather_location_catalog=None,
    ) -> None:
        super().__init__()
        self._set_mode = set_mode
        self.todo_page: TodoPage | None = None
        self.general_page: GeneralPage
        self.profile_page: ProfilePage
        self.weather_page: WeatherPage
        self.finance_page: FinancePage
        self.course_page: CoursePage
        self.data_status_page: DataStatusPage
        self.about_page: AboutPage
        self._settings_service = settings_service
        self._external_profile_preview = on_profile_preview
        self._external_language_changed = on_language_changed
        self._language = (
            settings_service.ui_language
            if settings_service is not None
            else "zh_CN"
        )
        if self._language not in SUPPORTED_LANGUAGES:
            self._language = "zh_CN"
        self.setObjectName("settingsWindow")
        self.setWindowTitle("DeskBoard Settings")
        self.resize(1040, 700)
        self.setMinimumSize(880, 600)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self._preview_theme_key = "mist_blue"
        self.setAutoFillBackground(True)
        self.setStyleSheet(settings_stylesheet(self._preview_theme_key))
        self.setPalette(settings_palette(self._preview_theme_key))

        root = QWidget(self)
        root.setObjectName("settingsRoot")
        outer_layout = QVBoxLayout(root)
        outer_layout.setContentsMargins(18, 18, 18, 18)
        outer_layout.setSpacing(14)

        header = QFrame(root)
        header.setObjectName("settingsHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 15, 18, 15)
        header_layout.setSpacing(12)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        eyebrow = QLabel("DESKBOARD", header)
        eyebrow.setObjectName("settingsEyebrow")
        self.header_title = QLabel("DeskBoard Settings", header)
        self.header_title.setObjectName("settingsTitle")
        self.header_subtitle = QLabel(
            "Local preferences, Profiles, and data sources", header
        )
        self.header_subtitle.setObjectName("settingsSubtitle")
        title_layout.addWidget(eyebrow)
        title_layout.addWidget(self.header_title)
        title_layout.addWidget(self.header_subtitle)
        header_layout.addLayout(title_layout, 1)
        language_layout = QVBoxLayout()
        language_layout.setSpacing(4)
        language_label = QLabel("Language", header)
        language_layout.addWidget(language_label, 0, Qt.AlignmentFlag.AlignRight)
        self.language_combo = QComboBox(header)
        self.language_combo.setMinimumWidth(150)
        self.language_combo.addItem("Simplified Chinese", "zh_CN")
        self.language_combo.addItem("English", "en_US")
        language_layout.addWidget(self.language_combo)
        header_layout.addLayout(language_layout)
        outer_layout.addWidget(header)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(14)
        sidebar = QFrame(root)
        sidebar.setObjectName("settingsSidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 12, 8, 12)
        sidebar_layout.setSpacing(5)
        self.navigation = QListWidget(sidebar)
        self.navigation.setObjectName("settingsNavigation")
        self.pages = QStackedWidget(root)
        self.pages.setObjectName("settingsPages")
        self.navigation.setFixedWidth(190)
        for title in self.PAGE_TITLES:
            self.navigation.addItem(title)
            if title == "General":
                page = GeneralPage(
                    set_mode,
                    show_dashboard,
                    hide_dashboard,
                    exit_application,
                    autostart=autostart,
                    settings_service=settings_service,
                    parent=self.pages,
                )
                self.general_page = page
            elif title == "Profiles":
                page = ProfilePage(
                    profile_service,
                    on_profile_switched=on_profile_switched,
                    on_profile_preview=self._preview_profile_state,
                    parent=self.pages,
                )
                self.profile_page = page
            elif title == "Weather":
                page = WeatherPage(
                    weather_service,
                    location_catalog=weather_location_catalog,
                    on_cities_changed=on_weather_cities_changed,
                    parent=self.pages,
                )
                self.weather_page = page
            elif title == "Finance":
                page = FinancePage(finance_service, parent=self.pages)
                self.finance_page = page
            elif title == "Todo" and todo_service is not None and clock is not None:
                from deskboard.ui.settings.todo_page import TodoPage

                self.todo_page = TodoPage(
                    todo_service,
                    clock,
                    self,
                    on_changed=on_todos_changed,
                )
                page = self.todo_page
            elif title == "Courses":
                page = CoursePage(
                    course_service,
                    settings_service,
                    clock,
                    on_changed=on_course_data_changed,
                    parent=self.pages,
                )
                self.course_page = page
            elif title == "Data Status":
                page = DataStatusPage(
                    refresh_service,
                    log_directory,
                    source_metadata=source_metadata,
                    display_names=display_names,
                    parent=self.pages,
                )
                self.data_status_page = page
            elif title == "About":
                page = AboutPage(parent=self.pages)
                self.about_page = page
            else:
                page = self._build_page(
                    title,
                    show_dashboard,
                    hide_dashboard,
                    exit_application,
                )
            self.pages.addWidget(self._scroll_page(page))
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.setCurrentRow(0)
        sidebar_layout.addWidget(self.navigation, 1)
        body_layout.addWidget(sidebar)
        content = QFrame(root)
        content.setObjectName("settingsContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 16, 18, 16)
        content_layout.addWidget(self.pages)
        body_layout.addWidget(content, 1)
        outer_layout.addLayout(body_layout, 1)
        self.setCentralWidget(root)
        self.mode_label = self.general_page.mode_label
        self.language_combo.currentIndexChanged.connect(self._header_language_changed)
        self.general_page.language_changed.connect(self._general_language_changed)
        self.set_language(self._language)

    def _scroll_page(self, page: QWidget) -> QScrollArea:
        """Keep long native pages usable at normal laptop resolutions."""

        page.setObjectName(page.objectName() or "settingsPage")
        page.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        page.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        scroll_area = QScrollArea(self.pages)
        scroll_area.setObjectName("settingsPageScrollArea")
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll_area.setWidget(page)
        return scroll_area

    def _build_page(
        self,
        title: str,
        show_dashboard: Callable[[], None],
        hide_dashboard: Callable[[], None],
        exit_application: Callable[[], None],
    ) -> QWidget:
        page = QWidget(self.pages)
        layout = QVBoxLayout(page)
        heading = QLabel(title, page)
        heading.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(heading)
        if title == "General":
            layout.addWidget(QLabel("Dashboard visibility and shell mode", page))
            for label, callback in (
                ("Show Dashboard", show_dashboard),
                ("Hide Dashboard", hide_dashboard),
                ("Locked", lambda: self._set_mode(AppMode.LOCKED)),
                ("Interaction", lambda: self._set_mode(AppMode.INTERACTION)),
                ("Layout Edit", lambda: self._set_mode(AppMode.LAYOUT_EDIT)),
                ("Exit DeskBoard", exit_application),
            ):
                button = QPushButton(label, page)
                button.clicked.connect(callback)
                layout.addWidget(button)
            self.mode_label = QLabel(page)
            layout.addWidget(self.mode_label)
        else:
            layout.addWidget(QLabel("This page is a native shell for a later task.", page))
        layout.addStretch(1)
        return page

    def set_mode_state(self, mode: AppMode) -> None:
        self.general_page.set_mode_state(mode)

    def set_language(self, language: str) -> None:
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported Settings language: {language}")
        self._language = language
        index = self.language_combo.findData(language)
        if index >= 0:
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)
        translate_widget_tree(self, language)
        for page in (
            self.general_page,
            self.profile_page,
            self.weather_page,
            self.finance_page,
            self.todo_page,
            self.course_page,
            self.data_status_page,
        ):
            setter = getattr(page, "set_language", None)
            if callable(setter):
                setter(language)
        self.about_page.set_language(language)
        self.setWindowTitle(translate_text("DeskBoard Settings", language))

    def _preview_profile_state(self, state) -> None:
        """Apply one transient theme to native Settings and Dashboard together."""

        theme_key = getattr(state, "theme_key", "mist_blue")
        if not isinstance(theme_key, str):
            theme_key = "mist_blue"
        self._preview_theme_key = theme_key
        self.setStyleSheet(settings_stylesheet(theme_key))
        self.setPalette(settings_palette(theme_key))
        if self._external_profile_preview is not None:
            self._external_profile_preview(state)

    def restore_saved_profile_preview(self) -> None:
        if getattr(self, "profile_page", None) is None:
            return
        service = getattr(self.profile_page, "_service", None)
        if service is not None:
            self._preview_profile_state(service.current_profile.state)

    def _header_language_changed(self, _index: int) -> None:
        language = self.language_combo.currentData()
        if not isinstance(language, str):
            return
        if self._settings_service is not None:
            try:
                language = self._settings_service.set_ui_language(language)
            except (TypeError, ValueError):
                return
        self.set_language(language)
        self._notify_language_changed(language)

    def _general_language_changed(self, language: str) -> None:
        if self._settings_service is not None:
            language = self._settings_service.set_ui_language(language)
        self.set_language(language)
        self._notify_language_changed(language)

    def _notify_language_changed(self, language: str) -> None:
        if self._external_language_changed is None:
            return
        try:
            self._external_language_changed(language)
        except Exception:  # noqa: BLE001 - language switching must remain usable
            pass

    def open_todo_editor(self, todo_id: int) -> bool:
        if self.todo_page is None:
            return False
        return self.todo_page.open_editor(todo_id)

    def request_delete_todo(self, todo_id: int) -> bool:
        if self.todo_page is None:
            return False
        return self.todo_page.delete_todo(todo_id)

    def showEvent(self, event) -> None:  # noqa: N802
        self.profile_page.refresh()
        self.weather_page.refresh()
        self.finance_page.refresh()
        if self.todo_page is not None:
            self.todo_page.refresh()
        self.course_page.refresh()
        self.data_status_page.refresh()
        self.set_language(self._language)
        super().showEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802
        # Theme/font changes are transient until Save Appearance.  Closing the
        # window therefore restores the persisted Profile before it can be
        # shown again, including the Dashboard mirror.
        self.restore_saved_profile_preview()
        super().closeEvent(event)
