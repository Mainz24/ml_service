from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from starlette import status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional, Sequence

from app.infrastructure.models.user import User
from app.infrastructure.models.transaction import UserTransaction, TransactionType


class InsufficientFundsError(Exception):
    """Пользовательская ошибка: недостаточно средств на балансе."""
    pass

async def get_all_users(session: AsyncSession) -> Sequence[User]:
    """
    Args:
        session: Database session

    Returns:
        List[User]: List of all users
    """
    try:
        statement = select(User)
        result = await session.execute(statement)
        users = result.scalars().all()
        return users
    except Exception as e:
        raise


async def get_user_by_id(user_id: int, session: AsyncSession) -> Optional[User]:
    """
    Get user by ID.

    Args:
        user_id: User ID to find
        session: Database session

    Returns:
        Optional[User]: Found user or None
    """
    try:
        statement = select(User).where(User.id == user_id)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        return user
    except Exception as e:
        raise


async def get_user_by_email(email: str, session: AsyncSession) -> Optional[User]:
    """
    Get user by email.

    Args:
        email: Email to search for
        session: Database session

    Returns:
        Optional[User]: Found user or None
    """
    try:
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        # result = await session.exec(statement)
        # user = result.first()
        return user
    except Exception as e:
        raise


async def create_user(user: User, session: AsyncSession) -> User:
    """
    Create new user.

    Args:
        user: User to create
        session: Database session

    Returns:
        User: Created user with ID
    """
    try:
        # Убедитесь, что для стандартного пользователя is_superuser=False
        if user.is_superuser is None:
            user.is_superuser = False

        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    except Exception as e:
        await session.rollback()
        raise


async def get_current_user(email: str, session: AsyncSession) -> User:
    """
    Извлекает и валидирует токен, возвращает объект текущего пользователя из БД.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def create_admin_user(admin_user: User, session: AsyncSession) -> User:
    """
    Create a new administrator user with superuser privileges.

    Args:
        email: Administrator's email address (unique identifier)
        password: The already hashed password for security
        session: Database session

    Returns:
        User: Created administrator user with ID
        :param admin_user:
        :param session:
        :param email:
        :param password:
    """
    # # Проверяем пользователя с таким email
    # existing_user = await session.execute(
    #     select(User).where(User.email == email)
    # )
    # if existing_user.scalar_one_or_none():
    #     raise ValueError(f"User with email {email} already exists.")
    #
    # # Создаем нового пользователя с флагом администратора
    # admin_user = User(
    #     email=email,
    #     password=password,
    #     # full_name=full_name,
    #     is_active=True,  # Администратор по умолчанию активен
    #     is_superuser=True,  # Ключевой флаг администратора
    # )

    try:
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        return admin_user
    except Exception as e:
        await session.rollback()
        raise


async def delete_user(user_id: int, session: AsyncSession) -> bool | None:
    """
    Delete user by ID.

    Args:
        user_id: User ID to delete
        session: Database session

    Returns:
        bool: True if deleted, False if not found
    """
    try:
        user = await get_user_by_id(user_id, session)
        if user:
            await session.delete(user)
            await session.commit()
            return True
        return False
    except Exception as e:
        await session.rollback()
        raise RuntimeError(f"Error deleting user: {e}")


async def create_transaction_record(
        user_id: int,
        amount: float,
        transaction_type: TransactionType,
        session: AsyncSession
) -> UserTransaction:
    """
    Создает объект транзакции и добавляет его в текущую сессию (без коммита).
    """
    transaction = UserTransaction(
        user_id=user_id,
        transaction_amount=amount,
        type=transaction_type,
    )
    session.add(transaction)
    return transaction


async def update_user_balance(user_id: int, amount: float, session: AsyncSession, operation: str) -> User:
    """
      Обновляет баланс пользователя и создает запись о транзакции.
      """

    # 1. Находим пользователя в базе данных
    user_stmt = select(User).where(User.id == user_id)
    result = await session.execute(user_stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError(f"User with id {user_id} not found")

    # 2. Определяем тип транзакции из Enum
    transaction_type = TransactionType.INCOME if operation == 'deposit' else TransactionType.EXPENSE

    # 3. Рассчитываем новый баланс
    if transaction_type == TransactionType.INCOME:
        user.credits += amount
    elif transaction_type == TransactionType.EXPENSE:
        if user.credits < amount:
            raise ValueError("Insufficient funds")
        user.credits -= amount

    try:
        # 4. Создаем запись о транзакции
        transaction = UserTransaction(
            transaction_amount=amount,
            type=transaction_type,
            user_id=user_id
        )

        # 5. Добавляем и фиксируем изменения в рамках одной атомарной операции (транзакции БД)
        session.add(user)
        session.add(transaction)
        await session.commit()
        await session.refresh(user)

        return user

    except SQLAlchemyError as e:
        await session.rollback()
        raise RuntimeError(f"Database operation failed: {e}")

