import asyncio
import json
import logging
from aio_pika import connect_robust, IncomingMessage, Message, DeliveryMode

from config.app_config import Settings, DB_QUEUE, TASK_QUEUE
from worker.ml.model_loader import cached_generate_response

logger = logging.getLogger(__name__)

settings = Settings()
BROKER_URL = settings.RABBITMQ_URL

async def publish_result(queue_name: str, payload: dict):
    """Вспомогательная функция для публикации сообщений."""
    connection = await connect_robust(BROKER_URL)
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            Message(
                body=json.dumps(payload, ensure_ascii=False).encode(),
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key=queue_name
        )


async def on_message_ml_task(message: IncomingMessage):
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            task_id = data['task_id']
            input_data = data.get("data", "")

            logger.info(f"Обработка задачи ML: {task_id}")

            # Генерация через GGUF + llama.cpp
            prompt = input_data if isinstance(input_data, str) else str(input_data)
            prediction_result = cached_generate_response(prompt)

            result_payload = {
                'task_id': task_id,
                'result': prediction_result
            }

            # --- ОТПРАВКА В ОЧЕРЕДИ ---
            # 1. Отправляем в очередь для записи в БД
            await publish_result(DB_QUEUE, result_payload)
            logger.info(f"Задача {task_id} завершена")

            # 2. Отправляем в очередь для ответа/уведомления клиента
            # await publish_result(RESULT_QUEUE, result_payload)

        except Exception as e:
            logger.exception(f"Ошибка в задаче: {e}")
            raise


async def main_ml_worker():
    from worker.ml.model_loader import load_model
    load_model()

    connection = await connect_robust(BROKER_URL)
    async with connection:
        channel = await connection.channel()
        # Объявляем очереди на случай, если их еще нет
        await channel.declare_queue(DB_QUEUE, durable=True)
        # await channel.declare_queue(RESULT_QUEUE, durable=True)

        task_queue = await channel.declare_queue(TASK_QUEUE, durable=True)
        await task_queue.consume(on_message_ml_task)
        logger.info("ML Worker запущен и ожидает задач в task_queue...")
        await asyncio.Future()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main_ml_worker())