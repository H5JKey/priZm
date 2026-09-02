from schemas.token import TokenInfo
from schemas.user import UserResponse

from core.config.application import settings
from core.constants import BEARER_TOKEN_TYPE
from core.security.jwt_tokens.utils import (
    create_access_token_payload,
    create_refresh_token_payload,
    encode_jwt,
)


def create_access_token(user: UserResponse) -> str:
    payload = create_access_token_payload(user)
    return encode_jwt(
        payload=payload,
        algorithm=settings.jwt.algorithm,
        key=settings.jwt.private_key_path.read_text(),
        expires_in_minutes=settings.jwt.access_token_expires_in_minutes,
    )


def create_refresh_token(user: UserResponse) -> str:
    payload = create_refresh_token_payload(user)
    return encode_jwt(
        payload=payload,
        algorithm=settings.jwt.algorithm,
        key=settings.jwt.private_key_path.read_text(),
        expires_in_minutes=settings.jwt.refresh_token_expires_in_minutes,
    )


def create_token(user: UserResponse) -> TokenInfo:
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    token = TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=BEARER_TOKEN_TYPE,
    )
    return token
