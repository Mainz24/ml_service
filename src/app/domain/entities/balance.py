from decimal import Decimal
from uuid import UUID

class Balance:
    def __init__(self, user_id: UUID, transaction_amount: Decimal = Decimal("0.00")):
        self._user_id: UUID = user_id
        self._amount = transaction_amount


    @property
    def transaction_amount(self) -> Decimal:
        return self._amount

    @transaction_amount.setter
    def transaction_amount(self, value: Decimal):
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._amount = value

    def top_up(self, transaction_amount: float) -> None:
        if transaction_amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной.")
        self._amount += Decimal(str(transaction_amount))

    def withdraw(self, transaction_amount: float) -> bool:
        transaction_amount_dec = Decimal(str(transaction_amount))
        if transaction_amount_dec <= 0:
            raise ValueError("Сумма вывода должна быть положительной.")
        if self._amount >= transaction_amount_dec:
            self._amount -= transaction_amount_dec
            return True
        return False
