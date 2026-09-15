"""
Automated Tests for Health Diagnostic Endpoints
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_llm_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health/llm")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "active_provider" in data
        assert "available_providers" in data
        assert isinstance(data["available_providers"], list)
