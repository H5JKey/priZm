from dependencies.annotations import AuthUserByAccessTokenDep, UserServiceDep
from fastapi import APIRouter, status
from schemas.user import UserFullResponse, UserResponse, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["User"],
)


@router.get(
    "/about-me",
    response_model=UserFullResponse,
    status_code=status.HTTP_200_OK,
)
async def get_current_user_profile(
    user_id: AuthUserByAccessTokenDep,
    user_service: UserServiceDep,
) -> UserFullResponse:
    return await user_service.get_profile_by_id(user_id)


@router.put(
    "/about-me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def update_current_user_profile(
    user_id: AuthUserByAccessTokenDep,
    user_service: UserServiceDep,
    update_user_data: UserUpdate,
) -> UserResponse:
    return await user_service.update_user(user_id, update_user_data)


@router.delete(
    "/about-me",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def delete_current_user_profile(
    user_id: AuthUserByAccessTokenDep,
    user_service: UserServiceDep,
) -> None:
    await user_service.delete_by_id(user_id)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_by_id(
    user_id: int,
    user_service: UserServiceDep,
) -> UserResponse:
    return await user_service.get_by_id(user_id)
