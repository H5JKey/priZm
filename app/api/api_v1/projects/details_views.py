from dependencies.annotations import (
    AuthUserByAccessTokenDep,
    MinioClientDep,
    ProjectServiceDep,
)
from fastapi import APIRouter
from schemas.project import (
    ProjectPartialUpdate,
    ProjectWithRenderFileFullResponse,
    ProjectWithRenderFileResponse,
)
from starlette import status

router = APIRouter()


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


@router.patch(
    "/{project_id}",
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
    "/{project_id}",
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
