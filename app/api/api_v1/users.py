from dependencies.annotations import AuthUserByAccessTokenDep, UserServiceDep
from fastapi import APIRouter, status
from schemas.user import UserResponse, UserUpdate

router = APIRouter(
    prefix="/user/about-me",
    tags=["User"],
)


@router.get(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_current_user_profile(
    user_id: AuthUserByAccessTokenDep,
    user_service: UserServiceDep,
) -> UserResponse:
    return await user_service.get_by_id(user_id)


@router.put(
    "/",
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
    "/",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def delete_current_user_profile(
    user_id: AuthUserByAccessTokenDep,
    user_service: UserServiceDep,
) -> None:
    await user_service.delete_by_id(user_id)
