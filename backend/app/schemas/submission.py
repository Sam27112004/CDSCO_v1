"""Pydantic schemas for statutory CDSCO submission workspaces."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class SubmissionCreate(BaseModel):
    """Payload to initialize a new statutory CDSCO submission."""

    pathway_code: str = Field(
        ...,
        description="Statutory pathway code (e.g. 'MD-14', 'MD-7', 'MD-8')",
        example="MD-14",
    )
    filing_modality: str = Field(
        default="FRESH",
        description="Filing modality: FRESH, RENEWAL, POST_APPROVAL_CHANGE, ENDORSEMENT",
    )
    device_category: str = Field(
        default="MEDICAL_DEVICE",
        description="Device category: MEDICAL_DEVICE or IVD",
    )
    risk_class: str = Field(
        ...,
        description="Statutory risk classification: CLASS_A, CLASS_B, CLASS_C, CLASS_D",
        example="CLASS_C",
    )
    device_family_name: Optional[str] = Field(
        default=None,
        description="Commercial or generic medical device family title",
        example="Orthopedic Pedicle Screw System",
    )
    regulatory_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dynamic applicability context (e.g. is_sterile, contains_software)",
    )
    applicant_profile_id: Optional[uuid.UUID] = None
    manufacturer_profile_id: Optional[uuid.UUID] = None
    site_profile_id: Optional[uuid.UUID] = None


class SubmissionSummaryResponse(BaseModel):
    """High-level summary of a submission workspace for portfolio dashboards."""

    id: uuid.UUID
    tracking_code: str
    pathway_code: str
    pathway_title: str
    filing_modality: str
    device_category: str
    risk_class: str
    device_family_name: Optional[str] = None
    status: str
    regulatory_context: Dict[str, Any] = Field(default_factory=dict)
    total_slots: int = 0
    satisfied_slots: int = 0
    missing_slots: int = 0
    progress_percent: int = 0
    blockers_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubmissionEntityResponse(BaseModel):
    """Statutory slot within an active submission workspace."""

    id: uuid.UUID
    submission_id: uuid.UUID
    slot_id: str
    slot_title: str
    fulfillment_mode: str
    status: str
    form_values: Optional[Dict[str, Any]] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class SubmissionDetailResponse(SubmissionSummaryResponse):
    """Detailed submission workspace view including all slot entities."""

    entities: List[SubmissionEntityResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
