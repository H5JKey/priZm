from pydantic import BaseModel

from schemas.constraints.event import MessageConstraint, TopicConstraint
from schemas.file import FileLocationCreate
from schemas.render import RenderCreate


class GenerateRenderEvent(BaseModel):
    """
    Схема для события генерация проекта.
    """

    project_id: int
    render: RenderCreate
    file: FileLocationCreate


class AddRenderProjectEvent(BaseModel):
    """
    Схема для события загрузка готового рендера в проект.
    """

    project_id: int
    file: FileLocationCreate


class EventBase(BaseModel):
    """
    Схема для работы с outbox.
    """


class EventCreate(BaseModel):
    """
    Схема для создания записи о событии в outbox.
    """

    topic: TopicConstraint
    message: MessageConstraint
