from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


TASK_QUEUE = 'task_queue'
RESULT_QUEUE = 'result_queue'
DB_QUEUE = 'db_queue'

class Settings(BaseSettings):

    # Database settings
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_USER: Optional[str] = None
    DB_PASS: Optional[str] = None
    DB_NAME: Optional[str] = None

    # Application settings
    APP_NAME: Optional[str] = None
    DEBUG: Optional[bool] = None
    API_VERSION: Optional[str] = None

    # RabbitMQ settings
    RABBITMQ_USER: Optional[str] = None
    RABBITMQ_PASS: Optional[str] = None
    MQ_PORT1: Optional[int] = None  # Например, для Management UI
    MQ_PORT2: Optional[int] = None  # Например, для AMQP
    MQ_HOST: Optional[str] = None

    WEB_PROXY1: Optional[str] = None
    WEB_PROXY2: Optional[str] = None


    @property
    def DATABASE_URL_asyncpg(self):
        if not all([self.DB_USER, self.DB_PASS, self.DB_HOST, self.DB_PORT, self.DB_NAME]):
            raise ValueError("Database asyncpg credentials missing for URL generation")
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    @property
    def RABBITMQ_URL(self):
        if not all([self.RABBITMQ_USER, self.RABBITMQ_PASS, self.MQ_HOST, self.MQ_PORT2]):
            raise ValueError("RabbitMQ credentials missing for URL generation")
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@{self.MQ_HOST}:{self.MQ_PORT2}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    async def validate(self, **kwargs) -> None:
        """Validate critical configuration settings
        :param **kwargs:
        """
        if not all([self.DB_HOST, self.DB_USER, self.DB_PASS, self.DB_NAME]):
            raise ValueError("Missing required database configuration")

        if not all([self.RABBITMQ_USER, self.RABBITMQ_PASS, self.MQ_PORT2]):
            raise ValueError("Missing required RabbitMQ configuration")


@lru_cache()
async def get_settings() -> Settings:
    settings = Settings()
    await settings.validate()
    return settings