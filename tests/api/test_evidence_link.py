"""API tests for POST /api/v1/submissions/{submission_id}/evidence/link and DELETE links."""

import io
from pathlib import Path
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
import pymupdf

from app.core.database import AsyncSessionLocal
from app.models.evidence import EvidenceDocument, EvidenceLink
from app.models.submission import Submission
from app.models.submission_entity import SubmissionEntity
from app.services.definition_service import DefinitionService
from app.services.storage import LocalStorageProvider, get_storage_provider


@pytest.fixture
def temp_storage(tmp_path: Path):
    """Overrides the storage provider dependency to write to an isolated temporary directory."""
    provider = LocalStorageProvider(base_dir=str(tmp_path))
    from app.main import app

    app.dependency_overrides[get_storage_provider] = lambda: provider
    yield provider, tmp_path
    app.dependency_overrides.pop(get_storage_provider, None)


def make_pdf(pages: int = 1, title: str = "Test Cert") -> bytes:
    doc = pymupdf.open()
    for _ in range(pages):
        doc.new_page()
    doc.set_metadata({"title": title})
    return doc.tobytes()


@pytest_asyncio.fixture
async def sample_submission_with_evidence():
    """Seeds a persistent test submission with an uploaded evidence document."""
    async with AsyncSessionLocal() as session:
        svc = DefinitionService()
        await svc.sync_blueprints_to_db(session)
        def_record = await svc.get_definition_from_db(session, "MD-14")
        assert def_record is not None

        sub = Submission(
            id=uuid.uuid4(),
            application_definition_id=def_record.id,
            tracking_code=f"TEST-LINK-{uuid.uuid4().hex[:8].upper()}",
            filing_modality="FRESH",
            device_category="MEDICAL_DEVICE",
            risk_class="CLASS_C",
            status="DRAFT",
            regulatory_context={"is_sterile": True},
        )
        session.add(sub)
        await session.flush()

        pdf_bytes = make_pdf(pages=1, title="ISO 13485 Certificate")
        doc = EvidenceDocument(
            id=uuid.uuid4(),
            submission_id=sub.id,
            document_title="ISO 13485 Quality Certificate",
            original_filename="iso_13485.pdf",
            storage_path=f"submissions/{sub.id}/raw/iso_13485.pdf",
            mime_type="application/pdf",
            file_size_bytes=len(pdf_bytes),
            page_count=1,
            extracted_metadata={"sha256": "fakehash123"},
        )
        session.add(doc)
        await session.commit()
        await session.refresh(sub)
        await session.refresh(doc)
        sub_id = sub.id
        doc_id = doc.id

    yield sub, doc

    # Teardown
    async with AsyncSessionLocal() as session:
        rec = await session.get(Submission, sub_id)
        if rec:
            await session.delete(rec)
            await session.commit()


@pytest.mark.asyncio
async def test_link_evidence_by_slot_id_success(
    async_client: AsyncClient,
    sample_submission_with_evidence,
    temp_storage,
):
    """Verifies linking an evidence document to a slot via slot_id transitions status to SATISFIED."""
    sub, doc = sample_submission_with_evidence

    payload = {
        "document_id": str(doc.id),
        "slot_id": "1.0",
    }

    response = await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json=payload,
    )

    assert response.status_code == 201
    data = response.json()

    assert data["submission_id"] == str(sub.id)
    assert data["evidence_document_id"] == str(doc.id)
    assert data["slot_id"] == "1.0"
    assert data["entity_status"] == "SATISFIED"
    assert data["document_title"] == "ISO 13485 Quality Certificate"
    assert data["original_filename"] == "iso_13485.pdf"

    # Verify DB entity state
    async with AsyncSessionLocal() as session:
        stmt = select(SubmissionEntity).where(
            SubmissionEntity.submission_id == sub.id,
            SubmissionEntity.slot_id == "1.0",
        )
        res = await session.execute(stmt)
        entity = res.scalar_one_or_none()
        assert entity is not None
        assert entity.status == "SATISFIED"


@pytest.mark.asyncio
async def test_link_evidence_by_submission_entity_id_success(
    async_client: AsyncClient,
    sample_submission_with_evidence,
    temp_storage,
):
    """Verifies linking an evidence document directly using submission_entity_id UUID."""
    sub, doc = sample_submission_with_evidence

    # Pre-create entity in DB
    async with AsyncSessionLocal() as session:
        entity = SubmissionEntity(
            id=uuid.uuid4(),
            submission_id=sub.id,
            slot_id="2.0",
            slot_title="TR6 Challan",
            status="MISSING",
        )
        session.add(entity)
        await session.commit()
        entity_id = entity.id

    payload = {
        "document_id": str(doc.id),
        "submission_entity_id": str(entity_id),
    }

    response = await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json=payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["submission_entity_id"] == str(entity_id)
    assert data["slot_id"] == "2.0"
    assert data["entity_status"] == "SATISFIED"


@pytest.mark.asyncio
async def test_link_evidence_with_dossier_chapter(
    async_client: AsyncClient,
    sample_submission_with_evidence,
    temp_storage,
):
    """Verifies associating an evidence document with a specific Fourth Schedule chapter."""
    sub, doc = sample_submission_with_evidence

    payload = {
        "document_id": str(doc.id),
        "slot_id": "10.11",
        "chapter": "DMF_6_2",
    }

    response = await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json=payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["dossier_chapter"] == "DMF_6_2"
    assert data["slot_id"] == "10.11"


@pytest.mark.asyncio
async def test_link_evidence_auto_resolves_dossier_chapter_from_blueprint(
    async_client: AsyncClient,
    sample_submission_with_evidence,
    temp_storage,
):
    """Verifies that dossier_chapter defaults from blueprint when not explicitly provided."""
    sub, doc = sample_submission_with_evidence

    # Slot 10.11 in Form MD-14 has dossier_chapter="DMF_6_2" in blueprint
    payload = {
        "document_id": str(doc.id),
        "slot_id": "10.11",
    }

    response = await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json=payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["dossier_chapter"] == "DMF_6_2"


@pytest.mark.asyncio
async def test_multi_requirement_attachment_tc_ur04_02(
    async_client: AsyncClient,
    sample_submission_with_evidence,
    temp_storage,
):
    """Verifies TC-UR04-02: Single document attached to multiple slots creates distinct links."""
    sub, doc = sample_submission_with_evidence

    # Link 1: Slot 1.0
    res1 = await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json={"document_id": str(doc.id), "slot_id": "1.0"},
    )
    assert res1.status_code == 201
    link1 = res1.json()

    # Link 2: Slot 2.0 (same document)
    res2 = await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json={"document_id": str(doc.id), "slot_id": "2.0"},
    )
    assert res2.status_code == 201
    link2 = res2.json()

    # Confirm distinct links pointing to same document
    assert link1["id"] != link2["id"]
    assert link1["evidence_document_id"] == str(doc.id)
    assert link2["evidence_document_id"] == str(doc.id)
    assert link1["slot_id"] == "1.0"
    assert link2["slot_id"] == "2.0"
    assert link1["entity_status"] == "SATISFIED"
    assert link2["entity_status"] == "SATISFIED"

    # Confirm in database
    async with AsyncSessionLocal() as session:
        stmt = select(EvidenceLink).where(EvidenceLink.evidence_document_id == doc.id)
        res = await session.execute(stmt)
        links = res.scalars().all()
        assert len(links) == 2


@pytest.mark.asyncio
async def test_link_evidence_idempotent_duplicate(
    async_client: AsyncClient,
    sample_submission_with_evidence,
    temp_storage,
):
    """Verifies that calling link endpoint twice with identical parameters is idempotent."""
    sub, doc = sample_submission_with_evidence
    payload = {"document_id": str(doc.id), "slot_id": "1.0"}

    res1 = await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json=payload,
    )
    assert res1.status_code == 201
    link1 = res1.json()

    res2 = await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json=payload,
    )
    assert res2.status_code == 201
    link2 = res2.json()

    # Returns the same link ID
    assert link1["id"] == link2["id"]


@pytest.mark.asyncio
async def test_link_evidence_submission_not_found(
    async_client: AsyncClient,
    sample_submission_with_evidence,
    temp_storage,
):
    """Verifies linking with a non-existent submission ID returns 404 Not Found."""
    _, doc = sample_submission_with_evidence
    bad_sub_id = uuid.uuid4()

    response = await async_client.post(
        f"/api/v1/submissions/{bad_sub_id}/evidence/link",
        json={"document_id": str(doc.id), "slot_id": "1.0"},
    )
    assert response.status_code == 404
    assert f"Submission '{bad_sub_id}' not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_link_evidence_document_not_found(
    async_client: AsyncClient,
    sample_submission_with_evidence,
    temp_storage,
):
    """Verifies linking with a non-existent document ID returns 404 Not Found."""
    sub, _ = sample_submission_with_evidence
    bad_doc_id = uuid.uuid4()

    response = await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json={"document_id": str(bad_doc_id), "slot_id": "1.0"},
    )
    assert response.status_code == 404
    assert "Evidence document" in response.json()["detail"]


@pytest.mark.asyncio
async def test_link_evidence_foreign_document_rejected(
    async_client: AsyncClient,
    sample_submission_with_evidence,
    temp_storage,
):
    """Verifies that linking a document belonging to a different submission returns 404."""
    sub, _ = sample_submission_with_evidence

    # Create second submission with its own document
    async with AsyncSessionLocal() as session:
        svc = DefinitionService()
        def_rec = await svc.get_definition_from_db(session, "MD-14")
        sub2 = Submission(
            id=uuid.uuid4(),
            application_definition_id=def_rec.id,
            tracking_code=f"FOREIGN-{uuid.uuid4().hex[:6]}",
            risk_class="CLASS_A",
        )
        session.add(sub2)
        await session.flush()

        foreign_doc = EvidenceDocument(
            id=uuid.uuid4(),
            submission_id=sub2.id,
            document_title="Foreign Document",
            original_filename="foreign.pdf",
            storage_path="foreign.pdf",
            mime_type="application/pdf",
            file_size_bytes=100,
        )
        session.add(foreign_doc)
        await session.commit()
        foreign_doc_id = foreign_doc.id
        sub2_id = sub2.id

    try:
        # Attempt to link foreign document to sub
        response = await async_client.post(
            f"/api/v1/submissions/{sub.id}/evidence/link",
            json={"document_id": str(foreign_doc_id), "slot_id": "1.0"},
        )
        assert response.status_code == 404
        assert "not found in submission" in response.json()["detail"]
    finally:
        async with AsyncSessionLocal() as session:
            s2 = await session.get(Submission, sub2_id)
            if s2:
                await session.delete(s2)
                await session.commit()


@pytest.mark.asyncio
async def test_link_evidence_invalid_slot_id_rejected(
    async_client: AsyncClient,
    sample_submission_with_evidence,
    temp_storage,
):
    """Verifies that linking to a non-existent slot ID returns 404 Not Found."""
    sub, doc = sample_submission_with_evidence

    response = await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json={"document_id": str(doc.id), "slot_id": "99.99"},
    )
    assert response.status_code == 404
    assert "Checklist slot '99.99' not found in blueprint" in response.json()["detail"]


@pytest.mark.asyncio
async def test_link_evidence_missing_target_validation_error(
    async_client: AsyncClient,
    sample_submission_with_evidence,
    temp_storage,
):
    """Verifies that omitting both slot_id and submission_entity_id raises 422 Unprocessable Entity."""
    sub, doc = sample_submission_with_evidence

    response = await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json={"document_id": str(doc.id)},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unlink_evidence_resets_slot_to_missing(
    async_client: AsyncClient,
    sample_submission_with_evidence,
    temp_storage,
):
    """Verifies that deleting an evidence link resets the target slot status from SATISFIED to MISSING."""
    sub, doc = sample_submission_with_evidence

    # First, link to Slot 1.0
    res_link = await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json={"document_id": str(doc.id), "slot_id": "1.0"},
    )
    assert res_link.status_code == 201
    link_id = res_link.json()["id"]

    # Delete link
    res_del = await async_client.delete(
        f"/api/v1/submissions/{sub.id}/evidence/links/{link_id}",
    )
    assert res_del.status_code == 204

    # Verify entity status reset to MISSING
    async with AsyncSessionLocal() as session:
        stmt = select(SubmissionEntity).where(
            SubmissionEntity.submission_id == sub.id,
            SubmissionEntity.slot_id == "1.0",
        )
        res = await session.execute(stmt)
        entity = res.scalar_one_or_none()
        assert entity is not None
        assert entity.status == "MISSING"

        # Verify link is deleted
        link = await session.get(EvidenceLink, uuid.UUID(link_id))
        assert link is None


@pytest.mark.asyncio
async def test_unlink_evidence_with_multiple_attachments_remains_satisfied(
    async_client: AsyncClient,
    sample_submission_with_evidence,
    temp_storage,
):
    """Verifies that unlinking one document when others remain leaves slot status as SATISFIED."""
    sub, doc1 = sample_submission_with_evidence

    # Create second document
    async with AsyncSessionLocal() as session:
        doc2 = EvidenceDocument(
            id=uuid.uuid4(),
            submission_id=sub.id,
            document_title="Annexure A",
            original_filename="annexure.pdf",
            storage_path="annexure.pdf",
            mime_type="application/pdf",
            file_size_bytes=200,
        )
        session.add(doc2)
        await session.commit()
        doc2_id = doc2.id

    # Link both doc1 and doc2 to slot 1.0
    res_link1 = await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json={"document_id": str(doc1.id), "slot_id": "1.0"},
    )
    link1_id = res_link1.json()["id"]

    await async_client.post(
        f"/api/v1/submissions/{sub.id}/evidence/link",
        json={"document_id": str(doc2_id), "slot_id": "1.0"},
    )

    # Delete only link 1
    res_del = await async_client.delete(
        f"/api/v1/submissions/{sub.id}/evidence/links/{link1_id}",
    )
    assert res_del.status_code == 204

    # Verify entity status remains SATISFIED because doc2 is still linked
    async with AsyncSessionLocal() as session:
        stmt = select(SubmissionEntity).where(
            SubmissionEntity.submission_id == sub.id,
            SubmissionEntity.slot_id == "1.0",
        )
        res = await session.execute(stmt)
        entity = res.scalar_one_or_none()
        assert entity is not None
        assert entity.status == "SATISFIED"
