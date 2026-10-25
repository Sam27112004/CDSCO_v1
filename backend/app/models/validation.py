import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin


class ValidationIssue(Base, UUIDMixin):
    """Continuous diagnostic issues and pre-submission audit findings."""

    __tablename__ = "validation_issues"
    __table_args__ = (
        Index("idx_val_issues_severity", "submission_id", "severity"),
    )

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # BLOCKER, ERROR, WARNING, INFO
    rule_code: Mapped[str] = mapped_column(String(100), nullable=False)
    target_slot_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    fix_guidance: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="validation_issues")
