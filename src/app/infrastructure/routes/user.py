from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Sequence, Dict
import logging

from database.database import get_session
from app.infrastructure.models.user import User, UserSignin, UserCreate
from app.infrastructure.services.crud import user as UserService
from app.infrastructure.auth.hash_password import verify_password
from app.infrastructure.auth.hash_password import get_password_hash
from app.infrastructure.auth.jwt_handler import create_access_token


logger = logging.getLogger(__name__)

user_route = APIRouter()

@user_route.post(
    '/signup',
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Register a new user with email and password")
async def signup(data: UserCreate, session=Depends(get_session)) -> Dict[str, str]:
    """
    Create new user account.

    Args:
        data: User registration data
        session: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If user already exists
    """
    try:
        user_exists = await UserService.get_user_by_email(data.email, session)
        if user_exists:
            logger.warning(f"Signup attempt with existing email: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )

        hashed_pw = get_password_hash(data.password)
        user = User(
            # id=data.id,
            email=data.email,
            hashed_password=hashed_pw,
            full_name=data.full_name,
            credits=0.0,        # ← значение по умолчанию
            is_active=True,     # ← значение по умолчанию
            is_superuser=False)  # ← значение по умолчанию
        await UserService.create_user(user, session)
        logger.info(f"New user registered: {data.email}")
        return {"message": "User successfully registered"}

    except Exception as e:
        logger.error(f"Error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )


@user_route.post('/signin')
async def signin(data: UserSignin, session=Depends(get_session)) -> Dict[str, str]:
    """
    Authenticate existing user.

    Args:
        form_data: User credentials
        session: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If authentication fails
        :param session:
        :param data:
    """
    user = await UserService.get_user_by_email(data.email, session)

    if not user or not user.hashed_password:  # <-- ДОБАВЛЕНА ПРОВЕРКА НА ПУСТОЙ ХЕШ
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )

    if user is None:
        raise HTTPException(status_code=404, detail="User does not exist")

    # ✅ Проверяем пароль через хэш
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=403, detail="Wrong credentials passed")

        # Устанавливаем куку
    access_token = create_access_token(data={"sub": user.email})

    return {
        "message": "User signed in successfully",
        "access_token": access_token,
        "token_type": "bearer"
    }


@user_route.get(
    "/users",
    response_model=List[User],
    summary="Get all users",
    response_description="List of all users"
)
async def get_all_users(session=Depends(get_session)) -> Sequence[User]:
    """
    Get list of all users.

    Args:
        session: Database session

    Returns:
        List[UserResponse]: List of users
    """
    try:
        users = await UserService.get_all_users(session)
        logger.info(f"Retrieved {len(users)} users")
        return users
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )