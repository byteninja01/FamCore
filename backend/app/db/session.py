"""Database Session Management & Health Connectivity Checks.

Provides async SQLAlchemy engine, session maker, and connectivity validation.
Supports both PostgreSQL (via psycopg) and SQLite (via aiosqlite for local testing).
"""

import time
from typing import AsyncGenerator, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.logging import logger

# Configure engine kwargs based on database dialect
connect_args = {}
engine_kwargs = {
    "echo": settings.debug and not settings.is_production,
    "future": True,
}

if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine_kwargs["connect_args"] = connect_args
else:
    # Production PostgreSQL pool configuration
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(settings.database_url, **engine_kwargs)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing database sessions to FastAPI endpoints."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connectivity() -> Tuple[bool, float, Optional[str]]:
    """Check database health by executing a lightweight query.

    Returns:
        (is_connected, latency_ms, error_message)
    """
    start_time = time.perf_counter()
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return True, latency_ms, None
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.warning("Database connectivity check failed: %s", exc)
        return False, latency_ms, "Database unreachable or not responding"
