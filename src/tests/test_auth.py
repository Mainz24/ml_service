import pytest

from app.infrastructure.routes.user import signup, signin
from app.infrastructure.models.user import UserCreate, UserSignin
from app.infrastructure.services.crud import user as UserService


@pytest.mark.asyncio
async def test_signup_route_direct_call(async_session, override_session_dependency):
    signup_data = UserCreate(email="direct_call@example.com", password="secure123", full_name="Direct Test")

    response_dict = await signup(data=signup_data, session=async_session)

    assert response_dict["message"] == "User successfully registered"
    user_exists = await UserService.get_user_by_email(signup_data.email, async_session)
    assert user_exists is not None


@pytest.mark.asyncio
async def test_signin_route_direct_call(async_session, override_session_dependency):
    signup_data = UserCreate(email="user_to_sign_in@example.com", password="secure123", full_name="Sign In Test")
    await signup(data=signup_data, session=async_session)

    login_data = UserSignin(email="user_to_sign_in@example.com", password="secure123")

    response_data = await signin(data=login_data, session=async_session)

    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"