"""Submissions Management REST API endpoints.

Handles creation, retrieval, and portfolio dashboard metrics for CDSCO statutory filings.
"""

from datetime import datetime, timezone
import random
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path as UrlPath, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.application_definition import ApplicationDefinition
from app.models.evidence import EvidenceLink
from app.models.submission import Submission
from app.models.submission_entity import SubmissionEntity
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionDetailResponse,
    SubmissionSummaryResponse,
)
from app.services.definition_service import definition_service

router = APIRouter(prefix="/submissions", tags=["Submissions"])


def _build_entity_response(entity: SubmissionEntity, slot_map: dict) -> dict:
    """Helper formatting slot entity with blueprint regulatory guidance and evidence links."""
    slot_bp = slot_map.get(entity.slot_id, {})
    return {
        "id": entity.id,
        "submission_id": entity.submission_id,
        "slot_id": entity.slot_id,
        "slot_title": entity.slot_title,
        "fulfillment_mode": entity.fulfillment_mode,
        "status": entity.status,
        "form_values": entity.form_values or {},
        "category": slot_bp.get("category"),
        "chapter": slot_bp.get("chapter"),
        "is_mandatory": slot_bp.get("is_mandatory", True),
        "guidance": slot_bp.get("guidance"),
        "evidence_links": [
            {
                "id": link.id,
                "submission_id": link.submission_id,
                "evidence_document_id": link.evidence_document_id,
                "submission_entity_id": link.submission_entity_id,
                "dossier_chapter": link.dossier_chapter,
                "created_at": link.created_at,
                "document_title": link.document.document_title if link.document else None,
                "original_filename": link.document.original_filename if link.document else None,
                "file_size_bytes": link.document.file_size_bytes if link.document else None,
                "page_count": link.document.page_count if link.document else None,
            }
            for link in (entity.evidence_links or [])
        ],
        "updated_at": entity.updated_at,
    }


def _build_summary_response(sub: Submission) -> SubmissionSummaryResponse:
    """Helper calculating progress percentages and slot counts for a submission."""
    entities = sub.entities or []
    issues = sub.validation_issues or []

    total_slots = len(entities)
    satisfied_slots = sum(1 for e in entities if e.status == "SATISFIED")
    missing_slots = total_slots - satisfied_slots
    progress_percent = int((satisfied_slots / total_slots) * 100) if total_slots > 0 else 0
    blockers_count = sum(1 for issue in issues if getattr(issue, "severity", "") == "BLOCKER")

    pathway_code = sub.application_definition.code if sub.application_definition else "UNKNOWN"
    pathway_title = sub.application_definition.title if sub.application_definition else "Statutory Application"

    device_family_name = None
    if isinstance(sub.regulatory_context, dict):
        device_family_name = sub.regulatory_context.get("device_family_name")

    return SubmissionSummaryResponse(
        id=sub.id,
        tracking_code=sub.tracking_code,
        pathway_code=pathway_code,
        pathway_title=pathway_title,
        filing_modality=sub.filing_modality,
        device_category=sub.device_category,
        risk_class=sub.risk_class,
        device_family_name=device_family_name,
        status=sub.status,
        regulatory_context=sub.regulatory_context or {},
        total_slots=total_slots,
        satisfied_slots=satisfied_slots,
        missing_slots=missing_slots,
        progress_percent=progress_percent,
        blockers_count=blockers_count,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
    )


@router.get(
    "",
    response_model=List[SubmissionSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List active submission workspaces",
)
async def list_submissions(
    db: AsyncSession = Depends(get_db),
) -> List[SubmissionSummaryResponse]:
    """Retrieves all submissions in the portfolio with high-level readiness metrics."""
    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.application_definition),
            selectinload(Submission.entities),
            selectinload(Submission.validation_issues),
        )
        .order_by(Submission.updated_at.desc())
    )
    result = await db.execute(stmt)
    submissions = result.scalars().all()

    return [_build_summary_response(sub) for sub in submissions]


@router.post(
    "",
    response_model=SubmissionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize new statutory submission workspace",
)
async def create_submission(
    payload: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
) -> SubmissionDetailResponse:
    """Initializes a new CDSCO submission, resolves the statutory pathway blueprint,

    and generates empty fulfillment slots for checklist tracking.
    """
    # 1. Lookup or synchronize ApplicationDefinition
    def_record = await definition_service.get_definition_from_db(db, payload.pathway_code)
    if not def_record:
        # Attempt synchronization if blueprints not yet seeded
        await definition_service.sync_blueprints_to_db(db)
        def_record = await definition_service.get_definition_from_db(db, payload.pathway_code)
        if not def_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Regulatory pathway blueprint '{payload.pathway_code}' not recognized.",
            )

    # 2. Generate unique tracking code
    year = datetime.now(timezone.utc).year
    rand_suffix = f"{random.randint(100, 999)}"
    tracking_code = f"SUB-{year}-{payload.pathway_code.replace('-', '')}-{rand_suffix}"

    # Merge device_family_name into regulatory_context
    context = dict(payload.regulatory_context)
    if payload.device_family_name:
        context["device_family_name"] = payload.device_family_name

    submission_id = uuid.uuid4()
    submission = Submission(
        id=submission_id,
        application_definition_id=def_record.id,
        tracking_code=tracking_code,
        filing_modality=payload.filing_modality,
        device_category=payload.device_category,
        risk_class=payload.risk_class,
        status="DRAFT",
        regulatory_context=context,
        applicant_profile_id=payload.applicant_profile_id,
        manufacturer_profile_id=payload.manufacturer_profile_id,
        site_profile_id=payload.site_profile_id,
    )
    db.add(submission)
    await db.flush()

    # 3. Instantiate SubmissionEntity slots from blueprint
    blueprint_data = def_record.schema_payload or {}
    slots_data = blueprint_data.get("slots", [])

    created_entities: List[SubmissionEntity] = []
    for slot in slots_data:
        entity = SubmissionEntity(
            id=uuid.uuid4(),
            submission_id=submission_id,
            slot_id=slot.get("slot_id", ""),
            slot_title=slot.get("title", ""),
            fulfillment_mode=slot.get("default_fulfillment_mode", "UPLOAD"),
            status="EMPTY",
            form_values={},
        )
        db.add(entity)
        created_entities.append(entity)

    await db.commit()

    # Re-query with eager relationships
    stmt = (
        select(Submission)
        .where(Submission.id == submission_id)
        .options(
            selectinload(Submission.application_definition),
            selectinload(Submission.entities)
            .selectinload(SubmissionEntity.evidence_links)
            .selectinload(EvidenceLink.document),
            selectinload(Submission.validation_issues),
        )
    )
    reloaded = (await db.execute(stmt)).scalar_one()
    summary = _build_summary_response(reloaded)

    blueprint_slots = (reloaded.application_definition.schema_payload or {}).get("slots", [])
    slot_map = {s["slot_id"]: s for s in blueprint_slots}

    return SubmissionDetailResponse(
        **summary.model_dump(),
        entities=[
            _build_entity_response(e, slot_map)
            for e in reloaded.entities
        ],
    )


@router.get(
    "/{submission_id}",
    response_model=SubmissionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch submission workspace details and entities",
)
async def get_submission(
    submission_id: uuid.UUID = UrlPath(..., description="Target submission identifier"),
    db: AsyncSession = Depends(get_db),
) -> SubmissionDetailResponse:
    """Retrieves full submission details including all statutory checklist slots."""
    stmt = (
        select(Submission)
        .where(Submission.id == submission_id)
        .options(
            selectinload(Submission.application_definition),
            selectinload(Submission.entities)
            .selectinload(SubmissionEntity.evidence_links)
            .selectinload(EvidenceLink.document),
            selectinload(Submission.validation_issues),
        )
    )
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{submission_id}' not found.",
        )

    summary = _build_summary_response(sub)
    blueprint_slots = (sub.application_definition.schema_payload or {}).get("slots", [])
    slot_map = {s["slot_id"]: s for s in blueprint_slots}

    return SubmissionDetailResponse(
        **summary.model_dump(),
        entities=[
            _build_entity_response(e, slot_map)
            for e in sub.entities
        ],
    )


@router.delete(
    "/{submission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete submission workspace",
)
async def delete_submission(
    submission_id: uuid.UUID = UrlPath(..., description="Target submission identifier"),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a submission workspace and cascades to all slots and evidence links."""
    sub = await db.get(Submission, submission_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{submission_id}' not found.",
        )

    await db.delete(sub)
    await db.commit()
    return None
