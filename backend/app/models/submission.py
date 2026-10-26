import uuid
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class Submission(Base, UUIDMixin, TimestampMixin):
    """Master record for a CDSCO statutory filing workspace."""

    __tablename__ = "submissions"
    __table_args__ = (
        Index("idx_submissions_status", "status"),
        Index("idx_submissions_regulatory_context", "regulatory_context", postgresql_using="gin"),
    )

    application_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("application_definitions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    tracking_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    filing_modality: Mapped[str] = mapped_column(String(50), default="FRESH", nullable=False)
    device_category: Mapped[str] = mapped_column(String(50), default="MEDICAL_DEVICE", nullable=False)
    risk_class: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False)
    regulatory_context: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    applicant_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    manufacturer_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    site_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    application_definition: Mapped["ApplicationDefinition"] = relationship(
        "ApplicationDefinition", back_populates="submissions"
    )
    applicant_profile: Mapped[Optional["Profile"]] = relationship(
        "Profile", foreign_keys=[applicant_profile_id]
    )
    manufacturer_profile: Mapped[Optional["Profile"]] = relationship(
        "Profile", foreign_keys=[manufacturer_profile_id]
    )
    site_profile: Mapped[Optional["Profile"]] = relationship(
        "Profile", foreign_keys=[site_profile_id]
    )

    entities: Mapped[List["SubmissionEntity"]] = relationship(
        "SubmissionEntity", back_populates="submission", cascade="all, delete-orphan"
    )
    evidence_documents: Mapped[List["EvidenceDocument"]] = relationship(
        "EvidenceDocument", back_populates="submission", cascade="all, delete-orphan"
    )
    evidence_links: Mapped[List["EvidenceLink"]] = relationship(
        "EvidenceLink", back_populates="submission", cascade="all, delete-orphan"
    )
    validation_issues: Mapped[List["ValidationIssue"]] = relationship(
        "ValidationIssue", back_populates="submission", cascade="all, delete-orphan"
    )
    background_jobs: Mapped[List["BackgroundJob"]] = relationship(
        "BackgroundJob", back_populates="submission", cascade="all, delete-orphan"
    )
