"""Synchronous bounded HTTP boundary for providers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import requests

from deskboard.providers.errors import (
    ProviderHTTPError,
    ProviderParseError,
    ProviderTimeoutError,
)

DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_USER_AGENT = "DeskBoard/0.1 (+local desktop dashboard)"


class HttpClient:
    """Use direct, bounded requests without a connectivity-probe gate."""

    def __init__(
        self,
        session: requests.Session | None = None,
        *,
        timeout: float | tuple[float, float] = DEFAULT_TIMEOUT_SECONDS,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self._session = session or requests.Session()
        if session is None:
            self._session.trust_env = False
        self._timeout = _validate_timeout(timeout)
        if not isinstance(user_agent, str) or not user_agent.strip():
            raise ValueError("user agent must not be empty")
        self._headers = {"User-Agent": user_agent}

    @property
    def timeout(self) -> float | tuple[float, float]:
        return self._timeout

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | tuple[float, float] | None = None,
    ) -> requests.Response:
        if not isinstance(url, str) or not url.strip():
            raise ValueError("HTTP URL must not be empty")
        request_headers = dict(self._headers)
        if headers is not None:
            request_headers.update(headers)
        try:
            response = self._session.get(
                url,
                params=params,
                headers=request_headers,
                timeout=self._timeout if timeout is None else _validate_timeout(timeout),
            )
        except requests.Timeout as error:
            raise ProviderTimeoutError(
                f"HTTP request timed out: {url}",
                user_message="请求超时",
            ) from error
        except requests.RequestException as error:
            raise ProviderHTTPError(
                f"HTTP request failed for {url}: {error}",
                user_message="网络请求失败",
            ) from error

        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            status = getattr(response, "status_code", "unknown")
            raise ProviderHTTPError(
                f"HTTP status {status} for {url}",
                user_message=f"数据源返回 HTTP {status}",
            ) from error
        return response

    def get_json(self, url: str, **kwargs: Any) -> Any:
        response = self.get(url, **kwargs)
        try:
            return response.json()
        except (TypeError, ValueError) as error:
            raise ProviderParseError(
                f"HTTP response was not valid JSON: {url}",
                user_message="数据格式无法解析",
            ) from error

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        if not isinstance(method, str) or method.upper() != "GET":
            raise ValueError("Task 15 HttpClient supports bounded GET requests only")
        return self.get(url, **kwargs)

    def get_text(self, url: str, **kwargs: Any) -> str:
        response = self.get(url, **kwargs)
        return str(response.text)


def _validate_timeout(value: float | tuple[float, float]) -> float | tuple[float, float]:
    if isinstance(value, tuple):
        if len(value) != 2 or any(
            isinstance(part, bool) or not isinstance(part, (int, float)) or part <= 0
            for part in value
        ):
            raise ValueError("HTTP timeout tuple must contain two positive numbers")
        return (float(value[0]), float(value[1]))
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError("HTTP timeout must be positive")
    return float(value)
