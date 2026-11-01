"""Health and Readiness Probes.

Implements /api/v1/health/live and /api/v1/health/ready.
Safely validates backend and database health without exposing sensitive credentials.
"""

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.db.session import check_database_connectivity

router = APIRouter(prefix="/health", tags=["Health & Readiness"])


class LivenessResponse(BaseModel):
    status: str = Field(default="UP", description="Liveness state")
    service: str = Field(default=settings.app_name)
    environment: str = Field(default=settings.app_env)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DatabaseHealth(BaseModel):
    status: str
    latency_ms: float
    error: str | None = None


class StorageHealth(BaseModel):
    provider: str
    status: str


class ReadinessResponse(BaseModel):
    status: str = Field(description="'READY' or 'DEGRADED'")
    service: str = Field(default=settings.app_name)
    database: DatabaseHealth
    storage: StorageHealth
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@router.get(
    "/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Confirm that the backend process is running and accepting HTTP connections.",
)
async def liveness_check() -> LivenessResponse:
    return LivenessResponse(
        status="UP",
        service=settings.app_name,
        environment=settings.app_env,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description=(
        "Confirm that backend dependencies (database, file storage) "
        "are healthy and ready to serve traffic."
    ),
)
async def readiness_check(response: Response) -> ReadinessResponse:
    # Check Database Connectivity
    is_db_connected, db_latency, db_error = await check_database_connectivity()

    # Check Storage Readiness
    storage_status = "AVAILABLE"
    if settings.storage_provider == "local":
        os.makedirs(settings.storage_local_dir, exist_ok=True)

    db_health = DatabaseHealth(
        status="CONNECTED" if is_db_connected else "UNAVAILABLE",
        latency_ms=db_latency,
        error=db_error,
    )

    storage_health = StorageHealth(
        provider=settings.storage_provider,
        status=storage_status,
    )

    if not is_db_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "DEGRADED"
    else:
        response.status_code = status.HTTP_200_OK
        overall_status = "READY"

    return ReadinessResponse(
        status=overall_status,
        service=settings.app_name,
        database=db_health,
        storage=storage_health,
    )
