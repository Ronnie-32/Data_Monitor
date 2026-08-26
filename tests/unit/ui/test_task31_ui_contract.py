from pathlib import Path

from deskboard.app.modes import AppMode
from deskboard.ui.dashboard.window import (
    HTCAPTION,
    layout_toolbar_control_rects,
    native_hit_test,
)
from deskboard.ui.settings.profile_page import THEME_LABELS
from deskboard.ui.settings.style import settings_stylesheet

WEB_ROOT = Path("src/deskboard/ui/dashboard/web")


def test_layout_toolbar_is_inside_shell_bar_and_reserved_from_native_dragging():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    css = (WEB_ROOT / "css/layout.css").read_text(encoding="utf-8")
    javascript = (WEB_ROOT / "js/layout.js").read_text(encoding="utf-8")
    app = (WEB_ROOT / "js/app.js").read_text(encoding="utf-8")
    bridge = Path("src/deskboard/ui/dashboard/bridge.py").read_text(encoding="utf-8")
    window = Path("src/deskboard/ui/dashboard/window.py").read_text(encoding="utf-8")
    toolbar_start = html.index('id="layout-toolbar"')
    shell_start = html.index('<header class="shell-bar">')
    network_start = html.index('class="network-status"')

    assert shell_start < toolbar_start < network_start
    assert 'class="layout-toolbar-actions"' in html
    assert ".layout-toolbar" in css
    assert "position: static" in css
    assert 'body[data-mode="layout_edit"] .shell-title' in css
    assert 'body[data-mode="layout_edit"] .settings-button' in css
    assert "grid-template-rows" in css
    assert "flex-wrap: wrap" in css
    assert "overflow-x: hidden" in css
    assert "overflow-x: auto" not in css
    assert "pointerdown" in javascript
    assert "beginWindowDrag" in javascript
    assert "store.getState().app" in app
    assert "windowDragRequested" in bridge
    assert "def beginWindowDrag" in bridge
    assert "WM_NCLBUTTONDOWN" in window

    toolbar_controls = layout_toolbar_control_rects(1200)
    action_rect, visibility_rect = toolbar_controls
    assert native_hit_test(
        AppMode.LAYOUT_EDIT,
        (action_rect[0] + action_rect[2]) // 2,
        (action_rect[1] + action_rect[3]) // 2,
        (0, 0, 1200, 800),
        toolbar_rects=toolbar_controls,
    ) is None
    assert native_hit_test(
        AppMode.LAYOUT_EDIT,
        action_rect[0] - 12,
        action_rect[1] + 12,
        (0, 0, 1200, 800),
        toolbar_rects=toolbar_controls,
    ) == HTCAPTION
    assert native_hit_test(
        AppMode.LAYOUT_EDIT,
        (visibility_rect[0] + visibility_rect[2]) // 2,
        (visibility_rect[1] + visibility_rect[3]) // 2,
        (0, 0, 1200, 800),
        toolbar_rects=toolbar_controls,
    ) is None

    compact_controls = layout_toolbar_control_rects(400)
    compact_action, compact_visibility = compact_controls
    assert compact_action[0] < compact_action[2]
    assert compact_visibility[1] > compact_action[1]
    assert native_hit_test(
        AppMode.LAYOUT_EDIT,
        (compact_action[0] + compact_action[2]) // 2,
        compact_action[1] + 10,
        (0, 0, 400, 800),
        toolbar_rects=compact_controls,
    ) is None
    assert native_hit_test(
        AppMode.LAYOUT_EDIT,
        compact_action[0] - 8,
        compact_action[1] + 10,
        (0, 0, 400, 800),
        toolbar_rects=compact_controls,
    ) == HTCAPTION


def test_courses_settings_exposes_scheme_crud_and_semester_binding_controls():
    source = Path("src/deskboard/ui/settings/course_page.py").read_text(encoding="utf-8")

    for marker in (
        "timetableSchemeList",
        "timetableSchemeAxisModeCombo",
        "timetableSchemePeriodCount",
        "timetableSchemePeriodTable",
        "bind_selected_semester_scheme",
        "save_timetable_scheme",
        "delete_timetable_scheme",
    ):
        assert marker in source


def test_settings_dark_theme_keeps_table_text_and_controls_contrast_safe():
    css = settings_stylesheet("starrail_astral")

    assert "QTableWidget::item:selected" in css
    assert "QHeaderView::section" in css
    assert "font-weight: 600" in css
    assert "color: #f1effd" in css
    assert "color: #fff6dc" in css


def test_settings_course_editor_uses_theme_specific_hover_and_cell_text_colors():
    for theme_key in ("mist_blue", "lavender_cloud", "ocean_night", "high_contrast"):
        css = settings_stylesheet(theme_key)

        assert "QTableWidget#timetableSchemePeriodTable" in css
        assert "QTableWidget#timetableSchemePeriodTable QTimeEdit" in css
        assert "QPushButton:hover" in css
        assert "QPushButton[primary=\"true\"]:hover" in css
        assert "QComboBox::drop-down:hover" in css
        assert "QAbstractSpinBox::up-button:hover" in css


def test_course_settings_page_uses_readable_control_and_tab_typography():
    css = settings_stylesheet("mist_blue")

    assert "QWidget#courseSettingsPage QTabBar::tab" in css
    assert "QWidget#courseSettingsPage QTableWidget::item" in css
    assert "QWidget#courseSettingsPage QPushButton" in css
    assert "min-height: 34px; padding: 6px 13px; font-size: 14px" in css


def test_theme_display_names_are_neutral_and_do_not_expose_game_titles():
    forbidden = ("Arknights", "Endfield", "Honkai", "Star Rail", "Wuthering")

    for label in THEME_LABELS.values():
        assert not any(term.casefold() in label.casefold() for term in forbidden)

    assert THEME_LABELS["terra_signal"] == "Terra Signal"
    assert THEME_LABELS["endfield_industrial"] == "Frontier Foundry"
    assert THEME_LABELS["starrail_astral"] == "Astral Transit"
    assert THEME_LABELS["wuthering_tide"] == "Coastal Tide"
