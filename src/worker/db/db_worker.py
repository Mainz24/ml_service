import asyncio
import json
import datetime
from aio_pika import connect_robust, IncomingMessage
from sqlalchemy import update

from database.database import get_async_task_session, get_database_engine
from app.infrastructure.models.prediction_task import PredictionTask, TaskStatus
from app.infrastructure.models.user import User
from app.infrastructure.models.transaction import UserTransaction
from config.app_config import Settings, DB_QUEUE


settings = Settings()
BROKER_URL = settings.RABBITMQ_URL

async def on_message_db_write(message: IncomingMessage) :
    async with message.process():
        data = json.loads(message.body.decode())
        task_id = data['task_id']
        result_data = data['result']

        print(f"[DB Worker] Получено задание на запись результата {task_id}")

        # --- АСИНХРОННАЯ ЗАПИСЬ В БД ---
        async with get_async_task_session() as session:
            stmt = update(PredictionTask).where(PredictionTask.id == task_id).values(
                    status=TaskStatus.COMPLETED,
                    result_data=result_data,
                    completed_at=datetime.datetime.utcnow()
                )
            await session.execute(stmt)
            await session.commit()
        print(f"[DB Worker] Успешно записано в БД {task_id}")

async def main_db_worker():
    await get_database_engine()
    connection = await connect_robust(BROKER_URL)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(DB_QUEUE, durable=True)
        await queue.consume(on_message_db_write)
        print("DB Worker запущен и ожидает сообщений в db_queue...")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main_db_worker())