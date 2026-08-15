
from dependencies.annotations import (
    AuthUserByAccessTokenDep,
    MinioClientDep,
    ProjectServiceDep,
)
from fastapi import APIRouter, status
from schemas.project import (
    ProjectPartialUpdate,
    ProjectResponseList,
    ProjectWithRenderCreate,
    ProjectWithRenderFileFullResponse,
    ProjectWithRenderFileResponse,
    ProjectWithRenderResponse,
)

router = APIRouter(
    prefix="/project",
    tags=["Project"],
)


@router.get(
    "/{project_id}",
    response_model=ProjectWithRenderFileFullResponse,
    status_code=status.HTTP_200_OK,
)
async def get_project(
    project_id: int,
    user_id: AuthUserByAccessTokenDep,
    project_service: ProjectServiceDep,
    s3_client: MinioClientDep,
) -> ProjectWithRenderFileFullResponse:
    return await project_service.get_by_id(
        project_id=project_id,
        user_id=user_id,
        s3_client=s3_client,
    )


@router.get(
    "/",
    response_model=ProjectResponseList,
    status_code=status.HTTP_200_OK,
)
async def get_current_user_projects(
    project_service: ProjectServiceDep,
    user_id: AuthUserByAccessTokenDep,
    size: int = 10,
    page: int = 1,
) -> ProjectResponseList:
    return await project_service.get_user_projects(
        user_id=user_id,
        size=size,
        page=page,
    )


@router.get(
    "/public/user/{user_id}",
    response_model=ProjectResponseList,
    status_code=status.HTTP_200_OK,
)
async def get_user_public_projects(
    project_service: ProjectServiceDep,
    user_id: int,
    size: int = 10,
    page: int = 1,
) -> ProjectResponseList:
    return await project_service.get_user_public_projects(
        user_id=user_id,
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


@router.patch(
    "/update/{project_id}",
    response_model=ProjectWithRenderFileResponse,
    status_code=status.HTTP_200_OK,
)
async def partial_update_project(
    project_id: int,
    user_id: AuthUserByAccessTokenDep,
    partial_update_project_data: ProjectPartialUpdate,
    project_service: ProjectServiceDep,
) -> ProjectWithRenderFileResponse:
    return await project_service.partial_update_project(
        project_id,
        user_id,
        partial_update_project_data,
    )


@router.delete(
    "/delete/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: int,
    user_id: AuthUserByAccessTokenDep,
    project_service: ProjectServiceDep,
) -> None:
    return await project_service.delete_by_id(
        project_id=project_id,
        user_id=user_id,
    )
