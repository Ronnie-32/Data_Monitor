from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest

from deskboard.providers.china_index.provider import (
    CHINA_INDEX_URL,
    ChinaIndexProvider,
    parse_china_indices,
)
from deskboard.providers.errors import ProviderDataError, ProviderParseError

FIXTURES = Path(__file__).parents[2] / "fixtures" / "providers"


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parse_validated_tencent_fixture_normalizes_all_a_share_indices():
    parsed = parse_china_indices(fixture("tencent_indices_gbk.txt"))

    assert tuple(parsed) == (
        "index.sse",
        "index.szse",
        "index.chinext",
        "index.csi300",
    )
    assert parsed["index.sse"] == {
        "key": "index.sse",
        "name": "上证指数",
        "value": pytest.approx(3903.72),
        "change": pytest.approx(9.30),
        "change_percent": pytest.approx(0.24),
        "unit": "index points",
    }
    assert parsed["index.szse"]["value"] == pytest.approx(13972.78)
    assert parsed["index.chinext"]["change_percent"] == pytest.approx(0.64)
    assert parsed["index.csi300"]["value"] == pytest.approx(4592.75)
    assert parsed["index.csi300"]["change"] == pytest.approx(4.05)
    assert parsed["index.csi300"]["change_percent"] == pytest.approx(0.09)
    assert all(
        set(item) == {"key", "name", "value", "change", "change_percent", "unit"}
        for item in parsed.values()
    )


def test_parser_rejects_missing_or_invalid_required_a_share_data():
    raw = fixture("tencent_indices_gbk.txt")
    missing = raw.replace(b'v_s_sz399006="', b'v_s_sz399006_missing="', 1)
    with pytest.raises(ProviderParseError, match="missing"):
        parse_china_indices(missing)

    zero_value = raw.replace(b"3903.72", b"0", 1)
    with pytest.raises(ProviderDataError, match="value"):
        parse_china_indices(zero_value)

    invalid_change = raw.replace(b"9.30", b"not-a-number", 1)
    with pytest.raises(ProviderDataError, match="change"):
        parse_china_indices(invalid_change)


class FakeChinaIndexHttpClient:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get(self, url: str, **kwargs: object) -> SimpleNamespace:
        self.calls.append((url, kwargs))
        return SimpleNamespace(content=self.response)


def test_provider_uses_one_fixed_source_and_returns_cacheable_catalog_items():
    client = FakeChinaIndexHttpClient(fixture("tencent_indices_gbk.txt"))
    provider = ChinaIndexProvider(http_client=client)

    result = provider.fetch()

    assert provider.group == "indices"
    assert [item.key for item in result.items] == [
        "index.sse",
        "index.szse",
        "index.chinext",
        "index.csi300",
    ]
    assert result.items[0].payload["key"] == "index.sse"
    assert result.items[0].payload["value"] == pytest.approx(3903.72)
    assert len(client.calls) == 1
    assert client.calls[0][0] == CHINA_INDEX_URL
    assert urlparse(client.calls[0][0]).path == (
        "/q=s_sh000001,s_sz399001,s_sz399006,sh000300"
    )
    assert client.calls[0][1]["headers"] == {"Accept": "text/plain"}
