from uuid import UUID, uuid4
from enum import Enum
from src.domain.entities.user import User

class TransactionType(Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

class Transaction(User):
    def __init__(self, id_transaction: UUID, transaction_amount: float, transaction_type: TransactionType, user_id: UUID, balance: float, email: str, password: str):
        super().__init__(email, user_id, password, balance)
        self._id_transaction: UUID = id_transaction if id_transaction else uuid4()
        self._transaction_amount: float = transaction_amount
        self._type: TransactionType = transaction_type

    @property
    def id_transaction(self) -> UUID:
        return self._id_transaction

    @property
    def transaction_amount(self) -> float:
        return self._transaction_amount


    def increase_balance(self, _transaction_amount: float):
        if _transaction_amount > 0:
            self.balance += _transaction_amount

    def decrease_balance(self, _transaction_amount: float) -> bool:
        if 0 <_transaction_amount <= self.balance:
            self.balance -= _transaction_amount
            return True
        return False
