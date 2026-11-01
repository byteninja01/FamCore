"""Tests for Health and Readiness Probes."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns service info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "FamCore"
    assert "version" in data
    assert "tagline" in data
    assert data["docs"] == "/api/v1/docs"
    assert data["health"] == "/api/v1/health/live"


@pytest.mark.asyncio
async def test_liveness_probe(client: AsyncClient):
    """Test /api/v1/health/live returns UP."""
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "FamCore"
    assert "timestamp" in data
    # Verify response headers
    assert "X-Correlation-ID" in response.headers
    assert "X-Response-Time-Ms" in response.headers


@pytest.mark.asyncio
async def test_readiness_probe(client: AsyncClient):
    """Test /api/v1/health/ready returns READY when DB is connected."""
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY"
    assert data["database"]["status"] == "CONNECTED"
    assert data["database"]["latency_ms"] >= 0.0
    assert data["storage"]["status"] == "AVAILABLE"
