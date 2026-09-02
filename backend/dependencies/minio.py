from collections.abc import AsyncGenerator
from typing import Annotated

from aiobotocore.client import AioBaseClient
from aiobotocore.session import AioSession
from core.config.application import settings
from fastapi import Depends
from infrastructure.minio.client import MinioClient
from infrastructure.minio.session import get_minio_session


async def get_s3_client(
    session: Annotated[
        AioSession,
        Depends(get_minio_session),
    ],
) -> AsyncGenerator[AioBaseClient]:
    async with session.create_client(
        "s3",
        **settings.minio.config,
    ) as client:
        yield client


async def get_minio_client(
    s3_client: Annotated[
        AioBaseClient,
        Depends(get_s3_client),
    ],
) -> AsyncGenerator[MinioClient]:
    minio_client = MinioClient(s3_client)
    yield minio_client
