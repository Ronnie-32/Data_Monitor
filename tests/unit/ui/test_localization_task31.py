from pathlib import Path

from deskboard.presentation.dashboard_state import present_dashboard_state
from deskboard.ui.settings.data_status_page import _group_label
from deskboard.ui.settings.i18n import translate_text


class FakeClock:
    def today(self):
        from datetime import date

        return date(2026, 8, 26)

    def now(self):
        from datetime import datetime

        return datetime(2026, 8, 26, 12)


def test_task31_chinese_translation_covers_common_native_ui_and_dynamic_mode_text():
    expected = {
        "Current": "当前",
        "current": "当前",
        "Current mode: interaction": "当前模式：交互",
        "Current mode: locked": "当前模式：锁定",
        "Current mode: layout_edit": "当前模式：布局编辑",
        "English": "英语",
        "Weekday only": "仅显示星期",
        "Weekly recurring courses": "每周重复课程",
        "Scheme editor (Save / Cancel)": "方案编辑（保存 / 取消）",
        "Data Status": "数据状态",
        "Refresh All": "全部刷新",
        "Weekly Timetable": "每周课表",
    }

    for source, chinese in expected.items():
        assert translate_text(source, "zh_CN") == chinese


def test_task31_data_status_translates_us_indices_group_label():
    assert _group_label("us_indices", "zh_CN") == "美国指数"
    assert _group_label("us_indices", "en_US") == "US indices"


def test_task31_dashboard_snapshot_carries_the_persisted_ui_language():
    state = present_dashboard_state(
        todo_service=None,
        agenda_service=None,
        clock=FakeClock(),
        language="zh_CN",
    )

    assert state["app"]["language"] == "zh_CN"


def test_task31_dashboard_uses_chinese_defaults_and_can_retranslate_live_copy():
    web_root = Path("src/deskboard/ui/dashboard/web")
    html = (web_root / "index.html").read_text(encoding="utf-8")
    app = (web_root / "js/app.js").read_text(encoding="utf-8")
    bridge = (web_root / "js/bridge.js").read_text(encoding="utf-8")
    i18n = (web_root / "js/i18n.js").read_text(encoding="utf-8")

    assert '<h2 id="todo-title" class="widget-title">待办</h2>' in html
    assert '<h2 id="timetable-title" class="timetable-title">每周课表</h2>' in html
    assert '<div id="mode" class="shell-mode">交互</div>' in html
    assert 'aria-label="拖动看板"' in html
    assert "applyDashboardLanguage" in app
    assert "languageChanged" in bridge
    assert '"Current": "当前"' not in i18n
    assert '"mode.interaction": "交互"' in i18n
    assert '"widget.todo": "待办"' in i18n
