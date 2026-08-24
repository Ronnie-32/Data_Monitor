"""Tencent public A-share index provider."""

from deskboard.providers.china_index.provider import (
    CHINA_INDEX_GROUP,
    CHINA_INDEX_ITEM_KEYS,
    CHINA_INDEX_URL,
    ChinaIndexProvider,
    parse_china_indices,
)

__all__ = [
    "CHINA_INDEX_GROUP",
    "CHINA_INDEX_ITEM_KEYS",
    "CHINA_INDEX_URL",
    "ChinaIndexProvider",
    "parse_china_indices",
]
