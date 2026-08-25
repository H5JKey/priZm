

from dependencies.annotations import (
    AuthUserByAccessTokenDep,
    PaginationPageDep,
    PaginationSizeDep,
    ProjectServiceDep,
)
from dependencies.auth import get_auth_user_by_access_token
from fastapi import APIRouter, Depends, status
from schemas.project import (
    ProjectResponseList,
    ProjectWithRenderCreate,
    ProjectWithRenderResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=ProjectResponseList,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(get_auth_user_by_access_token),
    ],
)
async def get_public_projects(
    project_service: ProjectServiceDep,
    size: PaginationSizeDep = 10,
    page: PaginationPageDep = 1,
) -> ProjectResponseList:
    return await project_service.get_public_projects(
        size=size,
        page=page,
    )


@router.post(
    "/create",
    response_model=ProjectWithRenderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    user_id: AuthUserByAccessTokenDep,
    create_project_data: ProjectWithRenderCreate,
    project_service: ProjectServiceDep,
) -> ProjectWithRenderResponse:
    return await project_service.create_project(
        user_id=user_id,
        create_project=create_project_data,
    )


@router.get(
    "/about-me",
    response_model=ProjectResponseList,
    status_code=status.HTTP_200_OK,
)
async def get_current_user_projects(
    project_service: ProjectServiceDep,
    user_id: AuthUserByAccessTokenDep,
    size: PaginationSizeDep = 10,
    page: PaginationPageDep = 1,
) -> ProjectResponseList:
    return await project_service.get_user_projects(
        user_id=user_id,
        size=size,
        page=page,
    )


@router.get(
    "/user/{user_id}",
    response_model=ProjectResponseList,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(get_auth_user_by_access_token),
    ],
)
async def get_user_public_projects(
    project_service: ProjectServiceDep,
    user_id: int,
    size: PaginationSizeDep = 10,
    page: PaginationPageDep = 1,
) -> ProjectResponseList:
    return await project_service.get_user_public_projects(
        user_id=user_id,
        size=size,
        page=page,
    )
