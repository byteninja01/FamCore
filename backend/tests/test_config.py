"""Tests for Application Configuration and Security Defaults."""

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_6digit_pin,
    hash_password,
    verify_password,
)


def test_settings_defaults():
    """Verify default configuration values."""
    s = Settings(app_name="FamCoreTest", allowed_origins="http://localhost:3000,http://127.0.0.1:3000")
    assert s.app_name == "FamCoreTest"
    assert s.api_v1_prefix == "/api/v1"
    assert isinstance(s.allowed_origins, list)
    assert len(s.allowed_origins) == 2
    assert "http://localhost:3000" in s.allowed_origins


def test_argon2_password_hashing():
    """Verify password hashing and verification using Argon2id."""
    password = "SuperSecurePassword123!"
    hashed = hash_password(password)
    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_lifecycle():
    """Verify JWT access token issuance and decoding."""
    payload = {"sub": "user_123", "role": "ROLE_PATIENT_OWNER"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "user_123"
    assert decoded["role"] == "ROLE_PATIENT_OWNER"
    assert "exp" in decoded


def test_pin_generator():
    """Verify 6-digit numeric PIN format for Health Passport."""
    pin = generate_6digit_pin()
    assert len(pin) == 6
    assert pin.isdigit()
