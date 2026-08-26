"""Visual tokens for the native Settings window."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette

_SETTINGS_THEME_COLORS = {
    "mist_blue": {
        "window": "#edf2f7", "base": "#ffffff", "alternate": "#f7fafc",
        "text": "#2b4257", "heading": "#20354a", "muted": "#718399",
        "accent": "#2b7ca7", "accent_soft": "#dcecf8", "border": "#dce4ed",
        "hover": "#e9f3fa", "hover_text": "#20354a",
        "accent_hover": "#236a91", "accent_hover_text": "#ffffff",
    },
    "mint_breeze": {
        "window": "#edf8f4", "base": "#ffffff", "alternate": "#f5fbf8",
        "text": "#263f3a", "heading": "#1d3832", "muted": "#5d776f",
        "accent": "#2f8b74", "accent_soft": "#d9f0e7", "border": "#c8e1d8",
        "hover": "#e7f5f0", "hover_text": "#1d3832",
        "accent_hover": "#26715e", "accent_hover_text": "#ffffff",
    },
    "almond_sand": {
        "window": "#fbf5e9", "base": "#fffefa", "alternate": "#fdf9f2",
        "text": "#493b30", "heading": "#3f3024", "muted": "#806e5d",
        "accent": "#a66f35", "accent_soft": "#f3e0c7", "border": "#e3d1b7",
        "hover": "#f7ecd9", "hover_text": "#3f3024",
        "accent_hover": "#8e5d2c", "accent_hover_text": "#fffefa",
    },
    "lavender_cloud": {
        "window": "#f5f1fb", "base": "#fffefe", "alternate": "#f9f7fd",
        "text": "#39334b", "heading": "#302941", "muted": "#706783",
        "accent": "#755ca9", "accent_soft": "#e8e0f7", "border": "#dcd2ed",
        "hover": "#efeafb", "hover_text": "#302941",
        "accent_hover": "#614b91", "accent_hover_text": "#fffefe",
    },
    "ocean_night": {
        "window": "#152030", "base": "#1d2b3e", "alternate": "#25364c",
        "text": "#e5f0f7", "heading": "#f6fbff", "muted": "#b5c8d7",
        "accent": "#4fa4cb", "accent_soft": "#294b61", "border": "#597999",
        "hover": "#2c4057", "hover_text": "#f6fbff",
        "accent_hover": "#6bb8dc", "accent_hover_text": "#152030",
    },
    "graphite_night": {
        "window": "#1e2128", "base": "#2a2e38", "alternate": "#333844",
        "text": "#eceff4", "heading": "#ffffff", "muted": "#c0c6d0",
        "accent": "#8fa7cc", "accent_soft": "#3e4655", "border": "#686f80",
        "hover": "#3b424f", "hover_text": "#ffffff",
        "accent_hover": "#abc0df", "accent_hover_text": "#1e2128",
    },
    "rose_dusk": {
        "window": "#301c2b", "base": "#3f2437", "alternate": "#4d2b42",
        "text": "#f9eaf0", "heading": "#fff6fa", "muted": "#d8b8c7",
        "accent": "#dc7d9d", "accent_soft": "#593347", "border": "#8b5a76",
        "hover": "#573145", "hover_text": "#fff6fa",
        "accent_hover": "#ee9fba", "accent_hover_text": "#301c2b",
    },
    "high_contrast": {
        "window": "#000000", "base": "#0e0e0e", "alternate": "#1b1b1b",
        "text": "#ffffff", "heading": "#ffffff", "muted": "#ededed",
        "accent": "#ffd640", "accent_soft": "#3d3514", "border": "#e6e6e6",
        "hover": "#ffd640", "hover_text": "#000000",
        "accent_hover": "#fff08a", "accent_hover_text": "#000000",
    },
    "terra_signal": {
        "window": "#181c1f", "base": "#23282a", "alternate": "#313739",
        "text": "#f1f2ec", "heading": "#fffef2", "muted": "#c4c9c3",
        "accent": "#e8d370", "accent_soft": "#4a4326", "border": "#899492",
        "hover": "#4a4326", "hover_text": "#fffef2",
        "accent_hover": "#f4e39a", "accent_hover_text": "#181c1f",
    },
    "endfield_industrial": {
        "window": "#1b272b", "base": "#26363a", "alternate": "#344749",
        "text": "#edf4f1", "heading": "#fffaf0", "muted": "#bbd0cb",
        "accent": "#ef9e4f", "accent_soft": "#523d29", "border": "#658d89",
        "hover": "#3e524f", "hover_text": "#fffaf0",
        "accent_hover": "#ffc078", "accent_hover_text": "#1b272b",
    },
    "starrail_astral": {
        "window": "#1c1d37", "base": "#2a2a4e", "alternate": "#3d3667",
        "text": "#f1effd", "heading": "#fff6dc", "muted": "#c8c5e0",
        "accent": "#7fdce5", "accent_soft": "#31335e", "border": "#847bb8",
        "hover": "#3d3d70", "hover_text": "#fff6dc",
        "accent_hover": "#a0edf2", "accent_hover_text": "#1c1d37",
    },
    "wuthering_tide": {
        "window": "#12232a", "base": "#1e363d", "alternate": "#2d4a50",
        "text": "#e9f6f4", "heading": "#f5fffd", "muted": "#b7d5d3",
        "accent": "#80e8dc", "accent_soft": "#28514f", "border": "#5e979c",
        "hover": "#32605d", "hover_text": "#f5fffd",
        "accent_hover": "#a7f5ed", "accent_hover_text": "#12232a",
    },
}


def _theme_colors(theme_key: str) -> dict[str, str]:
    return dict(_SETTINGS_THEME_COLORS.get(theme_key, _SETTINGS_THEME_COLORS["mist_blue"]))


def settings_palette(theme_key: str = "mist_blue") -> QPalette:
    """Return the selected palette explicitly, independent of Windows theme mode."""

    colors = _theme_colors(theme_key)
    palette = QPalette()
    active_roles = {
        QPalette.ColorRole.Window: colors["window"],
        QPalette.ColorRole.WindowText: colors["heading"],
        QPalette.ColorRole.Base: colors["base"],
        QPalette.ColorRole.AlternateBase: colors["alternate"],
        QPalette.ColorRole.ToolTipBase: colors["base"],
        QPalette.ColorRole.ToolTipText: colors["heading"],
        QPalette.ColorRole.Text: colors["text"],
        QPalette.ColorRole.Button: colors["base"],
        QPalette.ColorRole.ButtonText: colors["accent"],
        QPalette.ColorRole.BrightText: colors["base"],
        QPalette.ColorRole.Highlight: colors["accent"],
        QPalette.ColorRole.HighlightedText: colors["base"],
        QPalette.ColorRole.Link: colors["accent"],
        QPalette.ColorRole.PlaceholderText: colors["muted"],
    }
    for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
        for role, value in active_roles.items():
            palette.setColor(group, role, QColor(value))
    for role, value in {
        QPalette.ColorRole.WindowText: colors["muted"],
        QPalette.ColorRole.Text: colors["muted"],
        QPalette.ColorRole.ButtonText: colors["muted"],
        QPalette.ColorRole.PlaceholderText: colors["muted"],
    }.items():
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(value))
    return palette


SETTINGS_STYLESHEET = """
QMainWindow#settingsWindow {
    background: #edf2f7;
    color: #2b4257;
}
QWidget#settingsRoot {
    background: #edf2f7;
    color: #2b4257;
}
QWidget#settingsPage {
    background: #f6f8fb;
    color: #2b4257;
}
QScrollArea#settingsPageScrollArea {
    border: 0;
    background: #f6f8fb;
}
QScrollArea#settingsPageScrollArea > QWidget > QWidget {
    background: #f6f8fb;
}
QFrame#settingsHeader,
QFrame#settingsSidebar,
QFrame#settingsContent {
    background: #ffffff;
    border: 1px solid #dce4ed;
    border-radius: 16px;
}
QFrame#settingsHeader {
    min-height: 84px;
}
QFrame#settingsSidebar {
    background: #f8fafc;
}
QFrame#settingsContent {
    background: #f6f8fb;
}
QLabel#settingsEyebrow {
    color: #5f7f9e;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.6px;
}
QLabel#settingsTitle {
    color: #20354a;
    font-size: 25px;
    font-weight: 700;
}
QLabel#settingsSubtitle {
    color: #718399;
    font-size: 12px;
}
QLabel#settingsSectionTitle {
    color: #243b53;
    font-size: 21px;
    font-weight: 700;
}
QLabel#settingsSectionHint {
    color: #718399;
    font-size: 12px;
}
QLabel#settingsPage QLabel {
    background: transparent;
}
QListWidget#settingsNavigation {
    border: 0;
    background: transparent;
    outline: 0;
    padding: 8px;
    color: #52677d;
    font-size: 13px;
}
QListWidget#settingsNavigation::item {
    min-height: 38px;
    margin: 2px 0;
    padding: 0 12px;
    border-radius: 10px;
}
QListWidget#settingsNavigation::item:hover {
    background: #edf4fa;
    color: #2c6a93;
}
QListWidget#settingsNavigation::item:selected {
    background: #dcecf8;
    color: #1e5c86;
    font-weight: 700;
}
QGroupBox {
    margin-top: 15px;
    padding: 19px 14px 13px;
    border: 1px solid #dbe4ed;
    border-radius: 13px;
    background: #ffffff;
    color: #29445d;
    font-size: 13px;
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 13px;
    padding: 0 6px;
    background: #ffffff;
}
QLabel {
    color: #4a6076;
}
QPushButton {
    min-height: 30px;
    padding: 6px 13px;
    border: 1px solid #cbd8e5;
    border-radius: 8px;
    background: #ffffff;
    color: #2f506b;
}
QPushButton:hover {
    border-color: #8bb9d6;
    background: #f0f7fc;
}
QPushButton:pressed {
    background: #dcecf8;
}
QPushButton:disabled {
    color: #9aa9b7;
    background: #f0f3f6;
}
QPushButton[primary="true"] {
    border-color: #2b7ca7;
    background: #2b7ca7;
    color: #ffffff;
    font-weight: 700;
}
QPushButton[primary="true"]:hover {
    background: #236a91;
}
QComboBox,
QLineEdit,
QSpinBox,
QDateEdit,
QTimeEdit,
QDoubleSpinBox {
    min-height: 30px;
    padding: 4px 9px;
    border: 1px solid #cbd8e5;
    border-radius: 8px;
    background: #ffffff;
    color: #2b4257;
    selection-background-color: #b9dff2;
}
QComboBox:hover,
QLineEdit:hover,
QSpinBox:hover,
QDateEdit:hover,
QTimeEdit:hover,
QDoubleSpinBox:hover {
    border-color: #8bb9d6;
}
QComboBox:focus,
QLineEdit:focus,
QSpinBox:focus,
QDateEdit:focus,
QTimeEdit:focus,
QDoubleSpinBox:focus {
    border: 2px solid #4b9bc4;
    padding: 3px 8px;
}
QComboBox QAbstractItemView {
    border: 1px solid #cbd8e5;
    background: #ffffff;
    color: #2b4257;
    selection-background-color: #dcecf8;
    selection-color: #1e5c86;
}
QComboBox::drop-down {
    width: 26px;
    border: 0;
    background: #ffffff;
}
QComboBox::down-arrow {
    width: 8px;
    height: 8px;
    border-right: 2px solid #5f7f9e;
    border-bottom: 2px solid #5f7f9e;
}
QCheckBox,
QRadioButton {
    min-height: 27px;
    color: #405a70;
    spacing: 7px;
}
QCheckBox:focus,
QRadioButton:focus {
    color: #1e5c86;
}
QListWidget,
QTableWidget,
QTreeWidget {
    border: 1px solid #d5e0ea;
    border-radius: 10px;
    background: #ffffff;
    alternate-background-color: #f7fafc;
    color: #304a61;
}
QListWidget::item,
QTableWidget::item,
QTreeWidget::item {
    padding: 5px;
}
QListWidget::item:selected,
QTableWidget::item:selected,
QTreeWidget::item:selected {
    background: #dcecf8;
    color: #1e5c86;
}
QTableCornerButton::section {
    background: #f2f6f9;
    border: 0;
    border-bottom: 1px solid #d5e0ea;
}
QHeaderView::section {
    padding: 6px;
    border: 0;
    border-bottom: 1px solid #d5e0ea;
    background: #f2f6f9;
    color: #587086;
    font-weight: 700;
}
QTextBrowser,
QTextEdit,
QPlainTextEdit {
    border: 1px solid #d5e0ea;
    border-radius: 10px;
    background: #ffffff;
    color: #2b4257;
    selection-background-color: #b9dff2;
    selection-color: #1e5c86;
}
QTextBrowser {
    padding: 10px;
}
QTextBrowser a {
    color: #236a91;
}
QTabWidget::pane {
    border: 1px solid #d5e0ea;
    border-radius: 10px;
    background: #ffffff;
    top: -1px;
}
QTabWidget QStackedWidget,
QTabWidget QStackedWidget > QWidget {
    background: #ffffff;
    color: #2b4257;
}
QTabBar::tab {
    min-height: 30px;
    padding: 5px 12px;
    border: 1px solid transparent;
    border-bottom: 2px solid transparent;
    color: #587086;
    background: transparent;
}
QTabBar::tab:hover {
    color: #236a91;
    background: #edf4fa;
}
QTabBar::tab:selected {
    color: #1e5c86;
    border-bottom-color: #2b7ca7;
    font-weight: 700;
}
QDialog,
QMessageBox,
QInputDialog {
    background: #f6f8fb;
    color: #2b4257;
}
QMenu {
    border: 1px solid #cbd8e5;
    background: #ffffff;
    color: #2b4257;
}
QMenu::item:selected {
    background: #dcecf8;
    color: #1e5c86;
}
QScrollBar:vertical {
    width: 9px;
    margin: 4px 2px;
    background: transparent;
}
QScrollBar::handle:vertical {
    min-height: 28px;
    border-radius: 4px;
    background: #c4d2df;
}
QScrollBar::handle:vertical:hover {
    background: #99b6ca;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    height: 9px;
    margin: 2px 4px;
    background: transparent;
}
QScrollBar::handle:horizontal {
    min-width: 28px;
    border-radius: 4px;
    background: #c4d2df;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
}
"""


def settings_stylesheet(theme_key: str = "mist_blue") -> str:
    """Return theme-aware native colors and readable typography for Settings."""

    colors = _theme_colors(theme_key)
    return SETTINGS_STYLESHEET + f"""
QMainWindow#settingsWindow,
QWidget#settingsRoot {{ background: {colors['window']}; color: {colors['text']}; }}
QWidget#settingsPage,
QScrollArea#settingsPageScrollArea,
QScrollArea#settingsPageScrollArea > QWidget > QWidget,
QFrame#settingsContent {{ background: {colors['window']}; color: {colors['text']}; }}
QFrame#settingsHeader,
QFrame#settingsSidebar {{ background: {colors['base']}; border-color: {colors['border']}; }}
QLabel#settingsTitle,
QLabel#settingsSectionTitle {{ color: {colors['heading']}; }}
QLabel#settingsSubtitle,
QLabel#settingsSectionHint {{ color: {colors['muted']}; }}
QWidget#settingsRoot,
QWidget#settingsPage,
QFrame#settingsContent {{ font-size: 13px; }}
QGroupBox {{
    background: {colors['base']}; color: {colors['heading']};
    border-color: {colors['border']};
}}
QGroupBox::title {{ background: {colors['base']}; color: {colors['heading']}; }}
QLabel, QCheckBox, QRadioButton, QGroupBox, QListWidget, QTableWidget,
QTreeWidget {{ color: {colors['text']}; font-size: 13px; font-weight: 600; }}
QLabel#settingsTitle, QLabel#settingsSectionTitle {{
    color: {colors['heading']}; font-weight: 800;
}}
QLabel#settingsSubtitle, QLabel#settingsSectionHint {{ font-weight: 500; }}
QPushButton, QComboBox, QLineEdit, QSpinBox, QDateEdit, QTimeEdit,
QDoubleSpinBox, QAbstractSpinBox {{
    background: {colors['base']}; color: {colors['text']};
    border-color: {colors['border']}; font-size: 13px;
}}
QPushButton {{ font-weight: 600; }}
QPushButton[primary="true"] {{
    background: {colors['accent']}; color: {colors['base']};
    border-color: {colors['accent']}; font-weight: 800;
}}
QPushButton:hover, QComboBox:hover, QLineEdit:hover, QSpinBox:hover,
QDateEdit:hover, QTimeEdit:hover, QDoubleSpinBox:hover,
QAbstractSpinBox:hover {{
    background: {colors['hover']}; color: {colors['hover_text']};
    border-color: {colors['accent']};
}}
QPushButton[primary="true"]:hover {{
    background: {colors['accent_hover']}; color: {colors['accent_hover_text']};
    border-color: {colors['accent_hover']};
}}
QPushButton:disabled {{
    background: {colors['alternate']}; color: {colors['muted']};
    border-color: {colors['border']};
}}
QPushButton:pressed, QListWidget::item:selected, QTabBar::tab:selected {{
    background: {colors['accent_soft']}; color: {colors['heading']};
}}
QListWidget, QTableWidget, QTreeWidget {{
    background: {colors['base']}; alternate-background-color: {colors['alternate']};
    color: {colors['text']}; border-color: {colors['border']};
}}
QListWidget::item:selected, QTreeWidget::item:selected,
QTableWidget::item:selected {{
    background: {colors['accent']}; color: {colors['base']}; font-weight: 700;
}}
QHeaderView::section, QTableCornerButton::section {{
    background: {colors['alternate']}; color: {colors['heading']};
    border-color: {colors['border']}; font-weight: 800;
}}
QComboBox QAbstractItemView {{
    background: {colors['base']}; color: {colors['text']};
    selection-background-color: {colors['accent']};
    selection-color: {colors['base']};
}}
QComboBox::drop-down {{
    background: {colors['base']}; border-color: {colors['border']};
}}
QComboBox::drop-down:hover {{
    background: {colors['hover']};
}}
QComboBox::down-arrow {{
    border-right: 2px solid {colors['accent']};
    border-bottom: 2px solid {colors['accent']};
}}
QComboBox:hover::down-arrow {{
    border-right-color: {colors['hover_text']};
    border-bottom-color: {colors['hover_text']};
}}
QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{
    background: {colors['alternate']}; border-color: {colors['border']};
}}
QAbstractSpinBox::up-button:hover, QAbstractSpinBox::down-button:hover {{
    background: {colors['hover']};
}}
QAbstractSpinBox QLineEdit {{
    background: transparent; color: {colors['text']};
    border: 0; padding: 0;
}}
QAbstractSpinBox:hover QLineEdit {{
    color: {colors['hover_text']};
}}
QLineEdit, QSpinBox, QDateEdit, QTimeEdit {{
    selection-background-color: {colors['accent']};
    selection-color: {colors['base']};
}}
QDoubleSpinBox, QAbstractSpinBox {{
    selection-background-color: {colors['accent']};
    selection-color: {colors['base']};
}}
QTableWidget#timetableSchemePeriodTable {{
    background: {colors['base']}; color: {colors['text']};
    gridline-color: {colors['border']};
}}
QTableWidget#timetableSchemePeriodTable::item {{
    background: {colors['base']}; color: {colors['text']};
}}
QTableWidget#timetableSchemePeriodTable::item:alternate {{
    background: {colors['alternate']}; color: {colors['text']};
}}
QTableWidget#timetableSchemePeriodTable::item:selected {{
    background: {colors['accent']}; color: {colors['base']};
}}
QTableWidget#timetableSchemePeriodTable QTimeEdit,
QTableWidget#timetableSchemePeriodTable QAbstractSpinBox {{
    background: {colors['base']}; color: {colors['text']};
    border-color: {colors['border']}; font-size: 14px; font-weight: 600;
}}
QTableWidget#timetableSchemePeriodTable QTimeEdit:hover,
QTableWidget#timetableSchemePeriodTable QAbstractSpinBox:hover {{
    background: {colors['hover']}; color: {colors['hover_text']};
    border-color: {colors['accent']};
}}
QTableWidget#timetableSchemePeriodTable QTimeEdit QLineEdit,
QTableWidget#timetableSchemePeriodTable QAbstractSpinBox QLineEdit {{
    background: transparent; color: {colors['text']};
}}
QTableWidget#timetableSchemePeriodTable QTimeEdit:hover QLineEdit,
QTableWidget#timetableSchemePeriodTable QAbstractSpinBox:hover QLineEdit {{
    color: {colors['hover_text']};
}}
QTableWidget#timetableSchemePeriodTable QHeaderView::section {{
    background: {colors['alternate']}; color: {colors['heading']};
    border-color: {colors['border']}; font-weight: 800;
}}
QWidget#courseSettingsPage,
QWidget#courseSettingsPage QLabel,
QWidget#courseSettingsPage QCheckBox,
QWidget#courseSettingsPage QRadioButton,
QWidget#courseSettingsPage QGroupBox,
QWidget#courseSettingsPage QListWidget,
QWidget#courseSettingsPage QTableWidget,
QWidget#courseSettingsPage QComboBox,
QWidget#courseSettingsPage QLineEdit,
QWidget#courseSettingsPage QSpinBox,
QWidget#courseSettingsPage QDateEdit,
QWidget#courseSettingsPage QTimeEdit,
QWidget#courseSettingsPage QPushButton {{
    font-size: 14px;
}}
QWidget#courseSettingsPage QTabBar::tab {{
    min-height: 34px; padding: 6px 13px; font-size: 14px;
}}
QWidget#courseSettingsPage QTableWidget::item,
QWidget#courseSettingsPage QHeaderView::section {{
    font-size: 14px;
}}
QLabel#timetableSchemeStatus {{
    color: {colors['accent']}; font-size: 13px; font-weight: 700;
}}
QTabWidget::pane {{ background: {colors['base']}; border-color: {colors['border']}; }}
QTabWidget QStackedWidget, QTabWidget QStackedWidget > QWidget {{
    background: {colors['base']}; color: {colors['text']};
}}
QTextBrowser, QTextEdit, QPlainTextEdit {{ background: {colors['base']}; color: {colors['text']}; }}
"""
