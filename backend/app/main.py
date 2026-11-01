"""FamCore FastAPI Application Entry Point.

Initializes the FastAPI application, registers middleware, global exception handlers,
and aggregates domain routers under the /api/v1 prefix.
"""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import (
    FamCoreException,
    famcore_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import correlation_id_ctx, logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown hooks."""
    setup_logging(debug=settings.debug)
    logger.info(
        "Starting %s (%s environment) on port %d",
        settings.app_name,
        settings.app_env,
        settings.port,
    )
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_application() -> FastAPI:
    """Application factory for FamCore backend."""
    app = FastAPI(
        title="FamCore API",
        description="FamCore — Patient-Centric Family Healthcare Operating System API",
        version="0.1.0",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
        lifespan=lifespan,
    )

    # 1. Correlation ID & Access Log Middleware
    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or f"req_{uuid.uuid4().hex[:12]}"
        token = correlation_id_ctx.set(correlation_id)
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        logger.info(
            "%s %s -> %d (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        correlation_id_ctx.reset(token)
        return response

    # 2. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins if isinstance(settings.allowed_origins, list) else [settings.allowed_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID", "X-Response-Time-Ms"],
    )

    # 3. Global Exception Handlers
    app.add_exception_handler(FamCoreException, famcore_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # 4. Include API Routers
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    # 5. Root Service Discovery
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "tagline": "Your family's health. Your records. Your choices.",
            "docs": f"{settings.api_v1_prefix}/docs",
            "health": f"{settings.api_v1_prefix}/health/live",
        }

    return app


app = create_application()
