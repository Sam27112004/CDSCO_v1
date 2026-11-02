"""Pydantic schemas for evidence document ingestion, metadata, and slot linking."""

from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator


from app.services.pdf_inspector import PdfInspectionResult, PdfPageGeometry


class EvidenceDocumentResponse(BaseModel):
    """Response payload for uploaded and cataloged evidence documents."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Unique identifier of the evidence document")
    submission_id: uuid.UUID = Field(description="Parent submission ID")
    document_title: str = Field(description="Human-readable title of the document")
    original_filename: str = Field(description="Original uploaded filename")
    storage_path: str = Field(description="Relative object storage path")
    mime_type: str = Field(description="MIME type of the document")
    file_size_bytes: int = Field(description="Size of binary in bytes")
    page_count: int = Field(description="Total number of pages")
    extracted_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted technical and regulatory metadata (SHA-256, dates, version)",
    )
    uploaded_at: datetime = Field(description="UTC timestamp of upload")


class EvidenceLinkCreate(BaseModel):
    """Request payload to associate an evidence document with a slot or chapter."""

    document_id: uuid.UUID = Field(description="UUID of the cataloged evidence document")
    slot_id: Optional[str] = Field(
        default=None,
        description="Statutory checklist slot identifier (e.g. '10.3', '1.0')",
    )
    submission_entity_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Direct primary key UUID of the target submission entity",
    )
    chapter: Optional[str] = Field(
        default=None,
        description="Statutory Fourth Schedule dossier chapter code (e.g. 'DMF_6_2', 'PMF_3_0')",
    )
    dossier_chapter: Optional[str] = Field(
        default=None,
        description="Alias for chapter code",
    )

    @model_validator(mode="after")
    def validate_target_provided(self) -> "EvidenceLinkCreate":
        if not self.slot_id and not self.submission_entity_id:
            raise ValueError("Either 'slot_id' or 'submission_entity_id' must be provided.")
        return self


class EvidenceLinkResponse(BaseModel):
    """Response payload for an established or queried evidence link."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Unique link identifier")
    submission_id: uuid.UUID = Field(description="Parent submission ID")
    evidence_document_id: uuid.UUID = Field(description="Linked evidence document ID")
    submission_entity_id: uuid.UUID = Field(description="Target submission entity ID")
    slot_id: str = Field(description="Checklist slot identifier")
    dossier_chapter: Optional[str] = Field(default=None, description="Associated dossier chapter code")
    created_at: datetime = Field(description="Timestamp of link creation")
    document_title: Optional[str] = Field(default=None, description="Title of linked document")
    original_filename: Optional[str] = Field(default=None, description="Original filename of linked document")
    entity_status: str = Field(default="SATISFIED", description="Updated status of the slot entity")

