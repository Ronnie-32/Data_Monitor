from __future__ import annotations

import pytest
import requests

from deskboard.providers.errors import (
    ProviderHTTPError,
    ProviderParseError,
    ProviderTimeoutError,
)
from deskboard.providers.http_client import HttpClient


class FakeResponse:
    def __init__(self, payload=None, *, status_code=200, error=None):
        self.payload = payload
        self.status_code = status_code
        self.error = error
        self.text = "plain text"

    def raise_for_status(self):
        if self.error is not None:
            raise self.error

    def json(self):
        if isinstance(self.payload, BaseException):
            raise self.payload
        return self.payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


def test_get_is_direct_and_bounded_with_explicit_timeout_and_user_agent():
    session = FakeSession(FakeResponse({"ok": True}))
    client = HttpClient(session, timeout=(2, 5), user_agent="DeskBoard-Test")

    assert client.get_json("https://example.test/data", params={"a": "b"}) == {"ok": True}
    url, kwargs = session.calls[0]
    assert url == "https://example.test/data"
    assert kwargs["timeout"] == (2.0, 5.0)
    assert kwargs["headers"]["User-Agent"] == "DeskBoard-Test"


def test_timeout_http_error_and_parse_error_are_readable_provider_errors():
    with pytest.raises(ProviderTimeoutError, match="timed out"):
        HttpClient(FakeSession(requests.Timeout("slow"))).get("https://example.test")

    with pytest.raises(ProviderHTTPError, match="HTTP status 503"):
        HttpClient(
            FakeSession(FakeResponse(status_code=503, error=requests.HTTPError()))
        ).get("https://example.test")

    with pytest.raises(ProviderParseError, match="not valid JSON"):
        HttpClient(FakeSession(FakeResponse(ValueError("bad json")))).get_json(
            "https://example.test"
        )
