from dependencies.annotations import AuthUserByAccessTokenDep, TagServiceDep
from fastapi import APIRouter, status
from schemas.tag import TagCreate, TagResponse

router = APIRouter()


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    response_model=TagResponse,
)
async def create_tag(
    user_id: AuthUserByAccessTokenDep,
    create_tag_data: TagCreate,
    tag_service: TagServiceDep,
) -> TagResponse:
    return await tag_service.create_tag(
        user_id=user_id,
        create_tag_data=create_tag_data,
    )
