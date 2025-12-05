import logging
from pydantic import BaseModel
from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import String
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    # Используется только для статического анализа типов, не вызывает циклических импортов
    from src.app.infrastructure.models.user import User

class TransactionType(str, Enum):
    INCOME = "deposit"
    EXPENSE = "withdrawal"

class UserTransaction(SQLModel, table=True):
    __tablename__ = "transactions"
    id_transaction: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    transaction_amount: float = Field(gt=0, nullable=False)
    type: TransactionType = Field(sa_column=Column(String, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    user: Optional["User"] = Relationship(back_populates="transactions")


# Для входящих данных
class TransactionInput(BaseModel):
    transaction_amount: float = Field(gt=0, description="Amount for transaction, must be positive")

# Для стандартизированного ответа
class MessageResponse(BaseModel):
    message: str

# Модель ответа количество Transaction
class TransactionResponseItem(BaseModel):
    id_transaction: UUID
    transaction_amount: float
    type: TransactionType
    created_at: datetime

    class Config:
        from_attributes = True


# from app.infrastructure.models.user import User
