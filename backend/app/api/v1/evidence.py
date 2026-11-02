"""Evidence document ingestion and management REST endpoints.

Handles binary multipart PDF uploads, SHA-256 cryptographic verification,
portal ceiling validation, and evidence cataloging under statutory submissions.
"""

from datetime import datetime, timezone
import io
from pathlib import Path
import re
from typing import Optional
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path as UrlPath,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.evidence import EvidenceDocument
from app.models.submission import Submission
from app.schemas.evidence import EvidenceDocumentResponse
from app.services.pdf_inspector import (
    PDFInspector,
    PdfCorruptedError,
    PdfEmptyError,
    PdfEncryptedError,
)
from app.services.storage import StorageProvider, calculate_sha256, get_storage_provider

router = APIRouter(tags=["Evidence Documents"])


@router.post(
    "/submissions/{submission_id}/evidence/upload",
    response_model=EvidenceDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload binary PDF evidence file",
)
async def upload_evidence_document(
    submission_id: uuid.UUID = UrlPath(
        ...,
        description="Target submission workspace identifier",
    ),
    file: UploadFile = File(
        ...,
        description="Binary PDF evidence document",
    ),
    document_title: Optional[str] = Form(
        None,
        description="Optional human-readable title for the uploaded document",
    ),
    db: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> EvidenceDocumentResponse:
    """Accepts a multipart PDF upload, validates file size and format, computes SHA-256,

    persists binary to the submission raw vault, and records the evidence entity in PostgreSQL.
    """
    # 1. Verify target submission exists
    stmt = select(Submission).where(Submission.id == submission_id)
    result = await db.execute(stmt)
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{submission_id}' not found.",
        )

    # 2. Validate file existence and filename
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided or filename is missing.",
        )

    clean_filename = Path(file.filename).name.strip()
    if not clean_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty.",
        )

    # 3. Validate file extension (.pdf)
    if not clean_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files (.pdf) are permitted.",
        )

    # 4. Inspect file size and enforce 10MB ceiling
    file.file.seek(0, io.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=(
                f"File size ({file_size} bytes) exceeds maximum allowable "
                f"portal limit of {settings.MAX_FILE_SIZE_BYTES} bytes (10.0 MB)."
            ),
        )

    # 5. Validate PDF header magic bytes (%PDF)
    header = file.file.read(4)
    file.file.seek(0)
    if header != b"%PDF":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. File does not start with standard PDF header (%PDF).",
        )

    # 6. Deep pre-flight structural inspection via PyMuPDF (fitz)
    try:
        inspection = PDFInspector.inspect(file.file)
    except PdfEncryptedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except (PdfCorruptedError, PdfEmptyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to inspect PDF document: {str(exc)}",
        )

    # 7. Compute cryptographic SHA-256 checksum
    sha256_checksum = calculate_sha256(file.file)

    # 8. Construct isolated storage path
    evidence_id = uuid.uuid4()
    safe_filename = re.sub(r"[^\w\.\-]", "_", clean_filename)
    storage_path = f"submissions/{submission_id}/raw/{evidence_id}_{safe_filename}"

    # 9. Save binary into storage provider
    stored_path = storage.save_file(file.file, storage_path)

    # 10. Determine document title
    title = (
        document_title.strip()
        if document_title and document_title.strip()
        else clean_filename
    )

    # 11. Record metadata in PostgreSQL
    doc = EvidenceDocument(
        id=evidence_id,
        submission_id=submission_id,
        document_title=title,
        original_filename=clean_filename,
        storage_path=stored_path,
        mime_type="application/pdf",
        file_size_bytes=file_size,
        page_count=inspection.page_count,
        extracted_metadata={
            "sha256": sha256_checksum,
            "pdf_version": inspection.pdf_version,
            "is_encrypted": inspection.is_encrypted,
            "title": inspection.title,
            "author": inspection.author,
            "creator": inspection.creator,
            "producer": inspection.producer,
            "creation_date": inspection.creation_date,
            "modification_date": inspection.modification_date,
            "page_dimensions": [p.model_dump() for p in inspection.page_dimensions],
        },
        uploaded_at=datetime.now(timezone.utc),
    )

    try:
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
    except Exception:
        await db.rollback()
        try:
            storage.delete_file(storage_path)
        except Exception:
            pass
        raise

    return doc
