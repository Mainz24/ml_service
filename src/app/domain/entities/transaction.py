from uuid import UUID, uuid4
from enum import Enum

class TransactionType(Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

class Transaction:
    def __init__(self, id_transaction: UUID, transaction_amount: float, transaction_type: TransactionType, user_id: UUID):
        self._id_transaction: UUID = id_transaction if id_transaction else uuid4()
        self._transaction_amount: float = transaction_amount
        self._type: TransactionType = transaction_type
        self._user_id: UUID = user_id

    @property
    def id_transaction(self) -> UUID:
        return self._id_transaction

    @property
    def transaction_amount(self) -> float:
        return self._transaction_amount

    @property
    def type(self) -> TransactionType:
        return self._type
