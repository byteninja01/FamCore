"""Centralized Exception Handling & RFC 7807 Problem Details.

Standardizes API error responses across the FamCore platform.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_correlation_id, logger


class FamCoreException(Exception):
    """Base class for all application domain exceptions."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_SERVER_ERROR",
        error_type: str = "https://famcore.in/errors/internal-error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.error_type = error_type
        self.details = details or {}


class EntityNotFoundException(FamCoreException):
    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(
            message=f"{entity_name} with identifier '{identifier}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            error_type="https://famcore.in/errors/not-found",
        )


class ConsentDeniedException(FamCoreException):
    def __init__(self, message: str = "Access denied: No active consent grant found."):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code="CONSENT_DENIED",
            error_type="https://famcore.in/errors/consent-denied",
        )


class AuthenticationException(FamCoreException):
    def __init__(self, message: str = "Invalid or expired authentication credentials."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            error_type="https://famcore.in/errors/unauthorized",
        )


def format_rfc7807_error(
    status_code: int,
    title: str,
    detail: str,
    code: str,
    instance: str,
    error_type: str = "about:blank",
    extra: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    payload = {
        "type": error_type,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance,
        "code": code,
        "correlation_id": get_correlation_id(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        payload["details"] = extra

    return JSONResponse(
        status_code=status_code,
        content=payload,
        media_type="application/problem+json",
    )


async def famcore_exception_handler(request: Request, exc: FamCoreException) -> JSONResponse:
    logger.warning(
        "Domain exception occurred: %s (code: %s, status: %d) on %s",
        exc.message,
        exc.code,
        exc.status_code,
        request.url.path,
    )
    return format_rfc7807_error(
        status_code=exc.status_code,
        title=exc.code.replace("_", " ").title(),
        detail=exc.message,
        code=exc.code,
        instance=request.url.path,
        error_type=exc.error_type,
        extra=exc.details,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    formatted_errors = []
    for err in exc.errors():
        formatted_errors.append({
            "field": ".".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"],
        })

    logger.info("Request validation failed on %s: %s", request.url.path, formatted_errors)
    return format_rfc7807_error(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Unprocessable Entity",
        detail="The request body or parameters failed validation.",
        code="VALIDATION_ERROR",
        instance=request.url.path,
        error_type="https://famcore.in/errors/validation-error",
        extra={"validation_errors": formatted_errors},
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return format_rfc7807_error(
        status_code=exc.status_code,
        title="HTTP Error",
        detail=str(exc.detail),
        code="HTTP_ERROR",
        instance=request.url.path,
        error_type="https://famcore.in/errors/http-error",
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server exception on %s: %s", request.url.path, exc)
    return format_rfc7807_error(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="An unexpected internal error occurred. Please try again later.",
        code="INTERNAL_SERVER_ERROR",
        instance=request.url.path,
        error_type="https://famcore.in/errors/internal-error",
    )
