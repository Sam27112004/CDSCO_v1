import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin


class SubmissionEntity(Base, UUIDMixin):
    """Discrete statutory portal slot state (36-48 tracked slots per submission)."""

    __tablename__ = "submission_entities"
    __table_args__ = (
        UniqueConstraint("submission_id", "slot_id", name="uq_sub_entity_slot"),
        Index("idx_sub_entities_lookup", "submission_id", "status"),
    )

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    slot_id: Mapped[str] = mapped_column(String(50), nullable=False)
    slot_title: Mapped[str] = mapped_column(String(255), nullable=False)
    fulfillment_mode: Mapped[str] = mapped_column(String(20), default="UPLOAD", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="MISSING", nullable=False)
    form_values: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="entities")
    evidence_links: Mapped[List["EvidenceLink"]] = relationship(
        "EvidenceLink", back_populates="submission_entity", cascade="all, delete-orphan"
    )
