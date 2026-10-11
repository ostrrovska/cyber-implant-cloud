# Lab2
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.db.session import get_session
from app.models.user import User
from app.services import firmware_service, implant_service, ota_service

router = APIRouter(tags=["dashboards"])


@router.get("/me/dashboard")
async def user_dashboard(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    implants = await implant_service.list_implants(session, user)
    jobs = await ota_service.list_jobs(session, user)
    return {
        "role": user.role.value,
        "email": user.email,
        "implants_owned": len(implants),
        "ota_jobs": len(jobs),
    }


@router.get("/admin/dashboard")
async def admin_dashboard(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    implants = await implant_service.list_implants(session, admin)
    firmware = await firmware_service.list_firmware(session)
    jobs = await ota_service.list_jobs(session, admin)
    return {
        "role": admin.role.value,
        "email": admin.email,
        "total_implants": len(implants),
        "total_firmware": len(firmware),
        "total_ota_jobs": len(jobs),
    }
