import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from app.api import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker as sync_sessionmaker
from typing import Generator
from sqlalchemy.orm import Session


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sync_sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def get_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def anyio_backend():
    """Фикстура pytest-asyncio, указывающая использовать asyncio."""
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine():
    """Создает асинхронный движок БД для тестов."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    # Очищаем движок после завершения сессии
    await engine.dispose()


@pytest.fixture(scope="function")
async def async_session(test_engine):
    """
    Предоставляет асинхронную сессию БД для каждого теста.
    Транзакция откатывается после завершения теста для изоляции.
    """
    async with test_engine.connect() as connection:
        await connection.begin()
        async_session_maker = async_sessionmaker(connection, class_=AsyncSession, expire_on_commit=False, autoflush=False)
        session = async_session_maker()
        yield session
        await session.close()
        await connection.rollback()


@pytest.fixture
def override_session_dependency(async_session):
    """
    Фикстура для временной подмены зависимости get_session в приложении FastAPI.
    """
    async def override_get_session_async():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session_async

    yield # Запуск теста

    app.dependency_overrides.clear()