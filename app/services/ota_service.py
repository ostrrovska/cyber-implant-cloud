# Lab2
from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, NotFoundError, UnprocessableError
from app.models.firmware import FirmwareVersion
from app.models.implant import Implant
from app.models.ota_job import OtaJobStatus, OtaUpdateJob
from app.models.user import User, UserRole
from app.schemas.ota import RolloutResult

_TERMINAL = {OtaJobStatus.SUCCEEDED, OtaJobStatus.FAILED}


def _is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


async def launch_rollout(
    session: AsyncSession,
    firmware_version_id: uuid.UUID,
    implant_ids: list[uuid.UUID] | None,
) -> RolloutResult:
    """Admin fan-out: create one OTA job per targeted implant (whole fleet if None)."""
    firmware = await session.get(FirmwareVersion, firmware_version_id)
    if firmware is None:
        raise NotFoundError("Firmware version not found.")

    stmt = select(Implant)
    if implant_ids is not None:
        stmt = stmt.where(Implant.id.in_(implant_ids))
    targets = (await session.execute(stmt)).scalars().all()

    if implant_ids is not None and len(targets) != len(set(implant_ids)):
        raise UnprocessableError("One or more target implants do not exist.")
    if not targets:
        raise UnprocessableError("No implants to roll out to.")

    jobs = [
        OtaUpdateJob(implant_id=implant.id, firmware_version_id=firmware_version_id)
        for implant in targets
    ]
    session.add_all(jobs)
    await session.commit()
    for job in jobs:
        await session.refresh(job)

    return RolloutResult(
        firmware_version_id=firmware_version_id,
        jobs_created=len(jobs),
        job_ids=[job.id for job in jobs],
    )


async def list_jobs(session: AsyncSession, user: User) -> Sequence[OtaUpdateJob]:
    stmt = select(OtaUpdateJob).order_by(OtaUpdateJob.scheduled_at)
    if not _is_admin(user):
        stmt = stmt.join(Implant, Implant.id == OtaUpdateJob.implant_id).where(
            Implant.owner_id == user.id
        )
    result = await session.execute(stmt)
    return result.scalars().all()


async def report_status(
    session: AsyncSession, user: User, job_id: uuid.UUID, status: OtaJobStatus
) -> OtaUpdateJob:
    job = await session.get(OtaUpdateJob, job_id)
    if job is None:
        raise NotFoundError("OTA job not found.")

    implant = await session.get(Implant, job.implant_id)
    if not _is_admin(user) and (implant is None or implant.owner_id != user.id):
        raise ForbiddenError("You do not have access to this OTA job.")

    job.status = status
    job.attempts += 1
    job.completed_at = datetime.now(UTC) if status in _TERMINAL else None
    await session.commit()
    await session.refresh(job)
    return job
