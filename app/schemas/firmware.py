# Lab2
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FirmwareCreate(BaseModel):
    version: str = Field(min_length=1, max_length=32)
    checksum_sha256: str = Field(min_length=64, max_length=64)
    artifact_url: str = Field(min_length=1, max_length=512)
    release_notes: str | None = Field(default=None, max_length=2048)


class FirmwareRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version: str
    checksum_sha256: str
    artifact_url: str
    release_notes: str | None
    created_at: datetime
