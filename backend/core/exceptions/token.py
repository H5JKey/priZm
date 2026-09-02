from core.exceptions.base import ConflictError


class InvalidTokenPayloadError(ConflictError):
    """
    Ошибка, связанная с невалидным payload токена.
    """

    def __init__(self, payload: dict[str, str]) -> None:
        self.payload = payload
        detail = f"Invalid token payload: {payload}."
        super().__init__(detail)
