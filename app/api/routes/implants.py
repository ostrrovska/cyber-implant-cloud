# Lab2
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.implant import ImplantCreate, ImplantRead, ImplantUpdate
from app.services import implant_service

router = APIRouter(prefix="/implants", tags=["implants"])


@router.post("", response_model=ImplantRead, status_code=status.HTTP_201_CREATED)
async def register_implant(
    data: ImplantCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await implant_service.create_implant(session, user, data)


@router.get("", response_model=list[ImplantRead])
async def list_implants(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await implant_service.list_implants(session, user)


@router.get("/{implant_id}", response_model=ImplantRead)
async def get_implant(
    implant_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await implant_service.get_owned_implant(session, user, implant_id)


@router.patch("/{implant_id}", response_model=ImplantRead)
async def update_implant(
    implant_id: uuid.UUID,
    data: ImplantUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await implant_service.update_implant(session, user, implant_id, data)


@router.delete("/{implant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_implant(
    implant_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    await implant_service.delete_implant(session, user, implant_id)
