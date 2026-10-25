import pytest
from httpx import AsyncClient
from app.main import app
from app.core.database import get_db


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Verifies gateway root route responds with 200 OK and expected keys."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert "version" in data
    assert data["docs_url"] == "/docs"


@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient):
    """Verifies health check endpoint returns 200 OK and conforms to schema."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "project_name" in data
    assert "database_connected" in data
    assert "timestamp" in data
    assert data["status"] in ["healthy", "degraded"]


@pytest.mark.asyncio
async def test_health_check_with_mocked_db(async_client: AsyncClient):
    """Verifies health check returns 'healthy' when database responds successfully."""
    class DummyScalarResult:
        def scalar(self):
            return 1

    class MockAsyncSession:
        async def execute(self, statement):
            return DummyScalarResult()

    async def override_get_db():
        yield MockAsyncSession()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database_connected"] is True
    finally:
        app.dependency_overrides.clear()
