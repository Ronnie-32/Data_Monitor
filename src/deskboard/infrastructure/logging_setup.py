"""Low-noise bounded rotating logging setup."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOGGER_NAME = "deskboard"
DEFAULT_MAX_BYTES = 1_000_000
DEFAULT_BACKUP_COUNT = 2
_HANDLER_MARKER = "_deskboard_rotating_handler"


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or LOGGER_NAME)


def configure_logging(
    log_directory: str | Path,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> logging.Logger:
    """Configure the named application logger and return it.

    Reconfiguration replaces only handlers installed by this function, so a
    test or embedding host may retain unrelated handlers.  The logger does
    not propagate to the root logger, preventing duplicate console noise.
    """
    if max_bytes <= 0 or backup_count < 0:
        raise ValueError("max_bytes must be positive and backup_count must be non-negative")
    directory = Path(log_directory)
    directory.mkdir(parents=True, exist_ok=True)
    logger = get_logger()
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in list(logger.handlers):
        if getattr(handler, _HANDLER_MARKER, False):
            logger.removeHandler(handler)
            handler.close()
    handler = RotatingFileHandler(
        directory / "deskboard.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    setattr(handler, _HANDLER_MARKER, True)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    return logger
