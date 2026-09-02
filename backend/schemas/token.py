from core.constants import BEARER_TOKEN_TYPE
from pydantic import BaseModel


class TokenInfo(BaseModel):
    """
    Модель для отображения информации о токене.
    """

    access_token: str
    refresh_token: str | None = None
    token_type: str = BEARER_TOKEN_TYPE
