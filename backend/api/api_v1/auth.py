from dependencies.annotations import (
    AuthServiceDep,
    AuthUserByRefreshTokenDep,
    LoginRequestDep,
)
from fastapi import APIRouter, status
from schemas.auth import RegisterRequest
from schemas.token import TokenInfo

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=TokenInfo,
)
async def register(
    auth_service: AuthServiceDep,
    register_user_data: RegisterRequest,
) -> TokenInfo:
    return await auth_service.register(register_user_data)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenInfo,
)
async def login(
    auth_service: AuthServiceDep,
    auth_user_data: LoginRequestDep,
) -> TokenInfo:
    return await auth_service.authenticate_user(auth_user_data)


@router.get(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model_exclude_unset=True,
    response_model=TokenInfo,
)
async def refresh_access_token(
    auth_service: AuthServiceDep,
    user_id: AuthUserByRefreshTokenDep,
) -> TokenInfo:
    return await auth_service.refresh_access_token(user_id)
