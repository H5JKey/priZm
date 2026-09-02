from typing import Annotated

from core.config.application import settings
from core.constants import ACCESS_TOKEN_FIELD, FIELD_SUB, REFRESH_TOKEN_FIELD
from core.security.jwt_tokens.utils import decode_jwt, validate_token_payload
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from schemas.auth import LoginRequest


def get_access_token_payload(
    token: Annotated[
        str,
        Depends(settings.oauth2_scheme),
    ],
) -> dict[str, int | str]:
    return decode_jwt(
        token=token,
        algorithm=settings.jwt.algorithm,
        key=settings.jwt.public_key_path.read_text(),
    )


def get_valid_access_token_payload(
    payload: Annotated[
        dict[str, str],
        Depends(get_access_token_payload),
    ],
) -> dict[str, str]:
    validate_token_payload(
        payload,
        target_token_type=ACCESS_TOKEN_FIELD,
    )
    return payload


def get_refresh_token_payload(
    token: Annotated[
        str,
        Depends(settings.oauth2_scheme),
    ],
) -> dict[str, str]:
    return decode_jwt(
        token=token,
        algorithm=settings.jwt.algorithm,
        key=settings.jwt.public_key_path.read_text(),
    )


def get_valid_refresh_token_payload(
    payload: Annotated[
        dict[str, str],
        Depends(get_refresh_token_payload),
    ],
) -> dict[str, str]:
    validate_token_payload(
        payload,
        target_token_type=REFRESH_TOKEN_FIELD,
    )
    return payload


async def get_auth_user_by_access_token(
    valid_payload: Annotated[
        dict[str, str],
        Depends(get_valid_access_token_payload),
    ],
) -> int:
    user_id = int(valid_payload[FIELD_SUB])
    return user_id


async def get_auth_user_by_refresh_token(
    valid_payload: Annotated[
        dict[str, str],
        Depends(get_valid_refresh_token_payload),
    ],
) -> int:
    user_id = int(valid_payload[FIELD_SUB])
    return user_id


def get_login_request(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
) -> LoginRequest:
    login_request = LoginRequest(
        username=form_data.username,
        password=form_data.password,
    )
    return login_request
