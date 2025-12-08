from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette.requests import Request

from app.infrastructure.auth.jwt_handler import verify_token
from app.infrastructure.auth.hash_password import verify_password
from app.infrastructure.models.user import User
from database.database import get_session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def authenticate_user(email: str, password: str, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user_optional(
    request: Request,
    session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token or not token.startswith("Bearer "):
        return None
    payload = verify_token(token[7:])
    if not payload:
        return None
    email = payload.get("sub")
    if not email:
        return None
    user = await session.execute(select(User).where(User.email == email))
    return user.scalar_one_or_none()


async def get_current_user_from_cookie(request: Request, session: AsyncSession = Depends(get_session)) -> User:
    # 1. Получаем токен из куки
    token = request.cookies.get("access_token")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # 2. Верифицируем токен
    from app.infrastructure.auth.jwt_handler import verify_token

    payload = verify_token(token[7:]) # убираем "Bearer "
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    email = payload.get("sub")

    from app.infrastructure.models.user import User
    from sqlalchemy import select

    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user_optional),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user