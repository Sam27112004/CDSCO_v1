from typing import Optional, List
from sqlalchemy import String, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class Profile(Base, UUIDMixin, TimestampMixin):
    """Organization and Entity Profiles (Applicant, Foreign Manufacturer, Manufacturing Sites)."""

    __tablename__ = "profiles"
    __table_args__ = (
        Index("idx_profiles_type", "profile_type"),
    )

    profile_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
