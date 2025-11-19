from uuid import UUID
from src.app.domain.interfaces.user_repository import UserRepository
from src.app.domain.interfaces.balance_repository import BalanceRepository
from src.app.domain.interfaces.transaction_repository import TransactionRepository
from src.app.domain.entities.transaction import Transaction, TransactionType

class TopUpBalance:
    def __init__(self,user_repo: UserRepository,balance_repo: BalanceRepository,transaction_repo: TransactionRepository):
        self._user_repo = user_repo
        self._balance_repo = balance_repo
        self._transaction_repo = transaction_repo

    def execute(self, user_id: UUID, transaction_amount: float, id_transaction: UUID):
        user = self._user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        balance = self._balance_repo.get_by_user_id(user_id)
        if not balance:
            raise ValueError("Баланс пользователя не найден")

        balance.top_up(transaction_amount)

        self._balance_repo.save(balance)

        transaction = Transaction(user_id=user_id,transaction_amount=transaction_amount,transaction_type=TransactionType.INCOME, id_transaction=id_transaction)
        self._transaction_repo.save(transaction)