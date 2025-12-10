from unittest.mock import patch, AsyncMock
import pytest

from app.infrastructure.routes.ml_routes import request_prediction, PredictionInput
from app.infrastructure.models.user import UserCreate
from app.infrastructure.services.crud import user as UserService
from app.api import app
from app.infrastructure.auth.authenticate import get_current_user_from_cookie
from app.infrastructure.routes.user import signup
from app.infrastructure.routes.transaction import api_deposit_credits
from app.infrastructure.models.transaction import TransactionInput
from app.infrastructure.models.prediction_task import PredictionTask

@pytest.mark.asyncio
async def test_predict_route_direct_call(async_session, override_session_dependency):
    user_email = "user_for_deposit@example.com"
    signup_data = UserCreate(email=user_email, password="secure123", full_name="Deposit Test User")
    await signup(data=signup_data, session=async_session)

    user = await UserService.get_user_by_email(user_email, async_session)

    deposit_data = TransactionInput(transaction_amount=10.0)
    await api_deposit_credits(transaction_input=deposit_data, current_user=user, session=async_session)

    user = await UserService.get_user_by_email(user_email, async_session)

    app.dependency_overrides[get_current_user_from_cookie] = lambda: user

    prediction_data = PredictionInput(
        user_id=user.id,
        data="{'feature_example': 123}"
    )

    with patch('app.infrastructure.routes.ml_routes.submit_prediction_task', new_callable=AsyncMock) as mock_submit:
        # мок
        mock_task = PredictionTask(id=1, user_id=user.id, status="PENDING", result_data="{}")
        mock_submit.return_value = mock_task

        response_task_obj = await request_prediction(
            prediction_input=prediction_data,
            current_user=user,
            session=async_session
        )

        mock_submit.assert_awaited_once()  # проверка что заглушка была вызвана
        assert response_task_obj.status == "PENDING"
        assert response_task_obj.user_id == user.id

    del app.dependency_overrides[get_current_user_from_cookie]