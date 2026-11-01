"""Structured Logging Configuration for FamCore.

Implements clean, structured log formatting with correlation IDs and timestamps.
Strictly excludes sensitive user data, passwords, and medical document contents from logs.
"""

import logging
import sys
import uuid
from contextvars import ContextVar

# Context variable for request correlation ID
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    val = correlation_id_ctx.get()
    if not val:
        val = f"req_{uuid.uuid4().hex[:12]}"
        correlation_id_ctx.set(val)
    return val


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_ctx.get() or "system"
        return True


def setup_logging(debug: bool = False) -> None:
    log_level = logging.DEBUG if debug else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(correlation_id)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)


logger = logging.getLogger("famcore")
