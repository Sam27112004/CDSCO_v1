"""API tests for POST /api/v1/submissions/{submission_id}/evidence/upload endpoint."""

import hashlib
import io
from pathlib import Path
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.main import app
from app.models.evidence import EvidenceDocument
from app.models.submission import Submission
from app.services.definition_service import DefinitionService
from app.services.storage import LocalStorageProvider, get_storage_provider
import docx
from PIL import Image
import pymupdf


def make_sample_pdf(
    pages: int = 1,
    title: str = "",
    encrypt: bool = False,
    password: str = "pass123",
) -> bytes:
    """Helper generating memory-buffered PDF binaries with configurable attributes."""
    doc = pymupdf.open()
    for _ in range(pages):
        doc.new_page(width=595.0, height=842.0)
    if title:
        doc.set_metadata({"title": title, "creator": "CDSCO Test Suite"})
    if encrypt:
        return doc.tobytes(
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw=password,
            user_pw=password,
        )
    return doc.tobytes()


@pytest.fixture
def temp_storage(tmp_path: Path):
    """Overrides the storage provider dependency to write to an isolated temporary directory."""
    provider = LocalStorageProvider(base_dir=str(tmp_path))
    app.dependency_overrides[get_storage_provider] = lambda: provider
    yield provider, tmp_path
    app.dependency_overrides.pop(get_storage_provider, None)


@pytest_asyncio.fixture
async def sample_submission():
    """Seeds a persistent test submission in PostgreSQL and ensures clean teardown."""
    async with AsyncSessionLocal() as session:
        # Ensure MD-14 definition exists in DB
        svc = DefinitionService()
        await svc.sync_blueprints_to_db(session)
        def_record = await svc.get_definition_from_db(session, "MD-14")
        assert def_record is not None

        sub = Submission(
            id=uuid.uuid4(),
            application_definition_id=def_record.id,
            tracking_code=f"TEST-TRACK-{uuid.uuid4().hex[:8].upper()}",
            filing_modality="FRESH",
            device_category="MEDICAL_DEVICE",
            risk_class="CLASS_C",
            status="DRAFT",
            regulatory_context={"is_sterile": True},
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)
        submission_id = sub.id

    yield sub

    # Teardown: delete submission (cascades to evidence documents)
    async with AsyncSessionLocal() as session:
        record = await session.get(Submission, submission_id)
        if record:
            await session.delete(record)
            await session.commit()


# Valid 1-page sample PDF binary
VALID_PDF_BYTES = make_sample_pdf(pages=1, title="Test Document")
VALID_PDF_SHA256 = hashlib.sha256(VALID_PDF_BYTES).hexdigest()


@pytest.mark.asyncio
async def test_evidence_upload_success(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies successful PDF upload, SHA-256 calculation, storage save, and DB persistence."""
    provider, tmp_path = temp_storage
    submission_id = sample_submission.id

    files = {
        "file": ("iso_13485_certificate.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")
    }
    data = {
        "document_title": "ISO 13485:2016 Quality Management Certificate"
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
        data=data,
    )

    assert response.status_code == 201
    res_data = response.json()

    assert res_data["submission_id"] == str(submission_id)
    assert res_data["document_title"] == "ISO 13485:2016 Quality Management Certificate"
    assert res_data["original_filename"] == "iso_13485_certificate.pdf"
    assert res_data["mime_type"] == "application/pdf"
    assert res_data["file_size_bytes"] == len(VALID_PDF_BYTES)
    assert res_data["page_count"] == 1
    assert res_data["extracted_metadata"]["sha256"] == VALID_PDF_SHA256

    # Verify binary physically saved in storage provider
    storage_path = res_data["storage_path"]
    assert provider.exists(storage_path)
    assert provider.get_file_size(storage_path) == len(VALID_PDF_BYTES)

    # Verify database persistence
    async with AsyncSessionLocal() as session:
        doc = await session.get(EvidenceDocument, uuid.UUID(res_data["id"]))
        assert doc is not None
        assert doc.submission_id == submission_id
        assert doc.extracted_metadata["sha256"] == VALID_PDF_SHA256


@pytest.mark.asyncio
async def test_evidence_upload_default_title_from_filename(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies that document_title defaults to clean filename when omitted from form-data."""
    submission_id = sample_submission.id

    files = {
        "file": ("clinical_evaluation_v2.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
    )

    assert response.status_code == 201
    res_data = response.json()
    assert res_data["document_title"] == "clinical_evaluation_v2.pdf"
    assert res_data["original_filename"] == "clinical_evaluation_v2.pdf"


@pytest.mark.asyncio
async def test_evidence_upload_duplicate_detection_hash_consistency(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies TC-UR04-01: Uploading an identical binary produces matching SHA-256 digests."""
    submission_id = sample_submission.id

    # First upload
    res1 = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files={"file": ("cert_copy_1.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")},
    )
    assert res1.status_code == 201
    doc1 = res1.json()

    # Second upload with different filename but identical binary
    res2 = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files={"file": ("cert_copy_2.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")},
    )
    assert res2.status_code == 201
    doc2 = res2.json()

    # Distinct records
    assert doc1["id"] != doc2["id"]
    assert doc1["storage_path"] != doc2["storage_path"]
    # Identical cryptographic checksum
    assert doc1["extracted_metadata"]["sha256"] == doc2["extracted_metadata"]["sha256"]
    assert doc1["extracted_metadata"]["sha256"] == VALID_PDF_SHA256


@pytest.mark.asyncio
async def test_evidence_upload_submission_not_found(
    async_client: AsyncClient,
    temp_storage,
):
    """Verifies that uploading to a non-existent submission returns 404 Not Found."""
    non_existent_id = uuid.uuid4()
    files = {
        "file": ("test.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")
    }

    response = await async_client.post(
        f"/api/v1/submissions/{non_existent_id}/evidence/upload",
        files=files,
    )

    assert response.status_code == 404
    assert f"Submission '{non_existent_id}' not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_evidence_upload_non_pdf_rejected(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies that non-PDF extensions are rejected with 400 Bad Request."""
    submission_id = sample_submission.id
    files = {
        "file": ("malicious_executable.exe", io.BytesIO(b"MZ executable content"), "application/octet-stream")
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
    )

    assert response.status_code == 400
    assert "Invalid file format '.exe'" in response.json()["detail"]


@pytest.mark.asyncio
async def test_evidence_upload_invalid_magic_bytes_rejected(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies that a file named .pdf but without %PDF magic bytes is rejected."""
    submission_id = sample_submission.id
    fake_bytes = b"NOT_A_REAL_PDF_JUST_RANDOM_TEXT_DATA"
    files = {
        "file": ("spoofed.pdf", io.BytesIO(fake_bytes), "application/pdf")
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
    )

    assert response.status_code == 400
    assert "%PDF" in response.json()["detail"]


@pytest.mark.asyncio
async def test_evidence_upload_empty_file_rejected(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies that empty files (0 bytes) are rejected with 400 Bad Request."""
    submission_id = sample_submission.id
    files = {
        "file": ("empty.pdf", io.BytesIO(b""), "application/pdf")
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
    )

    assert response.status_code == 400
    assert "empty (0 bytes)" in response.json()["detail"]


@pytest.mark.asyncio
async def test_evidence_upload_exceeds_max_size_ceiling(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies that uploads exceeding MAX_FILE_SIZE_BYTES are rejected with 413 Payload Too Large."""
    submission_id = sample_submission.id

    # Temporarily set MAX_FILE_SIZE_BYTES to 10 bytes to trigger ceiling without allocating 10MB
    with patch.object(settings, "MAX_FILE_SIZE_BYTES", 10):
        files = {
            "file": ("oversized.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")
        }
        response = await async_client.post(
            f"/api/v1/submissions/{submission_id}/evidence/upload",
            files=files,
        )

    assert response.status_code == 413
    assert "exceeds maximum allowable portal limit" in response.json()["detail"]


@pytest.mark.asyncio
async def test_evidence_upload_filename_sanitization(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies that filenames with spaces and special characters are safely sanitized."""
    submission_id = sample_submission.id
    files = {
        "file": ("Risk Assessment (v2.1) [Final #1].pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
    )

    assert response.status_code == 201
    res_data = response.json()
    storage_path = res_data["storage_path"]

    # Verify no spaces, brackets, or pound signs in stored path
    filename_part = storage_path.split("/")[-1]
    assert " " not in filename_part
    assert "[" not in filename_part
    assert "]" not in filename_part
    assert "#" not in filename_part


@pytest.mark.asyncio
async def test_evidence_upload_db_error_triggers_storage_cleanup(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies transactional compensating action: if database commit fails, stored binary is cleaned up."""
    provider, tmp_path = temp_storage
    submission_id = sample_submission.id

    files = {
        "file": ("test_rollback.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")
    }

    with patch.object(AsyncSession, "commit", side_effect=Exception("DB simulated crash")):
        with pytest.raises(Exception, match="DB simulated crash"):
            await async_client.post(
                f"/api/v1/submissions/{submission_id}/evidence/upload",
                files=files,
            )

    # Confirm no orphaned files remain in temp storage
    saved_files = list(tmp_path.glob("**/*.pdf"))
    assert len(saved_files) == 0


@pytest.mark.asyncio
async def test_evidence_upload_encrypted_pdf_rejected(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies that password-locked or encrypted PDFs are rejected with 400 Bad Request."""
    submission_id = sample_submission.id
    encrypted_bytes = make_sample_pdf(pages=1, encrypt=True, password="secret_password")

    files = {
        "file": ("encrypted_certificate.pdf", io.BytesIO(encrypted_bytes), "application/pdf")
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
    )

    assert response.status_code == 400
    assert "Password-protected or encrypted PDF documents are not supported" in response.json()["detail"]


@pytest.mark.asyncio
async def test_evidence_upload_corrupted_pdf_rejected(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies that malformed or corrupted PDF binaries are rejected with 400 Bad Request."""
    submission_id = sample_submission.id
    corrupted_bytes = b"%PDF-1.4\x00\xff\xfe\xca\xfe\xba\xbe unreadable_corrupted_stream_data"

    files = {
        "file": ("corrupted_report.pdf", io.BytesIO(corrupted_bytes), "application/pdf")
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
    )

    assert response.status_code == 400
    assert "Corrupted or invalid PDF binary" in response.json()["detail"]


@pytest.mark.asyncio
async def test_evidence_upload_multi_page_extraction_tc_ur02_01(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies TC-UR02-01: Uploading a 3-page PDF accurately records page_count: 3 and page geometries."""
    submission_id = sample_submission.id
    three_page_bytes = make_sample_pdf(pages=3, title="ISO 13485 Multi-Page Audit")
    three_page_sha256 = hashlib.sha256(three_page_bytes).hexdigest()

    files = {
        "file": ("sample_iso.pdf", io.BytesIO(three_page_bytes), "application/pdf")
    }
    data = {
        "document_title": "ISO 13485 Full Audit Dossier"
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
        data=data,
    )

    assert response.status_code == 201
    res_data = response.json()

    assert res_data["page_count"] == 3
    assert res_data["file_size_bytes"] == len(three_page_bytes)
    assert res_data["extracted_metadata"]["sha256"] == three_page_sha256
    assert res_data["extracted_metadata"]["pdf_version"] in ("1.7", "1.4", "1.5", "1.6")
    assert res_data["extracted_metadata"]["is_encrypted"] is False
    assert res_data["extracted_metadata"]["title"] == "ISO 13485 Multi-Page Audit"

    page_dims = res_data["extracted_metadata"]["page_dimensions"]
    assert len(page_dims) == 3
    assert page_dims[0]["page_number"] == 1
    assert page_dims[0]["width"] == 595.0
    assert page_dims[0]["height"] == 842.0
    assert page_dims[0]["is_portrait"] is True


@pytest.mark.asyncio
async def test_evidence_upload_jpg_image_auto_converted_to_pdf(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies that uploading a JPEG image automatically converts it into a valid PDF."""
    submission_id = sample_submission.id

    img = Image.new("RGB", (600, 400), color=(100, 149, 237))
    img_buf = io.BytesIO()
    img.save(img_buf, format="JPEG")
    img_bytes = img_buf.getvalue()

    files = {
        "file": ("factory_site.jpg", io.BytesIO(img_bytes), "image/jpeg")
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
    )

    assert response.status_code == 201
    doc = response.json()

    assert doc["original_filename"] == "factory_site.jpg"
    assert doc["mime_type"] == "application/pdf"
    assert doc["page_count"] == 1
    assert doc["storage_path"].endswith(".pdf")
    assert doc["extracted_metadata"]["converted"] is True
    assert doc["extracted_metadata"]["source_format"] == "jpg"
    assert "sha256" in doc["extracted_metadata"]


@pytest.mark.asyncio
async def test_evidence_upload_png_image_auto_converted_to_pdf(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies that uploading a PNG image with transparency converts cleanly to PDF."""
    submission_id = sample_submission.id

    img = Image.new("RGBA", (300, 300), color=(255, 0, 0, 128))
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_bytes = img_buf.getvalue()

    files = {
        "file": ("device_label.png", io.BytesIO(img_bytes), "image/png")
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
    )

    assert response.status_code == 201
    doc = response.json()

    assert doc["original_filename"] == "device_label.png"
    assert doc["mime_type"] == "application/pdf"
    assert doc["page_count"] == 1
    assert doc["storage_path"].endswith(".pdf")
    assert doc["extracted_metadata"]["converted"] is True
    assert doc["extracted_metadata"]["source_format"] == "png"


@pytest.mark.asyncio
async def test_evidence_upload_docx_auto_converted_to_pdf(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies that uploading a Word .docx automatically converts into a standardized PDF."""
    submission_id = sample_submission.id

    doc = docx.Document()
    doc.add_heading("Statutory Undertaking (Form MD-14)", level=0)
    doc.add_paragraph("We hereby declare that all technical information submitted is accurate.")
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Clause"
    table.cell(0, 1).text = "Compliance"
    table.cell(1, 0).text = "Rule 34(1)"
    table.cell(1, 1).text = "Full Compliance"

    docx_buf = io.BytesIO()
    doc.save(docx_buf)
    docx_bytes = docx_buf.getvalue()

    files = {
        "file": ("undertaking.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
    )

    assert response.status_code == 201
    res_data = response.json()

    assert res_data["original_filename"] == "undertaking.docx"
    assert res_data["mime_type"] == "application/pdf"
    assert res_data["page_count"] >= 1
    assert res_data["storage_path"].endswith(".pdf")
    assert res_data["extracted_metadata"]["converted"] is True
    assert res_data["extracted_metadata"]["source_format"] == "docx"


@pytest.mark.asyncio
async def test_evidence_upload_corrupted_image_rejected(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies that corrupted image bytes with .jpg extension are rejected with 400 Bad Request."""
    submission_id = sample_submission.id
    files = {
        "file": ("corrupted.jpg", io.BytesIO(b"NOT_A_REAL_IMAGE_DATA"), "image/jpeg")
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
    )

    assert response.status_code == 400
    assert "Unidentified or invalid image" in response.json()["detail"]


@pytest.mark.asyncio
async def test_evidence_upload_corrupted_docx_rejected(
    async_client: AsyncClient,
    sample_submission: Submission,
    temp_storage,
):
    """Verifies that corrupted docx bytes with .docx extension are rejected with 400 Bad Request."""
    submission_id = sample_submission.id
    files = {
        "file": ("corrupted.docx", io.BytesIO(b"NOT_A_REAL_DOCX_DATA"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }

    response = await async_client.post(
        f"/api/v1/submissions/{submission_id}/evidence/upload",
        files=files,
    )

    assert response.status_code == 400
    assert "Failed to convert Word document" in response.json()["detail"]

