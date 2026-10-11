from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FirmwareVersion(Base):
    """A published firmware build available for OTA rollout."""

    __tablename__ = "firmware_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    checksum_sha256: Mapped[str] = mapped_column(String(64))
    artifact_url: Mapped[str] = mapped_column(String(512))
    release_notes: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
