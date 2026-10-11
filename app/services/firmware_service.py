# Lab2
from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.models.firmware import FirmwareVersion
from app.schemas.firmware import FirmwareCreate


async def publish_firmware(session: AsyncSession, data: FirmwareCreate) -> FirmwareVersion:
    existing = await session.execute(
        select(FirmwareVersion).where(FirmwareVersion.version == data.version)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("This firmware version already exists.")
    firmware = FirmwareVersion(
        version=data.version,
        checksum_sha256=data.checksum_sha256,
        artifact_url=data.artifact_url,
        release_notes=data.release_notes,
    )
    session.add(firmware)
    await session.commit()
    await session.refresh(firmware)
    return firmware


async def list_firmware(session: AsyncSession) -> Sequence[FirmwareVersion]:
    result = await session.execute(select(FirmwareVersion).order_by(FirmwareVersion.created_at))
    return result.scalars().all()
