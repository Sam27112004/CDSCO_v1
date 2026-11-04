"""API tests for /api/v1/profiles endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_profiles_auto_seed(async_client: AsyncClient):
    """Verifies that listing profiles automatically seeds statutory defaults if empty."""
    response = await async_client.get("/api/v1/profiles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3

    types = {p["profile_type"] for p in data}
    assert "INDIAN_AGENT" in types
    assert "FOREIGN_MANUFACTURER" in types
    assert "MANUFACTURING_SITE" in types


@pytest.mark.asyncio
async def test_filter_profiles_by_type(async_client: AsyncClient):
    """Verifies filtering profiles by profile_type query param."""
    response = await async_client.get("/api/v1/profiles?profile_type=INDIAN_AGENT")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for p in data:
        assert p["profile_type"] == "INDIAN_AGENT"


@pytest.mark.asyncio
async def test_create_custom_profile(async_client: AsyncClient):
    """Verifies registering a custom manufacturing profile."""
    payload = {
        "profile_type": "FOREIGN_MANUFACTURER",
        "name": "Bavaria MedTech AG",
        "data_payload": {"country": "Germany", "iso_13485": "CERT-8842"},
    }
    response = await async_client.post("/api/v1/profiles", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Bavaria MedTech AG"
    assert data["data_payload"]["country"] == "Germany"
