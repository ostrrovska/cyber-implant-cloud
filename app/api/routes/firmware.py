# Lab2
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.db.session import get_session
from app.models.user import User
from app.schemas.firmware import FirmwareCreate, FirmwareRead
from app.services import firmware_service

router = APIRouter(prefix="/firmware", tags=["firmware"])


# Admin-only: publishing firmware is an operator action (vertical RBAC).
@router.post("", response_model=FirmwareRead, status_code=status.HTTP_201_CREATED)
async def publish_firmware(
    data: FirmwareCreate,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    return await firmware_service.publish_firmware(session, data)


@router.get("", response_model=list[FirmwareRead])
async def list_firmware(
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await firmware_service.list_firmware(session)
