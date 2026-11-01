"""Tests for Centralized Exception Handling and RFC 7807 formatting."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_404_not_found_handling(client: AsyncClient):
    """Test non-existent endpoints return RFC 7807 problem details."""
    response = await client.get("/api/v1/non-existent-route")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert data["status"] == 404
    assert "detail" in data
    assert "correlation_id" in data
    assert "timestamp" in data
