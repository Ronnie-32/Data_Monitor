from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from deskboard.presentation.dashboard_state import present_dashboard_state
from deskboard.ui.dashboard.bridge import DashboardBridge


class FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 24, 9, 30)

    def today(self) -> date:
        return date(2026, 8, 24)


class FakeFinancePresenter:
    def __init__(self) -> None:
        self.calls = 0
        self.state = {
            "items": [
                {
                    "key": "fx.usd_cny",
                    "category": "fx",
                    "name": "美元/人民币",
                    "valueText": "1 USD = 6.7808 CNY",
                    "changePercentText": "+0.10%",
                    "direction": "up",
                    "marketState": "unknown",
                }
            ]
        }

    def present(self, **_kwargs):
        self.calls += 1
        return self.state


def test_dashboard_state_builds_finance_once_from_one_shared_presenter():
    presenter = FakeFinancePresenter()

    state = present_dashboard_state(
        todo_service=None,
        agenda_service=None,
        clock=FakeClock(),
        finance_presenter=presenter,
    )

    assert state["finance"] is not presenter.state
    assert state["finance"] == presenter.state
    assert presenter.calls == 1


def test_bridge_emits_finance_changed_with_initial_state():
    presenter = FakeFinancePresenter()
    bridge = DashboardBridge(clock=FakeClock(), finance_presenter=presenter)
    states: list[dict[str, object]] = []
    finance_events: list[dict[str, object]] = []
    bridge.stateChanged.connect(states.append)
    bridge.financeChanged.connect(finance_events.append)

    bridge.requestInitialState()

    assert states[0]["finance"] == presenter.state
    assert finance_events == [presenter.state]
    assert presenter.calls == 1


def test_finance_web_contract_uses_one_state_and_bounded_scroll_renderer():
    web_root = Path("src/deskboard/ui/dashboard/web")
    html = (web_root / "index.html").read_text(encoding="utf-8")
    app = (web_root / "js/app.js").read_text(encoding="utf-8")
    bridge = (web_root / "js/bridge.js").read_text(encoding="utf-8")
    finance = (web_root / "js/widgets/finance.js").read_text(encoding="utf-8")
    css = (web_root / "css/widgets.css").read_text(encoding="utf-8")

    assert "financeChanged" in bridge
    assert "createFinanceWidget" in app
    assert './widgets/finance.js' in app
    for category in ("gold", "fx", "china_indices", "us_indices", "overview"):
        assert f'data-finance-category="{category}"' in html
    assert "ResizeObserver" in finance
    assert "overflow-y: auto" not in finance
    finance_block = css[css.index(".finance-items") : css.index(".finance-item {")]
    assert "overflow-y: auto" in finance_block
    assert "scrollbar-width: thin" in finance_block
