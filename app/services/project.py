from types import TracebackType
from typing import Self, cast

from core.constants import KafkaTopic, ProjectVisibility
from core.exceptions.auth import PermissionDeniedError
from core.exceptions.file import FileIdNotFoundError
from core.exceptions.project import ProjectIdNotFoundError
from core.exceptions.user import UserIdNotFoundError
from core.interfaces.clients import AbstractUnitOfWorkClient
from core.logging import get_logger
from infrastructure.database.models import User
from infrastructure.database.repositories.file import FileRepository
from infrastructure.database.repositories.outbox import OutboxRepository
from infrastructure.database.repositories.project import ProjectRepository
from infrastructure.database.repositories.render import RenderRepository
from infrastructure.database.repositories.user import UserRepository
from schemas.event import AddRenderProjectEvent, EventCreate, GenerateRenderEvent
from schemas.file import FileLocationCreate
from schemas.project import (
    ProjectPartialUpdate,
    ProjectResponse,
    ProjectResponseList,
    ProjectWithRenderCreate,
    ProjectWithRenderFileResponse,
    ProjectWithRenderResponse,
)
from schemas.render import RenderResponse

logger = get_logger(__name__)


class ProjectService:
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWorkClient,
    ) -> None:
        self.unit_of_work = unit_of_work
        self.user_repository = self.unit_of_work.get_repository(UserRepository)
        self.project_repository = self.unit_of_work.get_repository(ProjectRepository)
        self.render_repository = self.unit_of_work.get_repository(RenderRepository)
        self.file_repository = self.unit_of_work.get_repository(FileRepository)
        self.outbox_repository = self.unit_of_work.get_repository(OutboxRepository)

    async def __aenter__(self) -> "Self":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """
        Метод для действий при выходе из контекстного менеджера.
        """

    async def get_by_id(
        self,
        project_id: int,
        user_id: int,
    ) -> ProjectWithRenderFileResponse:
        project = await self.project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectIdNotFoundError(project_id)

        get_owner_coroutine = self.project_repository.get_project_owner(
            project_id,
        )
        owner = cast(User, await get_owner_coroutine)
        if (
            project.visibility == ProjectVisibility.private.value
            and owner.id != user_id
        ):
            detail = "You are not allowed to watch this project."
            raise PermissionDeniedError(detail)

        logger.info(
            "Received project, project_id=%s, user_id=%s, render_id=%s, source_file_id=%s, name=%s, status=%s, visibility=%s",  # noqa: E501
            project.id,
            project.user_id,
            project.render_id,
            project.source_file_id,
            project.name,
            project.status,
            project.visibility,
        )
        return ProjectWithRenderFileResponse.model_validate(project)

    async def get_user_projects(
        self,
        user_id: int,
        size: int,
        page: int,
    ) -> ProjectResponseList:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise UserIdNotFoundError(user_id)

        get_projects = self.project_repository.get_user_projects(
            user_id,
        )
        projects = [
            ProjectResponse.model_validate(project) for project in await get_projects
        ]
        return ProjectResponseList(
            project_list=projects,
            size=size,
            page=page,
        )

    async def get_user_public_projects(
        self,
        user_id: int,
        size: int,
        page: int,
    ) -> ProjectResponseList:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise UserIdNotFoundError(user_id)

        get_projects = self.project_repository.get_user_public_projects(
            user_id,
        )
        projects = [
            ProjectResponse.model_validate(project) for project in await get_projects
        ]
        return ProjectResponseList(
            project_list=projects,
            size=size,
            page=page,
        )

    async def add_render_to_project(
        self,
        add_render_project_event: AddRenderProjectEvent,
    ) -> None:
        file = add_render_project_event.file
        project_id = add_render_project_event.project_id
        render_file = await self.file_repository.create_file(file)
        project = await self.project_repository.get_by_id(project_id)
        await self.render_repository.add_render_file(
            render_id=project.render.id,
            file_id=render_file.id,
        )

        logger.info(
            "Added render to project, project_id=%s, user_id=%s, render_id=%s, source_file_id=%s, name=%s, status=%s, visibility=%s",  # noqa: E501
            project.id,
            project.user_id,
            project.render_id,
            project.source_file_id,
            project.name,
            project.status,
            project.visibility,
        )

    async def update_project_status(
        self,
        project_id: int,
    ) -> ProjectWithRenderFileResponse:
        project = await self.project_repository.update_project_status(project_id)
        if project is None:
            raise ProjectIdNotFoundError(project_id)

        logger.info(
            "Updated project status, project_id=%s, user_id=%s, render_id=%s, source_file_id=%s, name=%s, status=%s, visibility=%s",  # noqa: E501
            project.id,
            project.user_id,
            project.render_id,
            project.source_file_id,
            project.name,
            project.status,
            project.visibility,
        )
        return ProjectWithRenderFileResponse.model_validate(project)

    async def create_project(
        self,
        user_id: int,
        create_project: ProjectWithRenderCreate,
    ) -> ProjectWithRenderResponse:
        create_project_data = create_project.project
        create_render_data = create_project.render
        file_id = create_project_data.source_file_id
        file = await self.file_repository.get_by_id(file_id)
        if file is None:
            raise FileIdNotFoundError(file_id)
        render = await self.render_repository.create_render(create_render_data)
        project = await self.project_repository.create_project(
            user_id=user_id,
            render_id=render.id,
            create_project_data=create_project_data,
        )
        render_response = RenderResponse.model_validate(render)
        project_response = ProjectResponse.model_validate(project)
        project_with_render_response = ProjectWithRenderResponse(
            render=render_response,
            **project_response.model_dump(),
        )
        file_location_create = FileLocationCreate(
            bucket=file.bucket,
            key=file.key,
        )
        message = GenerateRenderEvent(
            project_id=project.id,
            render=create_render_data,
            file=file_location_create,
        )
        json_string_message = message.model_dump_json()
        event_create_data = EventCreate(
            topic=KafkaTopic.create_project,
            message=json_string_message,
        )

        await self.outbox_repository.create_event(event_create_data)
        logger.info(
            "Created project, project_id=%s, user_id=%s, render_id=%s, source_file_id=%s, name=%s, status=%s, visibility=%s",  # noqa: E501
            project.id,
            user_id,
            project.render_id,
            project.source_file_id,
            project.name,
            project.status,
            project.visibility,
        )
        return project_with_render_response

    async def partial_update_project(
        self,
        project_id: int,
        user_id: int,
        partial_update_project_data: ProjectPartialUpdate,
    ) -> ProjectWithRenderFileResponse:
        project = await self.project_repository.get_by_id(
            project_id,
        )
        if project is None:
            raise ProjectIdNotFoundError(project_id)

        get_owner_coroutine = self.project_repository.get_project_owner(
            project_id,
        )
        owner = cast(User, await get_owner_coroutine)
        if owner.id != user_id:
            detail = "You are not allowed to watch this project."
            raise PermissionDeniedError(detail)

        project = await self.project_repository.partial_update_project(
            project_id,
            partial_update_project_data,
        )
        logger.info(
            "Updated project, project_id=%s, user_id=%s, render_id=%s, source_file_id=%s, name=%s, status=%s, visibility=%s",  # noqa: E501
            project_id,
            user_id,
            project.render_id,
            project.source_file_id,
            project.name,
            project.status,
            project.visibility,
        )
        return ProjectWithRenderFileResponse.model_validate(project)

    async def delete_by_id(
        self,
        project_id: int,
        user_id: int,
    ) -> None:
        project = await self.project_repository.get_by_id(
            project_id,
        )
        if project is None:
            raise ProjectIdNotFoundError(project_id)

        get_owner_coroutine = self.project_repository.get_project_owner(
            project_id,
        )
        owner = cast(User, await get_owner_coroutine)
        if owner.id != user_id:
            detail = "You are not allowed to watch this project."
            raise PermissionDeniedError(detail)

        await self.project_repository.delete_by_id(project_id)
        logger.info(
            "Deleted project, project_id=%s, user_id=%s, render_id=%s, source_file_id=%s, name=%s, status=%s, visibility=%s",  # noqa: E501
            project_id,
            user_id,
            project.render_id,
            project.source_file_id,
            project.name,
            project.status,
            project.visibility,
        )
