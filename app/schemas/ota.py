# Lab2
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.ota_job import OtaJobStatus


class RolloutRequest(BaseModel):
    firmware_version_id: uuid.UUID
    # None targets the whole fleet; a list targets specific implants.
    implant_ids: list[uuid.UUID] | None = None


class RolloutResult(BaseModel):
    firmware_version_id: uuid.UUID
    jobs_created: int
    job_ids: list[uuid.UUID]


class OtaJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    implant_id: uuid.UUID
    firmware_version_id: uuid.UUID
    status: OtaJobStatus
    attempts: int
    scheduled_at: datetime
    completed_at: datetime | None


class OtaStatusReport(BaseModel):
    status: OtaJobStatus
