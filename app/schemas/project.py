from typing import TYPE_CHECKING, ClassVar, Self

from core.constants import ProjectVisibility, RenderStatus
from infrastructure.database.models import Project, Render
from pydantic import BaseModel, ConfigDict

from schemas.constraints.pagination import PageConstraint, SizeConstraint
from schemas.constraints.project import DescriptionConstraint, NameConstraint
from schemas.render import (
    RenderCreatePayload,
    RenderResponse,
    RenderWithFileFullResponse,
    RenderWithFileResponse,
)

if TYPE_CHECKING:
    from core.interfaces.clients import AbstractS3Client


class ProjectBase(BaseModel):
    """
    Базовая схема для проекта.
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

    render: RenderCreatePayload
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
    user_id: int
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

    @classmethod
    async def get_from_database(
        cls,
        project: Project,
        s3_client: "AbstractS3Client",
    ) -> Self:
        project_response = ProjectResponse.model_validate(project)
        source_file_url = await s3_client.generate_presigned_url(
            bucket=project.source_file.bucket,
            key=project.source_file.key,
            expires_in=10 * 60,
            client_method="get_object",
        )

        render = RenderWithFileFullResponse.model_validate(project.render)
        if project.render.file is not None:
            render_file_url = await s3_client.generate_presigned_url(
                bucket=project.render.file.bucket,
                key=project.render.file.key,
                expires_in=10 * 60,
                client_method="get_object",
            )
            render.url = render_file_url.replace("minio", "localhost")

        return cls(
            **project_response.model_dump(),
            render=render,
            url=source_file_url.replace("minio", "localhost"),
        )


class ProjectWithRenderResponse(ProjectResponse):
    """
    Схема для вывода информации о проекте с рендером.
    """

    render: RenderResponse

    @classmethod
    def get_from_database(cls, project: Project, render: Render) -> Self:
        render_response = RenderResponse.model_validate(render)
        project_response = ProjectResponse.model_validate(project)
        return cls(
            render=render_response,
            **project_response.model_dump(),
        )


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
    size: SizeConstraint
    page: PageConstraint


class ProjectWithRenderFileResponseList(BaseModel):
    """
    Схема для вывода информации о списке проектов с рендером.
    """

    project_list: list[ProjectWithRenderFileResponse]
    size: SizeConstraint
    page: PageConstraint
