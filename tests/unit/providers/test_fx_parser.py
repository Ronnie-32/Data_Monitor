from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from deskboard.providers.errors import ProviderDataError, ProviderParseError
from deskboard.providers.fx.provider import FXProvider, parse_fx

FIXTURES = Path(__file__).parents[2] / "fixtures" / "providers"


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parse_chinamoney_fixture_normalizes_all_four_currencies():
    parsed = parse_fx(fixture("chinamoney_ccpr_his_new.json"))

    assert parsed["date"] == "2026-08-20"
    assert parsed["basis"] == "CNY per 1 foreign-currency unit"
    assert parsed["items"]["USD"]["value"] == pytest.approx(6.7808)
    assert parsed["items"]["EUR"]["value"] == pytest.approx(7.8815)
    assert parsed["items"]["JPY"]["value"] == pytest.approx(0.042636)
    assert parsed["items"]["HKD"]["value"] == pytest.approx(0.86476)
    assert all(
        item["unit"] == f"CNY/1 {currency}"
        for currency, item in parsed["items"].items()
    )


def test_parse_fx_does_not_divide_a_rate_already_quoted_per_one_unit():
    raw = {
        "data": {"searchlist": ["USD/CNY", "EUR/CNY", "JPY/CNY", "HKD/CNY"]},
        "records": [
            {
                "date": "2026-08-20",
                "values": ["6.8", "7.8", "0.043", "0.86"],
            }
        ],
    }

    parsed = parse_fx(json.dumps(raw).encode("utf-8"))

    assert parsed["items"]["JPY"]["value"] == pytest.approx(0.043)
    assert parsed["items"]["JPY"]["upstream_quotation"] == "JPY/CNY"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"data": {}, "records": []}, "shape"),
        (
            {
                "data": {"searchlist": ["USD/CNY"]},
                "records": [{"date": "2026-08-20", "values": ["not-a-rate"]}],
            },
            "USD/CNY",
        ),
        (
            {
                "data": {
                    "searchlist": ["USD/CNY", "EUR/CNY", "100JPY/CNY", "HKD/CNY"]
                },
                "records": [
                    {"date": "2026-08-20", "values": ["6.8", "7.8", "0", "0.86"]}
                ],
            },
            "positive",
        ),
    ],
)
def test_parse_fx_rejects_missing_invalid_or_non_positive_rates(
    payload: dict[str, object], message: str
):
    error_type = ProviderParseError if message == "shape" else ProviderDataError

    with pytest.raises(error_type, match=message):
        parse_fx(json.dumps(payload).encode("utf-8"))


class FakeFxHttpClient:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get_text(self, url: str, **kwargs: object) -> str:
        self.calls.append((url, kwargs))
        return self.response.decode("utf-8")


def test_fx_provider_returns_one_cacheable_result_per_fixed_catalog_item():
    client = FakeFxHttpClient(fixture("chinamoney_ccpr_his_new.json"))
    provider = FXProvider(http_client=client, as_of=date(2026, 8, 24))

    result = provider.fetch()

    assert provider.group == "fx"
    assert [item.key for item in result.items] == [
        "fx.usd_cny",
        "fx.eur_cny",
        "fx.jpy_cny",
        "fx.hkd_cny",
    ]
    assert [item.payload["value"] for item in result.items] == pytest.approx(
        [6.7808, 7.8815, 0.042636, 0.86476]
    )
    assert len(client.calls) == 1
    parsed = urlparse(client.calls[0][0])
    assert parsed.netloc == "www.chinamoney.com.cn"
    assert parse_qs(parsed.query) == {
        "startDate": ["2026-08-10"],
        "endDate": ["2026-08-24"],
        "currency": ["USD/CNY,EUR/CNY,100JPY/CNY,HKD/CNY"],
        "pageNum": ["1"],
        "pageSize": ["20"],
    }
