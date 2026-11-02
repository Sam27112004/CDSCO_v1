"""Pydantic schemas for evidence document ingestion, metadata, and slot linking."""

from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


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
