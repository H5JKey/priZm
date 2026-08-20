from typing import Self

from infrastructure.database.models import File, Project, Render
from pydantic import BaseModel

from schemas.constraints.event import TopicConstraint
from schemas.file import FileLocationCreate
from schemas.render import RenderCreate


class EventBase(BaseModel):
    """
    Схема для работы с outbox.
    """


class GenerateRenderEvent(BaseModel):
    """
    Схема для события генерация проекта.
    """

    project_id: int
    render: RenderCreate
    file: FileLocationCreate

    @classmethod
    def get_from_database(
        cls,
        project: Project,
        render: Render,
        file: File,
    ) -> Self:
        file_location_create = FileLocationCreate.model_validate(file)
        create_render_data = RenderCreate.model_validate(render)
        return cls(
            project_id=project.id,
            render=create_render_data,
            file=file_location_create,
        )


class EventCreate(BaseModel):
    """
    Схема для создания записи о событии в outbox.
    """

    topic: TopicConstraint
    message: dict  # type: ignore[type-arg]

    @classmethod
    def get_from_database(
        cls,
        project: Project,
        render: Render,
        file: File,
        topic: str,
    ) -> Self:
        message = GenerateRenderEvent.get_from_database(
            project,
            render,
            file,
        )
        return cls(
            topic=topic,
            message=message.model_dump(),
        )


class AddRenderProjectEvent(BaseModel):
    """
    Схема для события загрузка готового рендера в проект.
    """

    project_id: int
    file: FileLocationCreate
