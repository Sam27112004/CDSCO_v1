from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(default="healthy", description="Application operational status")
    version: str = Field(description="Service semantic version")
    project_name: str = Field(description="Canonical project name")
    environment: str = Field(description="Current deployment environment")
    database_connected: bool = Field(description="Database connectivity status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response generation UTC timestamp",
    )
