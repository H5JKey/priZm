from collections.abc import AsyncGenerator
from typing import Annotated

from core.config.application import settings
from fastapi import Depends
from infrastructure.database.unit_of_work import UnitOfWork
from infrastructure.minio.client import MinioClient
from services.auth import AuthService
from services.file_uploader import FileUploader
from services.project import ProjectService
from services.tag import TagService
from services.user import UserService

from dependencies.minio import get_minio_client
from dependencies.repositories import (
    get_unit_of_work,
)


async def get_input_file_uploader(
    s3_client: Annotated[
        MinioClient,
        Depends(get_minio_client),
    ],
    unit_of_work: Annotated[
        UnitOfWork,
        Depends(get_unit_of_work),
    ],
) -> AsyncGenerator[FileUploader]:
    file_uploader = FileUploader(
        bucket=settings.minio.bucket.input,
        s3_client=s3_client,
        unit_of_work=unit_of_work,
    )
    yield file_uploader


async def get_auth_service(
    unit_of_work: Annotated[
        UnitOfWork,
        Depends(get_unit_of_work),
    ],
) -> AsyncGenerator[AuthService]:
    auth_service = AuthService(unit_of_work)
    yield auth_service


async def get_user_service(
    unit_of_work: Annotated[
        UnitOfWork,
        Depends(get_unit_of_work),
    ],
) -> AsyncGenerator[UserService]:
    user_service = UserService(unit_of_work)
    yield user_service


async def get_project_service(
    unit_of_work: Annotated[
        UnitOfWork,
        Depends(get_unit_of_work),
    ],
) -> AsyncGenerator[ProjectService]:
    project_service = ProjectService(
        unit_of_work,
    )
    yield project_service


async def get_tag_service(
    unit_of_work: Annotated[
        UnitOfWork,
        Depends(get_unit_of_work),
    ],
) -> AsyncGenerator[TagService]:
    tag_service = TagService(
        unit_of_work,
    )
    yield tag_service
