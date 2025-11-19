from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.app.domain.entities.transaction import Transaction


class TransactionRepository(ABC):
    @abstractmethod
    def get_id_transaction(self, id_transaction: UUID) -> Optional[Transaction]:
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Optional[Transaction]:
        pass

    @abstractmethod
    def save(self, transaction: Transaction):
        pass