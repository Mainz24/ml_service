from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.database import get_session
from app.infrastructure.services.crud.ml_service import submit_prediction_task, get_prediction_task_history, get_prediction_result_history
from app.infrastructure.models.prediction_task import PredictionTask, PredictionTaskPublic, PredictionResultResponse
from app.infrastructure.models.user import User
from app.infrastructure.auth.authenticate import get_current_user_from_cookie


ml_router = APIRouter()

# Модель для входных данных запроса
class PredictionInput(BaseModel):
    user_id: int
    data: str


@ml_router.post("/predict", response_model=PredictionTask)
async def request_prediction(
        prediction_input: PredictionInput, current_user: User = Depends(get_current_user_from_cookie),
        session: AsyncSession = Depends(get_session)
):
    """
    Отправляет запрос на выполнение предсказания ML-модели,
    списывает средства с баланса пользователя и регистрирует задачу.
    """
    task = await submit_prediction_task(
        user_id=current_user.id,
        input_data=prediction_input.data,
        session=session
    )

    return task


@ml_router.post( "/predictions",
    response_model=List[PredictionTaskPublic])
async def api_get_user_tasks(
        current_user: User = Depends(get_current_user_from_cookie),
        session: AsyncSession = Depends(get_session)
):
    """
    Возвращает историю всех запросов (задач) ML-модели для указанного пользователя.
    """
    tasks = await get_prediction_task_history(current_user.id, session)

    if not tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No transactions found for user with ID {current_user.id}"
        )

    return tasks


@ml_router.get(
    "/predictions/results",
    response_model=List[PredictionResultResponse],
    summary="Get a history of all prediction results"
)
async def get_prediction_history(
        current_user: User = Depends(get_current_user_from_cookie),
        session: AsyncSession = Depends(get_session)
):
    """
    Извлекаем список всех завершенных (или всех) задач предсказаний из базы данных.
    """
    prediction_results = await get_prediction_result_history(current_user.id, session)

    if not prediction_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No predictions were found for the user with the specified ID {current_user.id}"
        )

    return prediction_results