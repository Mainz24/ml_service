from uuid import UUID, uuid4

class User:
    def __init__(self, email: str, user_id: UUID, password: str, balance: float = 0.0):
        self._user_id: UUID = user_id if user_id else uuid4()
        self._password_hash: str = password
        self._balance: float = balance
        self._email: str = email
        self._is_active: bool = True

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def email(self) -> str:
        return self._email

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        if value < 0:
            raise ValueError("Balance cannot be negative")
        self._balance = value

    def deactivate(self):
        """Метод, инкапсулирующий логику смены статуса."""
        self._is_active = False

    @property
    def is_active(self) -> bool:
        return self._is_active