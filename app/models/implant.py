from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ImplantStatus(enum.StrEnum):
    ACTIVE = "active"
    OFFLINE = "offline"
    QUARANTINED = "quarantined"


class Implant(Base):
    """A single connected cyber-implant device registered in the cloud."""

    __tablename__ = "implants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Lab2: owner_id ties an implant to the user who registered it (RBAC / IDOR guard).
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True
    )
    serial_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    model: Mapped[str] = mapped_column(String(128))
    current_firmware_version: Mapped[str] = mapped_column(String(32))
    status: Mapped[ImplantStatus] = mapped_column(
        Enum(ImplantStatus, name="implant_status"), default=ImplantStatus.ACTIVE
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
