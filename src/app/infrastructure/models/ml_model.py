from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import Optional

class MLModel(SQLModel, table=True):
    __tablename__ = "ml_models"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    file_path: str # Путь к файлу модели (например, .pkl или директория TF)
    version: str
    active: bool = Field(default=False) # Флаг активности для использования в сервисе
    created_at: datetime = Field(default_factory=datetime.utcnow)