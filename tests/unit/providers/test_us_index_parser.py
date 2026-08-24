from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest

from deskboard.providers.errors import ProviderDataError, ProviderParseError
from deskboard.providers.us_index.provider import (
    US_INDEX_ITEM_KEYS,
    US_INDEX_URL,
    USIndexProvider,
    parse_us_indices,
)

FIXTURES = Path(__file__).parents[2] / "fixtures" / "providers"


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parse_validated_tencent_fixture_normalizes_all_us_indices():
    parsed = parse_us_indices(fixture("tencent_indices_gbk.txt"))

    assert tuple(parsed) == US_INDEX_ITEM_KEYS
    assert parsed["index.dow"] == {
        "key": "index.dow",
        "name": "道琼斯",
        "value": pytest.approx(53463.05),
        "change": pytest.approx(119.65),
        "change_percent": pytest.approx(0.22),
        "unit": "index points",
    }
    assert parsed["index.sp500"]["value"] == pytest.approx(7707.98)
    assert parsed["index.nasdaq"]["change_percent"] == pytest.approx(0.16)
    assert all(
        set(item) == {"key", "name", "value", "change", "change_percent", "unit"}
        for item in parsed.values()
    )


def test_parser_rejects_missing_or_invalid_required_us_index_data():
    raw = fixture("tencent_indices_gbk.txt")
    missing = raw.replace(b'v_us.INX="', b'v_us.INX_missing="', 1)
    with pytest.raises(ProviderParseError, match="missing"):
        parse_us_indices(missing)

    zero_value = raw.replace(b"53463.05", b"0", 1)
    with pytest.raises(ProviderDataError, match="value"):
        parse_us_indices(zero_value)

    invalid_change = raw.replace(b"119.65", b"not-a-number", 1)
    with pytest.raises(ProviderDataError, match="change"):
        parse_us_indices(invalid_change)


class FakeUSIndexHttpClient:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get(self, url: str, **kwargs: object) -> SimpleNamespace:
        self.calls.append((url, kwargs))
        return SimpleNamespace(content=self.response)


def test_provider_uses_one_fixed_source_and_returns_cacheable_catalog_items():
    client = FakeUSIndexHttpClient(fixture("tencent_indices_gbk.txt"))
    provider = USIndexProvider(http_client=client)

    result = provider.fetch()

    assert provider.group == "us_indices"
    assert [item.key for item in result.items] == list(US_INDEX_ITEM_KEYS)
    assert result.items[0].payload["key"] == "index.dow"
    assert result.items[0].payload["value"] == pytest.approx(53463.05)
    assert len(client.calls) == 1
    assert client.calls[0][0] == US_INDEX_URL
    assert urlparse(client.calls[0][0]).path == "/q=us.DJI,us.INX,us.IXIC"
    assert client.calls[0][1]["headers"] == {"Accept": "text/plain"}
