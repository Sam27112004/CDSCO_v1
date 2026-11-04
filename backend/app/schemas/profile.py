"""Pydantic schemas for organizational and site profiles."""

from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
    """Payload to register an organizational profile."""

    profile_type: str = Field(
        ...,
        description="Profile type: INDIAN_AGENT, FOREIGN_MANUFACTURER, MANUFACTURING_SITE, DOMESTIC_MANUFACTURER",
        example="INDIAN_AGENT",
    )
    name: str = Field(
        ...,
        description="Legal entity or site name",
        example="MedTech India Solutions Pvt Ltd",
    )
    data_payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Administrative metadata (licence numbers, address, contact details)",
    )


class ProfileResponse(BaseModel):
    """Organizational profile response model."""

    id: uuid.UUID
    profile_type: str
    name: str
    data_payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True
