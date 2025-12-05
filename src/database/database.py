from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlmodel import SQLModel

from config.app_config import get_settings


engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None

async def get_database_engine():
    global engine, AsyncSessionLocal

    settings = await get_settings()

    engine = create_async_engine(
        url=settings.DATABASE_URL_asyncpg,
        echo=settings.DEBUG,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@asynccontextmanager
async def get_async_task_session() -> AsyncGenerator[AsyncSession, None]:
    global AsyncSessionLocal
    """
    Предоставляет асинхронную сессию SQLAlchemy как контекстный менеджер.
    Используется напрямую в коде воркеров.
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized")

    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def disconnect_db():
    """Disposes the global engine."""
    global engine
    if engine:
        await engine.dispose()
        engine = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    global engine, AsyncSessionLocal
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized")
    async with AsyncSessionLocal() as session:
        yield session


async def init_db(drop_all: bool = False) -> None:
    global engine

    if engine is None:
        raise RuntimeError("Database engine not available for init_db")

    try:
        async with engine.begin() as conn:
            if drop_all:
                await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)
    except Exception as e:
        raise