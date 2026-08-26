from typing import cast

from core.constants import ProjectVisibility
from core.exceptions.auth import PermissionDeniedError
from core.exceptions.project import ProjectIdNotFoundError
from core.exceptions.tag import TagIdNotFoundError
from core.interfaces.clients import AbstractUnitOfWorkClient
from infrastructure.database.models import User
from infrastructure.database.repositories import ProjectRepository, TagRepository
from schemas.tag import TagCreate, TagResponse, TagResponseList


class TagService:
    def __init__(self, unit_of_work: AbstractUnitOfWorkClient) -> None:
        self.unit_of_work = unit_of_work
        self.project_repository = self.unit_of_work.get_repository(ProjectRepository)
        self.tag_repository = self.unit_of_work.get_repository(TagRepository)

    async def get_project_tags(self, project_id: int, user_id: int) -> TagResponseList:
        project = await self.project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectIdNotFoundError(project_id)

        get_owner_coroutine = self.project_repository.get_project_owner(
            project_id,
        )
        owner = cast(User, await get_owner_coroutine)
        if project.visibility == ProjectVisibility.private and user_id != owner.id:
            raise PermissionDeniedError

        tag_list = [
            TagResponse.model_validate(tag)
            for tag in await self.tag_repository.get_project_tags(project_id)
        ]
        return TagResponseList(tag_list=tag_list)

    async def create_tag(
        self,
        create_tag_data: TagCreate,
        user_id: int,
    ) -> TagResponse:
        project_id = create_tag_data.project_id
        project = await self.project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectIdNotFoundError(project_id)

        get_owner_coroutine = self.project_repository.get_project_owner(
            project_id,
        )
        owner = cast(User, await get_owner_coroutine)
        if owner.id != user_id:
            raise PermissionDeniedError

        tag = await self.tag_repository.create_tag(create_tag_data)
        return TagResponse.model_validate(tag)

    async def delete_by_id(self, tag_id: int, user_id: int) -> None:
        tag = await self.tag_repository.get_by_id(tag_id)
        if tag is None:
            raise TagIdNotFoundError(tag_id)

        get_owner_coroutine = self.project_repository.get_project_owner(
            tag.project.id,
        )
        owner = cast(User, await get_owner_coroutine)
        if owner.id != user_id:
            raise PermissionDeniedError

        await self.tag_repository.delete_by_id(tag_id)
