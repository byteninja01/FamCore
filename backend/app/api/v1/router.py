"""API v1 Router Aggregator.

Consolidates all v1 domain routers under the /api/v1 prefix.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router

api_v1_router = APIRouter()

# Register domain routers
api_v1_router.include_router(health_router)
