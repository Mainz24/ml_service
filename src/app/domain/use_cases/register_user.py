from src.app.domain.interfaces.user_repository import UserRepository
from src.app.domain.entities.user import User
from uuid import UUID


class RegisterUser:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    def execute(self, email: str, password: str, user_id: UUID) -> User:
        if self._user_repo.get_by_email(email):
            raise ValueError("Пользователь с таким email уже существует")

        new_user = User(email=email, password=password, user_id=user_id)
        self._user_repo.save(new_user)
        return new_user