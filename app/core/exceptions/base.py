class BaseApplicationError(Exception):
    """
    Базовое исключение приложения.
    """

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(BaseApplicationError):
    """
    Ошибка, связанная с ненахождением объекта.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)


class ConflictError(BaseApplicationError):
    """
    Ошибка, связанная с конфликтами данных.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)


class AuthenticationError(BaseApplicationError):
    """
    Ошибка, связанная с аутентификацией.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)


class ForbiddenError(BaseApplicationError):
    """
    Ошибка, связанная с авторизацией.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)


class KafkaSendError(BaseApplicationError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
