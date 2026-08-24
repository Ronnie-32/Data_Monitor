from __future__ import annotations

from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from deskboard.providers.errors import ProviderDataError, ProviderParseError
from deskboard.providers.gold.provider import GoldProvider, parse_gold

FIXTURES = Path(__file__).parents[2] / "fixtures" / "providers"


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parse_sge_fixture_returns_au9999_daily_quote():
    quote = parse_gold(fixture("sge_au9999_daily.html"))

    assert quote == {
        "key": "gold_au9999",
        "date": "2026-08-20",
        "name": "Au99.99",
        "value": pytest.approx(968.14),
        "change": pytest.approx(22.92),
        "change_percent": pytest.approx(2.42),
        "unit": "CNY/g",
        "price_field": "daily close",
    }


def test_parse_gold_rejects_missing_or_non_positive_quote():
    with pytest.raises(ProviderParseError, match="Au99.99"):
        parse_gold(b"<html><body><table><tr><td>other</td></tr></table></body></html>")

    zero_close = b"""
    <table><tr>
      <td>2026-08-20</td><td>Au99.99</td>
      <td>1</td><td>2</td><td>1</td><td>0</td>
      <td>0</td><td>0%</td><td>1</td>
    </tr></table>
    """
    with pytest.raises(ProviderDataError, match="close"):
        parse_gold(zero_close)


class FakeGoldHttpClient:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get_text(self, url: str, **kwargs: object) -> str:
        self.calls.append((url, kwargs))
        return self.response.decode("utf-8")


def test_gold_provider_returns_stable_deskboard_item_and_uses_one_fixed_source():
    client = FakeGoldHttpClient(fixture("sge_au9999_daily.html"))
    provider = GoldProvider(
        http_client=client,
        as_of=date(2026, 8, 24),
        lookback_days=1,
    )

    result = provider.fetch()

    assert provider.group == "gold"
    assert [item.key for item in result.items] == ["gold.au9999"]
    assert result.items[0].payload["key"] == "gold.au9999"
    assert result.items[0].payload["value"] == pytest.approx(968.14)
    assert len(client.calls) == 1
    parsed = urlparse(client.calls[0][0])
    assert parsed.netloc == "www.sge.com.cn"
    assert parse_qs(parsed.query) == {
        "start_date": ["2026-08-24"],
        "end_date": ["2026-08-24"],
    }
