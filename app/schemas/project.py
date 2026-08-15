from typing import ClassVar

from core.constants import ProjectVisibility, RenderStatus
from pydantic import BaseModel, ConfigDict

from schemas.constraints.project import DescriptionConstraint, NameConstraint
from schemas.render import (
    RenderCreate,
    RenderResponse,
    RenderWithFileFullResponse,
    RenderWithFileResponse,
)


class ProjectBase(BaseModel):
    """
    Базовая схема для создания проекта.
    """

    name: NameConstraint
    description: DescriptionConstraint
    source_file_id: int
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class ProjectCreate(ProjectBase):
    """
    Схема для создания проекта.
    """

    visibility: ProjectVisibility


class ProjectWithRenderCreate(BaseModel):
    """
    Схема для создания проекта c предоставлением данных о рендере.
    """

    render: RenderCreate
    project: ProjectCreate


class ProjectPartialUpdate(BaseModel):
    """
    Схема для частичного обновления проекта от пользователя.
    """

    name: NameConstraint | None = None
    description: DescriptionConstraint | None = None
    visibility: ProjectVisibility | None = None


class ProjectResponse(ProjectBase):
    """
    Схема для вывода информации о проекте.
    """

    visibility: ProjectVisibility
    status: RenderStatus
    render_id: int | None
    id: int


class ProjectFullResponse(ProjectResponse):
    """
    Схема для вывода информации о проекте вместе с ссылкой доступа к исходному файлу.
    """

    url: str


class ProjectWithRenderFileFullResponse(ProjectFullResponse):
    """
    Схема для вывода информации о проекте с рендером.
    """

    render: RenderWithFileFullResponse


class ProjectWithRenderResponse(ProjectResponse):
    """
    Схема для вывода информации о проекте с рендером.
    """

    render: RenderResponse


class ProjectWithRenderFileResponse(ProjectResponse):
    """
    Схема для вывода информации о проекте с файлом рендера.
    """

    render: RenderWithFileResponse


class ProjectResponseList(BaseModel):
    """
    Схема для вывода информации о списке проектов.
    """

    project_list: list[ProjectResponse]
    size: int
    page: int


class ProjectWithRenderFileResponseList(BaseModel):
    """
    Схема для вывода информации о списке проектов с рендером.
    """

    project_list: list[ProjectWithRenderFileResponse]
    size: int
    page: int
