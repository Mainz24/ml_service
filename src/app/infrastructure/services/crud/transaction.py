import logging
from typing import Sequence
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.infrastructure.models.transaction import UserTransaction
from app.infrastructure.services.crud.user import update_user_balance
from app.infrastructure.models.user import User


logger = logging.getLogger(__name__)


async def deposit_credits(user_id: int, amount: float, session: AsyncSession) -> User:
    """Пополнение баланса."""
    return await update_user_balance(user_id, amount, session, operation='deposit')


async def withdraw_credits(user_id: int, amount: float, session: AsyncSession) -> User:
    """Списание кредитов."""
    return await update_user_balance(user_id, amount, session, operation='withdrawal')


async def get_transaction_history(user_id: int, session: AsyncSession) -> Sequence[UserTransaction]:
    """Получение истории транзакций пользователя"""
    stmt = select(UserTransaction).where(UserTransaction.user_id == user_id)
    result = await session.execute(stmt)
    transactions = result.scalars().all()
    return transactions

