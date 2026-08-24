"""China Foreign Exchange Trade System provider."""

from deskboard.providers.fx.provider import (
    CHINAMONEY_URL,
    FX_GROUP,
    FX_ITEM_KEYS,
    FXProvider,
    parse_fx,
)

__all__ = [
    "CHINAMONEY_URL",
    "FX_GROUP",
    "FX_ITEM_KEYS",
    "FXProvider",
    "parse_fx",
]
