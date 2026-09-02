from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from schemas.user import UserResponse

from core.config.application import settings
from core.constants import (
    ACCESS_TOKEN_FIELD,
    FIELD_SUB,
    REFRESH_TOKEN_FIELD,
    TOKEN_TYPE,
)
from core.exceptions.token import InvalidTokenPayloadError


def encode_jwt(
    payload: dict[str, Any],
    algorithm: str = settings.jwt.algorithm,
    key: str = settings.jwt.private_key_path.read_text(),
    expires_in_minutes: int = settings.jwt.access_token_expires_in_minutes,
) -> str:
    now_time = datetime.now(UTC)
    expire_time = now_time + timedelta(minutes=expires_in_minutes)
    payload.update(
        iat=now_time,
        exp=expire_time,
    )
    return jwt.encode(
        payload=payload,
        algorithm=algorithm,
        key=key,
    )


def decode_jwt(
    token: str,
    algorithm: str = settings.jwt.algorithm,
    key: str = settings.jwt.public_key_path.read_text(),
) -> dict[str, Any]:
    return jwt.decode(
        jwt=token,
        algorithms=[algorithm],
        key=key,
    )


def validate_token_payload(
    payload: dict[str, str],
    target_token_type: str,
) -> None:
    payload_token_type = payload.get(TOKEN_TYPE)
    if payload_token_type != target_token_type or FIELD_SUB not in payload:
        raise InvalidTokenPayloadError(payload)


def create_access_token_payload(user: UserResponse) -> dict[str, str]:
    user_id = str(user.id)
    payload = {
        TOKEN_TYPE: ACCESS_TOKEN_FIELD,
        FIELD_SUB: user_id,
    }
    return payload


def create_refresh_token_payload(user: UserResponse) -> dict[str, str]:
    user_id = str(user.id)
    payload = {
        TOKEN_TYPE: REFRESH_TOKEN_FIELD,
        FIELD_SUB: user_id,
    }
    return payload
