from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.database import get_session
from app.infrastructure.models.transaction import TransactionResponseItem, TransactionInput
from app.infrastructure.models.user import UserPublic
from app.infrastructure.services.crud.transaction import get_transaction_history, deposit_credits, withdraw_credits


transactions_router = APIRouter()

@transactions_router.post("/deposit", response_model=UserPublic, status_code=status.HTTP_200_OK)
async def api_deposit_credits(
    user_id: int,
    transaction_input: TransactionInput,
    session: AsyncSession = Depends(get_session)
):
    """Пополняет баланс пользователя и возвращает его обновленные данные."""
    try:
        updated_user = await deposit_credits(
            user_id=user_id,
            amount=transaction_input.transaction_amount,
            session=session
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected database error occurred - {e}"
        )

@transactions_router.post("/withdraw", response_model=UserPublic, status_code=status.HTTP_200_OK)
async def api_withdraw_credits(
    user_id: int,
    transaction_input: TransactionInput,
    session: AsyncSession = Depends(get_session)
):
    """Списывает кредиты с баланса пользователя."""
    try:
        updated_user = await withdraw_credits(
            user_id=user_id,
            amount=transaction_input.transaction_amount,
            session=session
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@transactions_router.get(
    "/{user_id}/transactions",
    response_model=List[TransactionResponseItem],
    status_code=status.HTTP_200_OK
)
async def api_get_transaction_history(
        user_id: int,
        session: AsyncSession = Depends(get_session)
):
    """
    Возвращает полную историю транзакций для указанного пользователя.
    """
    history = await get_transaction_history(user_id, session)

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No transactions found for user with ID {user_id}"
        )
    return history