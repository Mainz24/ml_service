from pydantic import BaseModel, field_validator, ConfigDict
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import re


if TYPE_CHECKING:
    from src.app.infrastructure.models.transaction import UserTransaction
    from src.app.infrastructure.models.prediction_task import PredictionTask

class User(SQLModel, table=True):
    __tablename__ = "users"

    """
    User model representing application users.
    
    Attributes:
        id (int): Primary key
        email (str): User's email address
        password (str): Hashed password
        created_at (datetime): Account creation timestamp
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(
        ...,  # Required field
        unique=True,
        index=True,
        min_length=5,
        max_length=255
    )
    hashed_password: str = Field(..., alias="password")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Баланс
    credits: float = Field(default=0.0, ge=0)
    # История транзакций как отдельная модель:
    transactions: List["UserTransaction"] = Relationship(back_populates="user")
    prediction_tasks: List["PredictionTask"] = Relationship(back_populates="user")
    # Поля админа
    is_active: bool = True
    is_superuser: bool = False
    
    def __str__(self) -> str:
        return f"Id: {self.id}. Email: {self.email}"

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """
        Validate email format.

        Args:
            v (str): Email to validate

        Returns:
            str: Validated email

        Raises:
            ValueError: If email format is invalid
        """
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError("Invalid email format")
        return v

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)


class UserPublic(BaseModel):
    """Модель пользователя для использования в ответах API."""
    id: int
    full_name: str
    email: str
    credits: float
    is_active: bool
    is_superuser: bool
    created_at: datetime

class UserSignin(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str