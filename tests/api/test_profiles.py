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


@pytest.mark.asyncio
async def test_profile_deduplication(async_client: AsyncClient):
    """Verifies that posting an entity with identical name updates existing record rather than duplicating."""
    payload_1 = {
        "profile_type": "FOREIGN_MANUFACTURER",
        "name": "Unique NeuroTech Corp",
        "data_payload": {"country": "Japan", "iso_13485": "ISO-001"},
    }
    res_1 = await async_client.post("/api/v1/profiles", json=payload_1)
    assert res_1.status_code == 201
    id_1 = res_1.json()["id"]

    # Re-post same name with varied whitespace and case
    payload_2 = {
        "profile_type": "FOREIGN_MANUFACTURER",
        "name": "  unique neurotech corp  ",
        "data_payload": {"country": "Japan", "iso_13485": "ISO-001-REVISED"},
    }
    res_2 = await async_client.post("/api/v1/profiles", json=payload_2)
    assert res_2.status_code == 201
    id_2 = res_2.json()["id"]

    # Must be deduplicated to the same UUID
    assert id_1 == id_2
    assert res_2.json()["data_payload"]["iso_13485"] == "ISO-001-REVISED"

    # Query list to verify exactly one record exists
    list_res = await async_client.get("/api/v1/profiles?profile_type=FOREIGN_MANUFACTURER")
    matching = [p for p in list_res.json() if p["name"].lower() == "unique neurotech corp"]
    assert len(matching) == 1


@pytest.mark.asyncio
async def test_profile_rolling_lru_cap(async_client: AsyncClient):
    """Verifies that the directory caps profiles per category at 6, evicting oldest (LRU)."""
    # Create 7 distinct domestic manufacturers
    for i in range(1, 8):
        await async_client.post(
            "/api/v1/profiles",
            json={
                "profile_type": "DOMESTIC_MANUFACTURER",
                "name": f"Rolling Domestic Plant {i}",
                "data_payload": {"index": i},
            },
        )

    # Fetch domestic profiles
    res = await async_client.get("/api/v1/profiles?profile_type=DOMESTIC_MANUFACTURER")
    assert res.status_code == 200
    domestic_profiles = res.json()

    # The maximum number of domestic profiles must be capped at 6
    assert len(domestic_profiles) <= 6

    # The latest created ones (e.g. Plant 7, 6, 5) must be present
    names = [p["name"] for p in domestic_profiles]
    assert "Rolling Domestic Plant 7" in names
    assert "Rolling Domestic Plant 6" in names
