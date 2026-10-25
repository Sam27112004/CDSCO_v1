import uuid
from typing import Optional, List
from sqlalchemy import String, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class ApplicationDefinition(Base, UUIDMixin):
    """Statutory Form Definition blueprint (e.g. Form MD-14, MD-7)."""

    __tablename__ = "application_definitions"
    __table_args__ = (
        UniqueConstraint("code", "version", name="uq_app_def_code_version"),
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    schema_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Submissions instantiated from this definition
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission", back_populates="application_definition"
    )
