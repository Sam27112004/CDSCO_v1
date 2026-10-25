import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin


class BackgroundJob(Base, UUIDMixin):
    """Asynchronous compilation, downsampling, and export job tracker."""

    __tablename__ = "background_jobs"
    __table_args__ = (
        Index("idx_bg_jobs_lookup", "submission_id", "status"),
    )

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)  # DOSSIER_ASSEMBLY, PDF_COMPRESSION, BULK_EXPORT
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    artifact_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata_payload: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="background_jobs")
