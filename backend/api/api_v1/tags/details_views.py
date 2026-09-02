from dependencies.annotations import AuthUserByAccessTokenDep, TagServiceDep
from fastapi import APIRouter, status
from schemas.tag import TagResponseList

router = APIRouter()


@router.get(
    "/project/{project_id}",
    status_code=status.HTTP_200_OK,
    response_model=TagResponseList,
)
async def get_project_tags(
    project_id: int,
    user_id: AuthUserByAccessTokenDep,
    tag_service: TagServiceDep,
) -> TagResponseList:
    return await tag_service.get_project_tags(
        project_id=project_id,
        user_id=user_id,
    )


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project_tag(
    tag_id: int,
    user_id: AuthUserByAccessTokenDep,
    tag_service: TagServiceDep,
) -> None:
    return await tag_service.delete_by_id(
        tag_id=tag_id,
        user_id=user_id,
    )
