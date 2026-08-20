"""Minimal application bootstrap for Task 2.

The GUI lifecycle is intentionally deferred to Task 3.  This module only
initializes the runtime directories and logging infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass

from deskboard.infrastructure.logging_setup import configure_logging
from deskboard.infrastructure.paths import RuntimePaths, ensure_runtime_dirs


@dataclass(frozen=True)
class Runtime:
    paths: RuntimePaths


def initialize_runtime() -> Runtime:
    """Create the supported runtime directories and configure DeskBoard logs."""
    paths = ensure_runtime_dirs()
    logger = configure_logging(paths.logs)
    logger.info("DeskBoard runtime initialized")
    return Runtime(paths=paths)


def main() -> int:
    initialize_runtime()
    return 0
