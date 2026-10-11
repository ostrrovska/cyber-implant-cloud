# Lab2
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole


async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await session.get(User, user_id)


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def register_user(
    session: AsyncSession, email: str, password: str, role: UserRole = UserRole.USER
) -> User:
    if await get_by_email(session, email) is not None:
        raise ConflictError("A user with this email already exists.")
    user = User(email=email, hashed_password=hash_password(password), role=role)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    user = await get_by_email(session, email)
    if user is None or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Incorrect email or password.")
    return user
