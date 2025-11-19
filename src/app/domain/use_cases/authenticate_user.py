from src.app.domain.interfaces.user_repository import UserRepository


class AuthenticateUser:
    def __init__(self, user_repo: UserRepository, password_hasher):
        self._user_repo = user_repo
        self._password_hasher = password_hasher

    def execute(self, email: str, password: str) -> bool:
        user = self._user_repo.get_by_email(email)
        if not user:
            return False

        return self._password_hasher.check_password(password, user.verify_password)