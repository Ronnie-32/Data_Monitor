"""Bounded, user-readable errors shared by network providers."""

from __future__ import annotations


class ProviderError(RuntimeError):
    """Base error raised by a provider or its HTTP boundary."""

    def __init__(self, message: str, *, user_message: str | None = None) -> None:
        super().__init__(message)
        self.user_message = user_message or message


class ProviderTimeoutError(ProviderError):
    """The bounded HTTP request exceeded its timeout."""


class ProviderHTTPError(ProviderError):
    """The upstream returned an unsuccessful HTTP response."""


class ProviderParseError(ProviderError):
    """The upstream response could not be parsed."""


class ProviderDataError(ProviderError):
    """The upstream response parsed but was not valid normalized data."""


# A descriptive alias for callers that treat transport failures separately.
HttpClientError = ProviderHTTPError

