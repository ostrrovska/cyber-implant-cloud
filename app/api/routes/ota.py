# Lab2
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.db.session import get_session
from app.models.user import User
from app.schemas.ota import OtaJobRead, OtaStatusReport, RolloutRequest, RolloutResult
from app.services import ota_service

router = APIRouter(prefix="/ota", tags=["ota"])


# Admin-only: launching a rollout fans out jobs across the fleet (vertical RBAC).
@router.post("/rollouts", response_model=RolloutResult, status_code=status.HTTP_201_CREATED)
async def launch_rollout(
    data: RolloutRequest,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> RolloutResult:
    return await ota_service.launch_rollout(session, data.firmware_version_id, data.implant_ids)


@router.get("/jobs", response_model=list[OtaJobRead])
async def list_jobs(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await ota_service.list_jobs(session, user)


@router.post("/jobs/{job_id}/status", response_model=OtaJobRead)
async def report_status(
    job_id: uuid.UUID,
    data: OtaStatusReport,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await ota_service.report_status(session, user, job_id, data.status)
