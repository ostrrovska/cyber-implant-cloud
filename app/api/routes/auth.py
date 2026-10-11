# Lab2
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import create_access_token
from app.db.session import get_session
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import LoginRequest, UserCreate, UserRead
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, session: AsyncSession = Depends(get_session)) -> User:
    return await user_service.register_user(session, data.email, data.password)


@router.post("/login", response_model=Token)
async def login(data: LoginRequest, session: AsyncSession = Depends(get_session)) -> Token:
    user = await user_service.authenticate(session, data.email, data.password)
    return Token(access_token=create_access_token(user.id, user.role.value))


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)) -> User:
    return user
