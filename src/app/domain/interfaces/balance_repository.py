from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from src.app.domain.entities.balance import Balance

class BalanceRepository(ABC):
    @abstractmethod
    def get_by_user_id(self, user_id: UUID) -> Optional[Balance]:
        pass

    @abstractmethod
    def save(self, balance: Balance) -> None:
        pass