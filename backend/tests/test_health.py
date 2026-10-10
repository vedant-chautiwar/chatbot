import pytest
from httpx import AsyncClient

from app.dependencies import get_db
from app.main import app
from tests.mock_mongo import MockMongoDBManager


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Agentic AI Chatbot Backend"
    assert data["status"] == "online"


@pytest.mark.asyncio
async def test_health_check_healthy(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data
    assert data["components"]["api"] == "ok"


@pytest.mark.asyncio
async def test_health_check_degraded(client: AsyncClient, mock_db: MockMongoDBManager):
    class BrokenDB(MockMongoDBManager):
        async def ping(self) -> bool:
            return False

    broken = BrokenDB()
    app.dependency_overrides[get_db] = lambda: broken

    try:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"
        assert data["components"]["database"] == "unavailable"
    finally:
        app.dependency_overrides[get_db] = lambda: mock_db
