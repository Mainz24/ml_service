from uuid import UUID, uuid4
import bcrypt


class User:
    def __init__(self, email: str, user_id: UUID, password: str):
        self._user_id: UUID = user_id or uuid4()
        self._email: str = email
        self._is_active: bool = True
        self._password_hash: str = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, plain_password: str) -> bool:
        if self._password_hash is None:
            return False
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            self._password_hash.encode('utf-8')
        )

    @property
    def email(self) -> str:
        return self._email

    @property
    def user_id(self) -> UUID:
        return self._user_id

    def deactivate(self):
        """Метод, инкапсулирующий логику смены статуса."""
        self._is_active = False

    @property
    def is_active(self) -> bool:
        return self._is_active