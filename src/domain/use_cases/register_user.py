from src.domain.interfaces.user_repository import UserRepository
from src.domain.entities.user import User
from uuid import UUID


class RegisterUser(User):
    def __init__(self, user_repo: UserRepository, password_hasher, email: str, user_id: UUID, password: str,
                 balance: float):
        super().__init__(email, user_id, password, balance)
        self._user_repo = user_repo
        self._password_hasher = password_hasher

    def execute(self, email: str, password: str, user_id: UUID, balance: float) -> User:
        if self._user_repo.get_by_email(email):
            raise ValueError("Пользователь с таким email уже существует")

        hashed_password = self._password_hasher.hash_password(password)
        new_user = User(email=email, password=hashed_password, user_id=user_id, balance=balance)
        self._user_repo.save(new_user)
        return new_user