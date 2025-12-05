from fastapi import HTTPException, status
from sqlalchemy import Sequence
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from aio_pika import connect_robust, Message, DeliveryMode

from app.infrastructure.models.prediction_task import PredictionTask, TaskStatus
from app.infrastructure.services.crud.transaction import withdraw_credits
from config.app_config import Settings, TASK_QUEUE


settings = Settings()
BROKER_URL = settings.RABBITMQ_URL

# Устанавливаем цену за предсказание
PREDICTION_COST = 5.0


async def submit_prediction_task(
        user_id: int,
        input_data: str,
        session: AsyncSession
) -> PredictionTask:
    # 1. Списание средств за выполнение задачи
    try:
        await withdraw_credits(user_id, PREDICTION_COST, session)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 2. Регистрация задачи в базе данных
    task = PredictionTask(
        user_id=user_id,
        input_data=input_data,
        cost=PREDICTION_COST,
        status=TaskStatus.PENDING
    )

    session.add(task)
    await session.commit()
    await session.refresh(task)

    # 3. Отправили задачи в очередь
    connection = await connect_robust(BROKER_URL)
    async with connection:
        channel = await connection.channel()
        # Объявляем очередь task_queue
        await channel.default_exchange.publish(
            Message(
                body=f'{{"task_id": "{task.id}", "data": "{input_data}"}}'.encode(),
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key=TASK_QUEUE
        )
    return task


async def get_prediction_task_history(user_id: int, session: AsyncSession) -> Sequence[PredictionTask]:
    """
    Получает все задачи предсказания ML-модели для конкретного пользователя.
    """
    statement = (
        select(PredictionTask)
        .where(PredictionTask.user_id == user_id)
        .order_by(PredictionTask.created_at.desc()) # Сначала новые задачи
    )
    result = await session.execute(statement)
    tasks = result.scalars().all()
    return tasks


async def get_prediction_result_history(user_id: int, session: AsyncSession) -> Sequence[PredictionTask]:
    """
        Получает все результаты предсказаний ML-модели для конкретного пользователя.
        """
    statement = (select(PredictionTask)
                 .where(PredictionTask.user_id == user_id))
    results = await session.execute(statement)
    prediction_results = results.scalars().all()
    return prediction_results