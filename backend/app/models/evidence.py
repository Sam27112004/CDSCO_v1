import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Integer, BigInteger, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin


class EvidenceDocument(Base, UUIDMixin):
    """Uploaded physical PDF evidence binaries and generated statutory documents."""

    __tablename__ = "evidence_documents"
    __table_args__ = (
        Index("idx_evidence_docs_lookup", "submission_id", "original_filename"),
    )

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf", nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    extracted_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="evidence_documents")
    links: Mapped[List["EvidenceLink"]] = relationship(
        "EvidenceLink", back_populates="document", cascade="all, delete-orphan"
    )


class EvidenceLink(Base, UUIDMixin):
    """Many-to-Many association mapping an evidence document to portal slots and Fourth Schedule chapters."""

    __tablename__ = "evidence_links"
    __table_args__ = (
        UniqueConstraint(
            "submission_id",
            "evidence_document_id",
            "submission_entity_id",
            name="uq_evidence_link",
        ),
    )

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    submission_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submission_entities.id", ondelete="CASCADE"),
        nullable=False,
    )
    dossier_chapter: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="evidence_links")
    document: Mapped["EvidenceDocument"] = relationship("EvidenceDocument", back_populates="links")
    submission_entity: Mapped["SubmissionEntity"] = relationship("SubmissionEntity", back_populates="evidence_links")
