import pytest

from app.infrastructure.routes.user import signup, signin
from app.infrastructure.models.user import UserCreate, UserSignin
from app.infrastructure.services.crud import user as UserService
from app.infrastructure.routes.transaction import api_deposit_credits, api_withdraw_credits
from app.infrastructure.auth.authenticate import get_current_user_from_cookie
from app.api import app
from app.infrastructure.models.transaction import TransactionInput


@pytest.mark.asyncio
async def test_deposit_route_direct_call(async_session, override_session_dependency):
    user_email = "user_for_deposit@example.com"
    signup_data = UserCreate(email=user_email, password="secure123", full_name="Deposit Test User")
    await signup(data=signup_data, session=async_session)
    user = await UserService.get_user_by_email(user_email, async_session)

    app.dependency_overrides[get_current_user_from_cookie] = lambda: user

    deposit_data = TransactionInput(transaction_amount=100.0)

    response_obj = await api_deposit_credits(transaction_input=deposit_data, current_user=user, session=async_session)

    assert response_obj.credits == 100.0

    del app.dependency_overrides[get_current_user_from_cookie]


@pytest.mark.asyncio
async def test_withdraw_route_direct_call(async_session, override_session_dependency):
    user_email = "user_for_withdraw@example.com"
    signup_data = UserCreate(email=user_email, password="secure123", full_name="Withdraw Test User")
    await signup(data=signup_data, session=async_session)
    user = await UserService.get_user_by_email(user_email, async_session)

    initial_deposit = 50.0
    deposit_data = TransactionInput(transaction_amount=initial_deposit)
    await api_deposit_credits(transaction_input=deposit_data, current_user=user, session=async_session)

    user = await UserService.get_user_by_email(user_email, async_session)

    assert user.credits == initial_deposit

    app.dependency_overrides[get_current_user_from_cookie] = lambda: user

    withdraw_one_amount = 10.0
    withdraw_data = TransactionInput(transaction_amount=withdraw_one_amount)

    response_valid_obj = await api_withdraw_credits(
        transaction_input=withdraw_data,
        current_user=user,
        session=async_session
    )

    expected_balance = initial_deposit - withdraw_one_amount
    assert response_valid_obj.credits == expected_balance

    del app.dependency_overrides[get_current_user_from_cookie]