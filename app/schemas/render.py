from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from schemas.constraints.render import (
    HeightConstraint,
    SampleConstraint,
    WidthConstraint,
)
from schemas.file import FileResponse


class RenderBase(BaseModel):
    """
    Базовая схема для рендера.
    """

    width: WidthConstraint
    height: HeightConstraint
    samples: SampleConstraint
    denoiser: bool
    gpu: bool

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class RenderCreate(RenderBase):
    """
    Схема для создания рендера.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class RenderResponse(RenderBase):
    """
    Схема для вывода информации о рендере.
    """

    file_id: int | None
    id: int


class RenderWithFileResponse(RenderResponse):
    """
    Схема для вывода информации о рендере вместе с файлом.
    """

    file: FileResponse | None


class RenderFullResponse(RenderResponse):
    """
    Схема для вывода информации о рендере вместе с доступом к результирующему файлу.
    """

    url: str | None = None


class RenderWithFileFullResponse(RenderFullResponse):
    """
    Схема для вывода информации о рендере вместе с файлом и ссылкой на файл.
    """

    file: FileResponse | None
