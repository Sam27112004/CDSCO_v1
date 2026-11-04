"""API integration tests for /api/v1/submissions endpoints."""

import uuid
import pytest
from httpx import AsyncClient

from app.core.database import AsyncSessionLocal
from app.models.submission import Submission
from app.services.definition_service import DefinitionService


@pytest.mark.asyncio
async def test_list_submissions_empty(async_client: AsyncClient):
    """Verifies that listing submissions returns an array without error."""
    response = await async_client.get("/api/v1/submissions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_submission_md14_generates_slots(async_client: AsyncClient):
    """Verifies creating an MD-14 submission initializes statutory slots and returns summary."""
    payload = {
        "pathway_code": "MD-14",
        "filing_modality": "FRESH",
        "device_category": "MEDICAL_DEVICE",
        "risk_class": "CLASS_C",
        "device_family_name": "Orthopedic Pedicle Screw System",
        "regulatory_context": {"is_sterile": True},
    }

    response = await async_client.post("/api/v1/submissions", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["pathway_code"] == "MD-14"
    assert data["device_family_name"] == "Orthopedic Pedicle Screw System"
    assert data["risk_class"] == "CLASS_C"
    assert data["status"] == "DRAFT"
    assert data["total_slots"] == 36  # MD-14 has 36 slots
    assert data["satisfied_slots"] == 0
    assert data["progress_percent"] == 0
    assert len(data["entities"]) == 36

    # Verify slots are properly populated
    slot_ids = [e["slot_id"] for e in data["entities"]]
    assert "1.0" in slot_ids
    assert "4.0" in slot_ids
    assert "10.1" in slot_ids

    # Cleanup
    sub_id = data["id"]
    del_res = await async_client.delete(f"/api/v1/submissions/{sub_id}")
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_create_submission_md7_generates_slots(async_client: AsyncClient):
    """Verifies creating an MD-7 submission initializes statutory slots (48 slots)."""
    payload = {
        "pathway_code": "MD-7",
        "filing_modality": "FRESH",
        "device_category": "MEDICAL_DEVICE",
        "risk_class": "CLASS_D",
        "device_family_name": "Drug-Eluting Coronary Stent",
        "regulatory_context": {"is_sterile": True},
    }

    response = await async_client.post("/api/v1/submissions", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["pathway_code"] == "MD-7"
    assert data["total_slots"] == 48  # MD-7 has 48 slots
    assert len(data["entities"]) == 48

    # Cleanup
    await async_client.delete(f"/api/v1/submissions/{data['id']}")


@pytest.mark.asyncio
async def test_get_submission_detail(async_client: AsyncClient):
    """Verifies fetching submission by ID returns full entity tree."""
    # Create submission
    payload = {
        "pathway_code": "MD-14",
        "filing_modality": "FRESH",
        "device_category": "MEDICAL_DEVICE",
        "risk_class": "CLASS_B",
    }
    create_res = await async_client.post("/api/v1/submissions", json=payload)
    sub_id = create_res.json()["id"]

    # Get submission
    get_res = await async_client.get(f"/api/v1/submissions/{sub_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == sub_id
    assert data["risk_class"] == "CLASS_B"

    # Cleanup
    await async_client.delete(f"/api/v1/submissions/{sub_id}")


@pytest.mark.asyncio
async def test_get_submission_not_found(async_client: AsyncClient):
    """Verifies 404 for non-existent submission ID."""
    random_id = uuid.uuid4()
    response = await async_client.get(f"/api/v1/submissions/{random_id}")
    assert response.status_code == 404
    assert f"Submission '{random_id}' not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_submission_not_found(async_client: AsyncClient):
    """Verifies 404 when deleting non-existent submission."""
    random_id = uuid.uuid4()
    response = await async_client.delete(f"/api/v1/submissions/{random_id}")
    assert response.status_code == 404
