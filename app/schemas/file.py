from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from schemas.constraints.file import (
    BucketConstraint,
    KeyConstraint,
    NameConstraint,
    SizeConstraint,
)


class FileBase(BaseModel):
    """
    Базовая схема для работы с файлами.
    """

    name: NameConstraint
    size: SizeConstraint
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class FileLocationCreate(BaseModel):
    """
    Схема для создания расположения файла в хранилище.
    """

    bucket: BucketConstraint
    key: KeyConstraint


class FileCreate(FileBase, FileLocationCreate):
    """
    Схема для создания файла.
    """


class FileResponse(FileBase):
    """
    Схема для вывода информации о файле.
    """

    id: int
