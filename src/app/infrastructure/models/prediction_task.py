from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.infrastructure.models.user import User


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PredictionTask(SQLModel, table=True):
    __tablename__ = "prediction_tasks"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True
    )
    user_id: int = Field(foreign_key="users.id", nullable=False)
    input_data: str
    result_data: Optional[str] = None
    cost: float # Стоимость выполнения задачи
    status: TaskStatus = Field(default=TaskStatus.PENDING, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    user: Optional["User"] = Relationship(back_populates="prediction_tasks")


class PredictionTaskPublic(BaseModel):
    """Модель ответа истории задач"""
    id: UUID
    user_id: int
    input_data: str
    result_data: Optional[str]
    cost: float
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class PredictionResultResponse(SQLModel):
    """Модель ответа истории предсказаний"""
    id: UUID
    status: str
    result_data: str | None
    created_at: datetime
    completed_at: datetime | None


# from app.infrastructure.models.user import User