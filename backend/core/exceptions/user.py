from pydantic import EmailStr

from core.exceptions.base import ConflictError, NotFoundError


class UserNotFoundError(NotFoundError):
    """
    Ошибка, связанная с ненахождением пользователя.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)


class UserIdNotFoundError(NotFoundError):
    """
    Ошибка, связанная с ненахождением пользователя по id.
    """

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        detail = f"User with id = {user_id} not found."
        super().__init__(detail)


class UserUsernameNotFoundError(NotFoundError):
    """
    Ошибка, связанная с ненахождением пользователя по username.
    """

    def __init__(self, username: str) -> None:
        self.username = username
        detail = f"User with username = {username} not found."
        super().__init__(detail)


class UserAlreadyExistsError(ConflictError):
    """
    Ошибка, связанная с существованием переданных данных.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)


class UserEmailAlreadyExistsError(UserAlreadyExistsError):
    """
    Ошибка, связанная с существованием email пользователя.
    """

    def __init__(self, email: EmailStr) -> None:
        self.email = email
        detail = f"User with email = {email} already exists."
        super().__init__(detail)


class UserUsernameAlreadyExistsError(UserAlreadyExistsError):
    """
    Ошибка, связанная с существованием username пользователя.
    """

    def __init__(self, username: str) -> None:
        self.username = username
        detail = f"User with username = {username} already exists."
        super().__init__(detail)
