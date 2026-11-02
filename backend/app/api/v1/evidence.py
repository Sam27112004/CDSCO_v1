"""Evidence document ingestion and management REST endpoints.

Handles binary multipart PDF uploads, SHA-256 cryptographic verification,
portal ceiling validation, and evidence cataloging under statutory submissions.
"""

from datetime import datetime, timezone
import io
from pathlib import Path
import re
from typing import BinaryIO, Generator, Optional, Tuple
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Path as UrlPath,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.application_definition import ApplicationDefinition
from app.models.evidence import EvidenceDocument, EvidenceLink
from app.models.submission import Submission
from app.models.submission_entity import SubmissionEntity
from app.schemas.evidence import (
    EvidenceDocumentResponse,
    EvidenceLinkCreate,
    EvidenceLinkResponse,
)
from app.services.definition_service import definition_service, DefinitionService
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


@router.post(
    "/submissions/{submission_id}/evidence/link",
    response_model=EvidenceLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Link evidence document to checklist slot or dossier chapter",
)
async def link_evidence_document(
    submission_id: uuid.UUID = UrlPath(
        ...,
        description="Target submission workspace identifier",
    ),
    payload: EvidenceLinkCreate = ...,
    db: AsyncSession = Depends(get_db),
) -> EvidenceLinkResponse:
    """Associates an uploaded evidence document with a discrete portal slot and/or Fourth Schedule chapter.

    Transitions the target slot entity status from MISSING to SATISFIED.
    """
    # 1. Verify target submission
    stmt_sub = select(Submission).where(Submission.id == submission_id)
    res_sub = await db.execute(stmt_sub)
    submission = res_sub.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{submission_id}' not found.",
        )

    # 2. Verify evidence document belongs to this submission
    stmt_doc = select(EvidenceDocument).where(
        EvidenceDocument.id == payload.document_id,
        EvidenceDocument.submission_id == submission_id,
    )
    res_doc = await db.execute(stmt_doc)
    doc = res_doc.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Evidence document '{payload.document_id}' not found "
                f"in submission '{submission_id}'."
            ),
        )

    # 3. Resolve target SubmissionEntity
    entity: Optional[SubmissionEntity] = None
    if payload.submission_entity_id:
        stmt_ent = select(SubmissionEntity).where(
            SubmissionEntity.id == payload.submission_entity_id,
            SubmissionEntity.submission_id == submission_id,
        )
        res_ent = await db.execute(stmt_ent)
        entity = res_ent.scalar_one_or_none()
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Submission entity '{payload.submission_entity_id}' not found "
                    f"in submission '{submission_id}'."
                ),
            )
    elif payload.slot_id:
        stmt_ent = select(SubmissionEntity).where(
            SubmissionEntity.submission_id == submission_id,
            SubmissionEntity.slot_id == payload.slot_id,
        )
        res_ent = await db.execute(stmt_ent)
        entity = res_ent.scalar_one_or_none()

        if not entity:
            # Query blueprint to verify and auto-initialize the slot entity
            app_def = await db.get(ApplicationDefinition, submission.application_definition_id)
            slot_def = None
            if app_def:
                svc = DefinitionService()
                bp = svc.get_blueprint(app_def.code)
                if bp:
                    slot_def = svc.get_slot_by_id(bp, payload.slot_id)

            if not slot_def:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Checklist slot '{payload.slot_id}' not found in blueprint.",
                )

            entity = SubmissionEntity(
                id=uuid.uuid4(),
                submission_id=submission_id,
                slot_id=payload.slot_id,
                slot_title=slot_def.title,
                fulfillment_mode="UPLOAD",
                status="MISSING",
                form_values={},
                updated_at=datetime.now(timezone.utc),
            )
            db.add(entity)
            await db.flush()

    # 4. Determine dossier chapter
    chapter = payload.chapter or payload.dossier_chapter
    if not chapter and entity:
        app_def = await db.get(ApplicationDefinition, submission.application_definition_id)
        if app_def:
            svc = DefinitionService()
            bp = svc.get_blueprint(app_def.code)
            if bp:
                slot_def = svc.get_slot_by_id(bp, entity.slot_id)
                if slot_def and slot_def.dossier_chapter:
                    chapter = slot_def.dossier_chapter

    # 5. Check for existing link (idempotent handling)
    stmt_link = select(EvidenceLink).where(
        EvidenceLink.submission_id == submission_id,
        EvidenceLink.evidence_document_id == doc.id,
        EvidenceLink.submission_entity_id == entity.id,
    )
    res_link = await db.execute(stmt_link)
    existing_link = res_link.scalar_one_or_none()

    if existing_link:
        if chapter and existing_link.dossier_chapter != chapter:
            existing_link.dossier_chapter = chapter
            await db.commit()
            await db.refresh(existing_link)
        link = existing_link
    else:
        link = EvidenceLink(
            id=uuid.uuid4(),
            submission_id=submission_id,
            evidence_document_id=doc.id,
            submission_entity_id=entity.id,
            dossier_chapter=chapter,
            created_at=datetime.now(timezone.utc),
        )
        db.add(link)

    # 6. Update Slot Status to SATISFIED
    entity.status = "SATISFIED"
    entity.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(link)
    await db.refresh(entity)

    return EvidenceLinkResponse(
        id=link.id,
        submission_id=link.submission_id,
        evidence_document_id=link.evidence_document_id,
        submission_entity_id=link.submission_entity_id,
        slot_id=entity.slot_id,
        dossier_chapter=link.dossier_chapter,
        created_at=link.created_at,
        document_title=doc.document_title,
        original_filename=doc.original_filename,
        entity_status=entity.status,
    )


@router.delete(
    "/submissions/{submission_id}/evidence/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink evidence document from slot",
)
async def unlink_evidence_document(
    submission_id: uuid.UUID = UrlPath(
        ...,
        description="Target submission workspace identifier",
    ),
    link_id: uuid.UUID = UrlPath(
        ...,
        description="UUID of evidence link to delete",
    ),
    db: AsyncSession = Depends(get_db),
):
    """Deletes an association between an evidence document and a slot.

    Resets the slot state to MISSING if no other evidence documents remain linked.
    """
    stmt = select(EvidenceLink).where(
        EvidenceLink.id == link_id,
        EvidenceLink.submission_id == submission_id,
    )
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence link '{link_id}' not found in submission '{submission_id}'.",
        )

    entity_id = link.submission_entity_id
    await db.delete(link)
    await db.flush()

    # Check if other documents remain linked to this entity
    stmt_rem = select(EvidenceLink).where(
        EvidenceLink.submission_entity_id == entity_id,
    )
    res_rem = await db.execute(stmt_rem)
    remaining_links = res_rem.scalars().all()

    if not remaining_links:
        entity = await db.get(SubmissionEntity, entity_id)
        if entity:
            entity.status = "MISSING"
            entity.updated_at = datetime.now(timezone.utc)

    await db.commit()
    return None


def parse_range_header(range_header: str, total_size: int) -> Optional[Tuple[int, int]]:
    """Parses an HTTP 'Range: bytes=start-end' header per RFC 7233.

    Returns:
        (start, end) tuple of inclusive byte offsets, or None if invalid or unsatisfiable.
    """
    if not range_header or not range_header.startswith("bytes="):
        return None

    range_val = range_header[6:].strip()
    if "," in range_val:
        range_val = range_val.split(",")[0].strip()

    if "-" not in range_val:
        return None

    start_str, end_str = range_val.split("-", 1)
    start_str = start_str.strip()
    end_str = end_str.strip()

    try:
        if not start_str and end_str:
            suffix_len = int(end_str)
            if suffix_len <= 0:
                return None
            start = max(0, total_size - suffix_len)
            end = total_size - 1
        elif start_str and not end_str:
            start = int(start_str)
            end = total_size - 1
        elif start_str and end_str:
            start = int(start_str)
            end = int(end_str)
        else:
            return None
    except ValueError:
        return None

    if start < 0 or start >= total_size or end < start:
        return None

    end = min(end, total_size - 1)
    return start, end


def stream_range_chunks(
    stream: BinaryIO,
    start: int,
    length: int,
    chunk_size: int = 65536,
) -> Generator[bytes, None, None]:
    """Streams a slice of bytes from a binary stream in chunks, then closes the stream."""
    try:
        try:
            stream.seek(start)
        except (io.UnsupportedOperation, AttributeError, OSError):
            discarded = 0
            while discarded < start:
                chunk = stream.read(min(chunk_size, start - discarded))
                if not chunk:
                    break
                discarded += len(chunk)

        remaining = length
        while remaining > 0:
            chunk = stream.read(min(chunk_size, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk
    finally:
        try:
            stream.close()
        except Exception:
            pass


@router.api_route(
    "/evidence/{document_id}/stream",
    methods=["GET", "HEAD"],
    summary="Stream evidence document with HTTP byte-range support",
)
async def stream_evidence_document(
    document_id: uuid.UUID = UrlPath(
        ...,
        description="Unique identifier of the evidence document to stream",
    ),
    request: Request = ...,
    range: Optional[str] = Header(None, alias="Range"),
    db: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
):
    """Streams an uploaded PDF binary supporting HTTP 206 Partial Content byte ranges

    for responsive, non-blocking rendering in browser PDF.js viewer modals.
    """
    # 1. Query document record from DB
    stmt = select(EvidenceDocument).where(EvidenceDocument.id == document_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence document '{document_id}' not found.",
        )

    # 2. Check storage presence and resolve file size
    if not storage.exists(doc.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physical binary for document '{document_id}' not found in storage.",
        )

    total_size = storage.get_file_size(doc.storage_path)
    safe_filename = re.sub(r"[^\w\.\-]", "_", doc.original_filename)
    mime_type = doc.mime_type or "application/pdf"

    # 3. Handle HEAD probe
    if request.method == "HEAD":
        return Response(
            content=b"",
            status_code=status.HTTP_200_OK,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(total_size),
                "Content-Type": mime_type,
                "Content-Disposition": f'inline; filename="{safe_filename}"',
            },
            media_type=mime_type,
        )

    # 4. Handle Range Requests (HTTP 206 vs HTTP 416)
    if range:
        parsed_range = parse_range_header(range, total_size)
        if parsed_range is None:
            raise HTTPException(
                status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE,
                detail="Requested range is not satisfiable.",
                headers={"Content-Range": f"bytes */{total_size}"},
            )

        start, end = parsed_range
        content_length = end - start + 1
        stream = storage.get_file_stream(doc.storage_path)

        headers = {
            "Content-Range": f"bytes {start}-{end}/{total_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": mime_type,
            "Content-Disposition": f'inline; filename="{safe_filename}"',
        }
        return StreamingResponse(
            content=stream_range_chunks(stream, start, content_length),
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            headers=headers,
            media_type=mime_type,
        )

    # 5. Full Document Stream (HTTP 200 OK)
    stream = storage.get_file_stream(doc.storage_path)
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(total_size),
        "Content-Type": mime_type,
        "Content-Disposition": f'inline; filename="{safe_filename}"',
    }
    return StreamingResponse(
        content=stream_range_chunks(stream, 0, total_size),
        status_code=status.HTTP_200_OK,
        headers=headers,
        media_type=mime_type,
    )


