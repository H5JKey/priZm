from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from schemas.constraints.tag import NameConstraint


class TagBase(BaseModel):
    """
    Базовая схема для работы с тэгами.
    """

    name: NameConstraint
    project_id: int
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class TagCreate(TagBase):
    """
    Схема для добавления тэга к проекту.
    """


class TagResponse(TagBase):
    """
    Схема для вывода информации о тэге.
    """

    id: int


class TagResponseList(BaseModel):
    """
    Схема для вывода информации о списке тэгов проекта.
    """

    tag_list: list[TagResponse]
