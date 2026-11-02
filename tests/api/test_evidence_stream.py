"""API tests for GET/HEAD /api/v1/evidence/{document_id}/stream with HTTP byte-range support."""

import io
from pathlib import Path
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
import pymupdf

from app.core.database import AsyncSessionLocal
from app.models.evidence import EvidenceDocument
from app.models.submission import Submission
from app.services.definition_service import DefinitionService
from app.services.pdf_inspector import PDFInspector
from app.services.storage import LocalStorageProvider, get_storage_provider


@pytest.fixture
def temp_storage(tmp_path: Path):
    """Overrides the storage provider dependency to write to an isolated temporary directory."""
    provider = LocalStorageProvider(base_dir=str(tmp_path))
    from app.main import app

    app.dependency_overrides[get_storage_provider] = lambda: provider
    yield provider, tmp_path
    app.dependency_overrides.pop(get_storage_provider, None)


def make_test_pdf(pages: int = 3, title: str = "Stream Test Document") -> bytes:
    """Generates a multi-page PDF binary with text content for byte-range testing."""
    doc = pymupdf.open()
    for idx in range(pages):
        page = doc.new_page(width=595.0, height=842.0)
        page.insert_text((50, 50), f"Section {idx + 1}: Technical Report Content for Range Testing")
        page.insert_text((50, 100), "A" * 200)  # Add filler text
    doc.set_metadata({"title": title})
    return doc.tobytes()


@pytest_asyncio.fixture
async def sample_document_with_file(temp_storage):
    """Seeds a persistent test submission, creates a physical PDF on disk, and records EvidenceDocument in DB."""
    provider, tmp_path = temp_storage
    pdf_bytes = make_test_pdf(pages=3, title="Audit Report")

    async with AsyncSessionLocal() as session:
        svc = DefinitionService()
        await svc.sync_blueprints_to_db(session)
        def_rec = await svc.get_definition_from_db(session, "MD-14")

        sub = Submission(
            id=uuid.uuid4(),
            application_definition_id=def_rec.id,
            tracking_code=f"STREAM-{uuid.uuid4().hex[:6].upper()}",
            risk_class="CLASS_C",
        )
        session.add(sub)
        await session.flush()

        doc_id = uuid.uuid4()
        storage_path = f"submissions/{sub.id}/raw/{doc_id}_audit_report.pdf"
        # Save physically to storage provider
        provider.save_file(io.BytesIO(pdf_bytes), storage_path)

        doc = EvidenceDocument(
            id=doc_id,
            submission_id=sub.id,
            document_title="Audit Report",
            original_filename="audit_report.pdf",
            storage_path=storage_path,
            mime_type="application/pdf",
            file_size_bytes=len(pdf_bytes),
            page_count=3,
            extracted_metadata={"sha256": "sample_hash"},
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        sub_id = sub.id

    yield doc, pdf_bytes, provider

    # Teardown
    async with AsyncSessionLocal() as session:
        rec = await session.get(Submission, sub_id)
        if rec:
            await session.delete(rec)
            await session.commit()


@pytest.mark.asyncio
async def test_stream_full_file_200_ok(
    async_client: AsyncClient,
    sample_document_with_file,
):
    """Verifies standard GET request without Range header returns full content and 200 OK."""
    doc, pdf_bytes, _ = sample_document_with_file

    response = await async_client.get(f"/api/v1/evidence/{doc.id}/stream")

    assert response.status_code == 200
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-length"] == str(len(pdf_bytes))
    assert response.headers["content-type"] == "application/pdf"
    assert 'inline; filename="audit_report.pdf"' in response.headers["content-disposition"]
    assert response.content == pdf_bytes


@pytest.mark.asyncio
async def test_stream_closed_byte_range_206_partial_content(
    async_client: AsyncClient,
    sample_document_with_file,
):
    """Verifies requesting bytes=0-100 returns exact 101 bytes and 206 Partial Content."""
    doc, pdf_bytes, _ = sample_document_with_file
    total_size = len(pdf_bytes)

    headers = {"Range": "bytes=0-100"}
    response = await async_client.get(
        f"/api/v1/evidence/{doc.id}/stream",
        headers=headers,
    )

    assert response.status_code == 206
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-range"] == f"bytes 0-100/{total_size}"
    assert response.headers["content-length"] == "101"
    assert response.content == pdf_bytes[0:101]


@pytest.mark.asyncio
async def test_stream_mid_file_byte_range_206(
    async_client: AsyncClient,
    sample_document_with_file,
):
    """Verifies requesting an arbitrary internal slice bytes=50-250 returns 206 Partial Content."""
    doc, pdf_bytes, _ = sample_document_with_file
    total_size = len(pdf_bytes)

    headers = {"Range": "bytes=50-250"}
    response = await async_client.get(
        f"/api/v1/evidence/{doc.id}/stream",
        headers=headers,
    )

    assert response.status_code == 206
    assert response.headers["content-range"] == f"bytes 50-250/{total_size}"
    assert response.headers["content-length"] == "201"
    assert response.content == pdf_bytes[50:251]


@pytest.mark.asyncio
async def test_stream_open_ended_range_206(
    async_client: AsyncClient,
    sample_document_with_file,
):
    """Verifies requesting bytes=200- streams from byte 200 to EOF."""
    doc, pdf_bytes, _ = sample_document_with_file
    total_size = len(pdf_bytes)

    headers = {"Range": "bytes=200-"}
    response = await async_client.get(
        f"/api/v1/evidence/{doc.id}/stream",
        headers=headers,
    )

    assert response.status_code == 206
    assert response.headers["content-range"] == f"bytes 200-{total_size - 1}/{total_size}"
    assert response.headers["content-length"] == str(total_size - 200)
    assert response.content == pdf_bytes[200:]


@pytest.mark.asyncio
async def test_stream_suffix_range_206(
    async_client: AsyncClient,
    sample_document_with_file,
):
    """Verifies requesting suffix bytes=-100 streams the last 100 bytes (for PDF trailers)."""
    doc, pdf_bytes, _ = sample_document_with_file
    total_size = len(pdf_bytes)

    headers = {"Range": "bytes=-100"}
    response = await async_client.get(
        f"/api/v1/evidence/{doc.id}/stream",
        headers=headers,
    )

    assert response.status_code == 206
    expected_start = total_size - 100
    assert response.headers["content-range"] == f"bytes {expected_start}-{total_size - 1}/{total_size}"
    assert response.headers["content-length"] == "100"
    assert response.content == pdf_bytes[-100:]


@pytest.mark.asyncio
async def test_stream_range_overflow_capped_to_eof_206(
    async_client: AsyncClient,
    sample_document_with_file,
):
    """Verifies requesting a range that extends past EOF is capped to total_size - 1."""
    doc, pdf_bytes, _ = sample_document_with_file
    total_size = len(pdf_bytes)

    headers = {"Range": f"bytes=50-{total_size + 5000}"}
    response = await async_client.get(
        f"/api/v1/evidence/{doc.id}/stream",
        headers=headers,
    )

    assert response.status_code == 206
    assert response.headers["content-range"] == f"bytes 50-{total_size - 1}/{total_size}"
    assert response.content == pdf_bytes[50:]


@pytest.mark.asyncio
async def test_stream_unsatisfiable_range_416(
    async_client: AsyncClient,
    sample_document_with_file,
):
    """Verifies requesting a range starting beyond EOF returns 416 Range Not Satisfiable."""
    doc, pdf_bytes, _ = sample_document_with_file
    total_size = len(pdf_bytes)

    headers = {"Range": f"bytes={total_size + 100}-{total_size + 200}"}
    response = await async_client.get(
        f"/api/v1/evidence/{doc.id}/stream",
        headers=headers,
    )

    assert response.status_code == 416
    assert response.headers["content-range"] == f"bytes */{total_size}"


@pytest.mark.asyncio
async def test_stream_inverted_range_416(
    async_client: AsyncClient,
    sample_document_with_file,
):
    """Verifies requesting an inverted range (start > end) returns 416 Range Not Satisfiable."""
    doc, pdf_bytes, _ = sample_document_with_file
    total_size = len(pdf_bytes)

    headers = {"Range": "bytes=300-100"}
    response = await async_client.get(
        f"/api/v1/evidence/{doc.id}/stream",
        headers=headers,
    )

    assert response.status_code == 416
    assert response.headers["content-range"] == f"bytes */{total_size}"


@pytest.mark.asyncio
async def test_stream_head_request_probe(
    async_client: AsyncClient,
    sample_document_with_file,
):
    """Verifies HEAD request probe returns metadata headers with empty body for PDF.js."""
    doc, pdf_bytes, _ = sample_document_with_file

    response = await async_client.head(f"/api/v1/evidence/{doc.id}/stream")

    assert response.status_code == 200
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-length"] == str(len(pdf_bytes))
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) == 0


@pytest.mark.asyncio
async def test_stream_document_not_found_404(
    async_client: AsyncClient,
    sample_document_with_file,
):
    """Verifies requesting a non-existent document ID returns 404 Not Found."""
    bad_id = uuid.uuid4()
    response = await async_client.get(f"/api/v1/evidence/{bad_id}/stream")
    assert response.status_code == 404
    assert f"Evidence document '{bad_id}' not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_stream_missing_physical_file_404(
    async_client: AsyncClient,
    sample_document_with_file,
):
    """Verifies that if database record exists but physical file is absent, 404 is returned."""
    doc, _, provider = sample_document_with_file

    # Delete physical file from storage without deleting DB record
    provider.delete_file(doc.storage_path)

    response = await async_client.get(f"/api/v1/evidence/{doc.id}/stream")
    assert response.status_code == 404
    assert "Physical binary for document" in response.json()["detail"]
