from pydantic import BaseModel

from schemas.constraints.event import TopicConstraint
from schemas.file import FileLocation, FileLocationCreate
from schemas.render import RenderCreatePayload


class EventBase(BaseModel):
    """
    Схема для работы с outbox.
    """


class GenerateRenderEvent(BaseModel):
    """
    Схема для события генерация проекта.
    """

    project_id: int
    input: FileLocationCreate
    output: FileLocation
    render: RenderCreatePayload


class EventCreate(BaseModel):
    """
    Схема для создания записи о событии в outbox.
    """

    topic: TopicConstraint
    message: dict  # type: ignore[type-arg]


class AddRenderProjectEvent(BaseModel):
    """
    Схема для события загрузка готового рендера в проект.
    """

    project_id: int
    output: FileLocationCreate
