from pydantic import BaseModel
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
    password: str = Field(..., min_length=4) 
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Баланс
    credits: float = Field(default=0.0, ge=0)
    # История транзакций как отдельная модель:
    transactions: List["UserTransaction"] = Relationship(back_populates="user")
    prediction_tasks: List["PredictionTask"] = Relationship(back_populates="user")
    # Поля админа
    is_active: bool
    is_superuser: bool
    
    def __str__(self) -> str:
        return f"Id: {self.id}. Email: {self.email}"

    def validate_email(self) -> bool:
        """
        Validate email format.
        
        Returns:
            bool: True if email is valid
        
        Raises:
            ValueError: If email format is invalid
        """
        pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not pattern.match(self.email):
            raise ValueError("Invalid email format")
        return True

    class Config:
        """Model configuration"""
        validate_assignment = True
        arbitrary_types_allowed = True


class UserPublic(BaseModel):
    """Модель пользователя для использования в ответах API."""
    id: int
    full_name: str
    email: str
    credits: float
    is_active: bool
    created_at: datetime

class UserSignin(BaseModel):
    email: str
    password: str


# from app.infrastructure.models.transaction import UserTransaction
# from app.infrastructure.models.prediction_task import PredictionTask