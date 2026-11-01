"""Common FastAPI Request Dependencies.

Provides dependencies for correlation IDs, database sessions, and authenticated context.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_correlation_id
from app.db.session import get_db

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
CorrelationId = Annotated[str, Depends(get_correlation_id)]
