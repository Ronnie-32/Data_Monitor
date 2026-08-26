from pathlib import Path

WEB_ROOT = Path("src/deskboard/ui/dashboard/web")


def test_dashboard_loads_shared_visual_tokens_before_component_styles():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert '<html lang="zh-CN" data-theme="mist_blue">' in html
    assert './css/base.css' in html
    assert './css/themes.css' in html
    assert html.index('./css/base.css') < html.index('./css/themes.css')
    assert html.index('./css/themes.css') < html.index('./css/layout.css')
    assert html.index('./css/layout.css') < html.index('./css/widgets.css')


def test_visual_tokens_define_theme_catalog_font_and_profile_opacity_contract():
    base = (WEB_ROOT / "css/base.css").read_text(encoding="utf-8")
    themes = (WEB_ROOT / "css/themes.css").read_text(encoding="utf-8")
    app = (WEB_ROOT / "js/app.js").read_text(encoding="utf-8")

    themes_to_check = (
        "mist_blue",
        "mint_breeze",
        "almond_sand",
        "lavender_cloud",
        "ocean_night",
        "graphite_night",
        "rose_dusk",
        "high_contrast",
        "terra_signal",
        "endfield_industrial",
        "starrail_astral",
        "wuthering_tide",
    )
    for theme in themes_to_check:
        assert f'[data-theme="{theme}"]' in themes
    assert themes.count('[data-theme="') >= len(themes_to_check)
    assert "--panel-opacity" in base
    assert "--surface-rgb" in themes
    assert "--widget-rgb" in themes
    assert "themeKey" in app
    assert "panelOpacity" in app
    assert "document.documentElement.dataset.theme" in app
    assert "--panel-opacity" in app
    assert "FONT_FAMILIES" in app
    assert "fontKey" in app


def test_visual_baseline_records_readable_minimums_for_every_v1_widget():
    baseline = Path("docs/ui-readability-baseline.md").read_text(encoding="utf-8")

    for widget_key in (
        "weather",
        "todo",
        "today_agenda",
        "gold",
        "fx",
        "china_indices",
        "us_indices",
        "finance_overview",
    ):
        assert f"`{widget_key}`" in baseline
    assert "360 × 220" in baseline
    assert "Mist Blue" in baseline
    assert "Mint Breeze" in baseline
    assert "Almond Sand" in baseline
    assert "Lavender Cloud" in baseline
    assert "Profile opacity" in baseline


def test_dashboard_native_minimum_matches_the_accepted_visual_baseline():
    source = Path("src/deskboard/ui/dashboard/window.py").read_text(encoding="utf-8")

    assert "setMinimumSize(360, 220)" in source


def test_visual_styles_do_not_add_continuous_animation_or_runtime_assets():
    css = "\n".join(
        (WEB_ROOT / "css" / name).read_text(encoding="utf-8")
        for name in ("base.css", "themes.css", "layout.css", "widgets.css", "timetable.css")
    )
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert "animation:" not in css
    assert "@keyframes" not in css
    assert "https://" not in html
    assert "http://" not in html


def test_information_cards_show_data_directly_without_shell_titles():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    weather = (WEB_ROOT / "js/widgets/weather.js").read_text(encoding="utf-8")
    finance = (WEB_ROOT / "js/widgets/finance.js").read_text(encoding="utf-8")
    widgets = (WEB_ROOT / "css/widgets.css").read_text(encoding="utf-8")

    assert 'class="widget weather-widget info-widget"' in html
    assert 'class="widget finance-widget info-widget"' in html
    assert 'id="weather-title"' not in html
    assert 'id="gold-title"' not in html
    assert 'id="finance-overview-title"' not in html
    assert "cities.slice" not in weather
    assert "filtered.slice" not in finance
    assert "uniqueFinanceItems" in finance
    assert ".info-widget .weather-cities" in widgets
    assert ".info-widget .finance-items" in widgets
    assert "overflow: hidden" in widgets


def test_layout_edit_exposes_resize_handles_and_wraps_long_values():
    layout = (WEB_ROOT / "js/layout.js").read_text(encoding="utf-8")
    app = (WEB_ROOT / "js/app.js").read_text(encoding="utf-8")
    layout_css = (WEB_ROOT / "css/layout.css").read_text(encoding="utf-8")
    bridge = Path("src/deskboard/ui/dashboard/bridge.py").read_text(encoding="utf-8")
    window = Path("src/deskboard/ui/dashboard/window.py").read_text(encoding="utf-8")
    widgets = (WEB_ROOT / "css/widgets.css").read_text(encoding="utf-8")

    assert "alwaysShowResizeHandle: true" in layout
    assert 'handles: "n,e,s,w,ne,se,sw,nw"' in layout
    assert "ui-resizable-handle" in layout_css
    assert "display: block !important" in layout_css
    assert "grid-stack-placeholder" in layout_css
    assert "background-size: calc(100% / 48)" in layout_css
    assert ".finance-value" in widgets
    assert "overflow-wrap: anywhere" in widgets
    assert ".weather-city-heading" in widgets
    assert "flex-wrap: wrap" in widgets
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    assert "拖卡片移动" in html
    assert 'id="shell-drag-handle"' in html
    assert 'data-drag-region="true"' in html
    assert 'id="edit-dragbar"' not in html
    assert html.index('<header class="shell-bar">') < html.index('id="layout-toolbar"')
    assert html.index('id="layout-toolbar"') < html.index('class="network-status"')
    assert 'class="layout-toolbar-actions"' in html
    assert ".layout-toolbar" in layout_css
    assert "position: static" in layout_css
    assert "overflow-x: hidden" in layout_css
    assert "overflow-x: auto" not in layout_css
    assert "pointerdown" in layout
    assert "beginWindowDrag" in layout
    assert "store.getState().app" in app
    assert "windowDragRequested" in bridge
    assert "WM_NCLBUTTONDOWN" in window
    assert 'body[data-mode="layout_edit"] .shell-title' in layout_css
    assert 'body[data-mode="layout_edit"] .settings-button' in layout_css
    assert 'body[data-mode="layout_edit"] .dashboard-surface { padding-top' not in widgets


def test_compact_information_headings_use_available_space_before_wrapping():
    widgets = (WEB_ROOT / "css/widgets.css").read_text(encoding="utf-8")

    assert "grid-template-columns: minmax(0, 1fr) auto" in widgets
    assert "max-width: 55%" not in widgets
    assert (
        ".weather-city-heading { display: flex; align-items: baseline; flex-wrap: nowrap;"
        in widgets
    )
    assert "white-space: nowrap;" in widgets


def test_dashboard_widget_typography_grows_at_readable_widths():
    widgets = (WEB_ROOT / "css/widgets.css").read_text(encoding="utf-8")

    assert "@container (min-width: 640px)" in widgets
    assert ".todo-content" in widgets
    assert ".agenda-content" in widgets
    assert "font-size: clamp(13px, calc(10px + 0.95cqw), 16px);" in widgets
    assert "font-size: clamp(12px, calc(9px + 1.7cqw), 15px);" in widgets


def test_finance_cards_use_card_width_and_keep_compact_headings_single_line():
    widgets = (WEB_ROOT / "css/widgets.css").read_text(encoding="utf-8")
    compact_rules = widgets[widgets.index("@container (max-width: 240px)") :]

    assert ".finance-item {\n  container-type: inline-size;" in widgets
    assert "font-size: clamp(12px, calc(9px + 1.9cqw), 16px);" in widgets
    assert "grid-template-columns: minmax(0, 1fr) auto;" in compact_rules
    assert "grid-template-columns: minmax(0, 1fr);" not in compact_rules
    assert "white-space: normal;" not in compact_rules
