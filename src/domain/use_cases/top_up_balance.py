from src.domain.interfaces.transaction_repository import TransactionRepository
from src.domain.entities.transaction import Transaction
from uuid import UUID


class TopUpBalance:
    def __init__(self, user_repo: TransactionRepository):
        self._user_repo = user_repo

    def execute(self, user_id: UUID, transaction_amount: float):
        user = self._user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        user.increase_balance(transaction_amount)
        self._user_repo.save(user)