import logging

from deskboard.infrastructure.logging_setup import configure_logging


def test_configure_logging_creates_bounded_rotating_file(tmp_path):
    logger = configure_logging(tmp_path, max_bytes=128, backup_count=2)

    assert (tmp_path / "deskboard.log").exists()
    handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler, logging.handlers.RotatingFileHandler)
    ]
    assert len(handlers) == 1
    assert handlers[0].maxBytes == 128
    assert handlers[0].backupCount == 2


def test_fault_records_are_written_with_context(tmp_path):
    logger = configure_logging(tmp_path)

    logger.info("startup complete")
    logger.error("provider request failed", extra={"component": "provider"})
    try:
        raise RuntimeError("fixture failure")
    except RuntimeError:
        logger.exception("sqlite migration failed")
    for handler in logger.handlers:
        handler.flush()

    content = (tmp_path / "deskboard.log").read_text(encoding="utf-8")
    assert "startup complete" in content
    assert "provider request failed" in content
    assert "sqlite migration failed" in content
    assert "fixture failure" in content


def test_reconfiguration_does_not_duplicate_handlers(tmp_path):
    first = configure_logging(tmp_path)
    second = configure_logging(tmp_path)

    assert first is second
    rotating_handlers = [
        handler
        for handler in second.handlers
        if isinstance(handler, logging.handlers.RotatingFileHandler)
    ]
    assert len(rotating_handlers) == 1
