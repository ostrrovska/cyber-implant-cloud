# Lab2
from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.models.implant import Implant
from app.models.user import User, UserRole
from app.schemas.implant import ImplantCreate, ImplantUpdate


def _is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


async def create_implant(session: AsyncSession, owner: User, data: ImplantCreate) -> Implant:
    existing = await session.execute(
        select(Implant).where(Implant.serial_number == data.serial_number)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("An implant with this serial number already exists.")
    implant = Implant(
        owner_id=owner.id,
        serial_number=data.serial_number,
        model=data.model,
        current_firmware_version=data.current_firmware_version,
    )
    session.add(implant)
    await session.commit()
    await session.refresh(implant)
    return implant


async def list_implants(session: AsyncSession, user: User) -> Sequence[Implant]:
    stmt = select(Implant).order_by(Implant.created_at)
    if not _is_admin(user):
        stmt = stmt.where(Implant.owner_id == user.id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_owned_implant(session: AsyncSession, user: User, implant_id: uuid.UUID) -> Implant:
    """Fetch an implant, enforcing ownership for non-admins (IDOR guard)."""
    implant = await session.get(Implant, implant_id)
    if implant is None:
        raise NotFoundError("Implant not found.")
    if not _is_admin(user) and implant.owner_id != user.id:
        raise ForbiddenError("You do not have access to this implant.")
    return implant


async def update_implant(
    session: AsyncSession, user: User, implant_id: uuid.UUID, data: ImplantUpdate
) -> Implant:
    implant = await get_owned_implant(session, user, implant_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(implant, field, value)
    await session.commit()
    await session.refresh(implant)
    return implant


async def delete_implant(session: AsyncSession, user: User, implant_id: uuid.UUID) -> None:
    implant = await get_owned_implant(session, user, implant_id)
    await session.delete(implant)
    await session.commit()
