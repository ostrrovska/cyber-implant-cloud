from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OtaJobStatus(enum.StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class OtaUpdateJob(Base):
    """A single per-implant unit of work within a mass OTA rollout campaign."""

    __tablename__ = "ota_update_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    implant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("implants.id"), index=True)
    firmware_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("firmware_versions.id"), index=True
    )
    status: Mapped[OtaJobStatus] = mapped_column(
        Enum(OtaJobStatus, name="ota_job_status"), default=OtaJobStatus.PENDING
    )
    attempts: Mapped[int] = mapped_column(default=0)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
