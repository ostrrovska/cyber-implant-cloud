# Lab2
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.implant import ImplantStatus


class ImplantCreate(BaseModel):
    serial_number: str = Field(min_length=1, max_length=64)
    model: str = Field(min_length=1, max_length=128)
    current_firmware_version: str = Field(min_length=1, max_length=32)


class ImplantUpdate(BaseModel):
    model: str | None = Field(default=None, min_length=1, max_length=128)
    current_firmware_version: str | None = Field(default=None, min_length=1, max_length=32)
    status: ImplantStatus | None = None


class ImplantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID | None
    serial_number: str
    model: str
    current_firmware_version: str
    status: ImplantStatus
    last_seen_at: datetime | None
    created_at: datetime
