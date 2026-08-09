from collections.abc import AsyncGenerator
from typing import Annotated

from aiokafka import AIOKafkaProducer
from core.constants import s3_bucket
from fastapi import Depends
from infrastructure.database.repositories.file import FileRepository
from infrastructure.database.repositories.user import UserRepository
from infrastructure.database.unit_of_work import UnitOfWork
from infrastructure.kafka import generate_render_producer
from infrastructure.minio.client import MinioClient
from services.auth import AuthService
from services.file_uploader import FileUploader
from services.project import ProjectService
from services.user import UserService

from dependencies.minio import get_minio_client
from dependencies.repositories import (
    get_file_repository,
    get_unit_of_work,
    get_user_repository,
)


async def get_aiokafka_producer() -> AIOKafkaProducer:
    return generate_render_producer


async def get_input_file_uploader(
    s3_client: Annotated[
        MinioClient,
        Depends(get_minio_client),
    ],
    file_repository: Annotated[
        FileRepository,
        Depends(get_file_repository),
    ],
) -> AsyncGenerator[FileUploader]:
    file_uploader = FileUploader(
        bucket=s3_bucket.input_bucket,
        s3_client=s3_client,
        file_repository=file_repository,
    )
    yield file_uploader


async def get_auth_service(
    user_repository: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
) -> AsyncGenerator[AuthService]:
    auth_service = AuthService(user_repository)
    yield auth_service


async def get_user_service(
    user_repository: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
) -> AsyncGenerator[UserService]:
    user_service = UserService(user_repository)
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
