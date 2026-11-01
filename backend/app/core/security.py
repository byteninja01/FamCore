"""Security, Password Hashing & JWT Token Management.

Implements Argon2id password hashing and JWT token issuance and verification.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.core.logging import logger

# Initialize Argon2id password hasher with RFC 9106 recommended parameters
# memory_cost=65536 KiB (64MB), time_cost=3 iterations, parallelism=4 lanes
_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return _password_hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False
    except Exception as exc:
        logger.error("Argon2 verification failed unexpectedly: %s", exc)
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a short-lived JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Access token has expired.")
    except jwt.InvalidTokenError:
        raise AuthenticationException("Invalid access token.")


def generate_opaque_token(length_bytes: int = 24) -> str:
    """Generate a high-entropy URL-safe token (e.g. for Health Passport)."""
    return secrets.token_urlsafe(length_bytes)


def generate_6digit_pin() -> str:
    """Generate a secure 6-digit numeric PIN for temporary Health Passport access."""
    return f"{secrets.randbelow(1_000_000):06d}"
