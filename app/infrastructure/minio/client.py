from io import BytesIO
from types import TracebackType
from typing import BinaryIO, Self, cast

from aiobotocore.client import AioBaseClient
from core.interfaces.clients import AbstractS3Client
from core.logging import get_logger

logger = get_logger(__name__)


class MinioClient(AbstractS3Client):
    def __init__(self, s3_client: AioBaseClient) -> None:
        self.minio_client = s3_client

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    async def get_file_size(self, bucket: str, key: str) -> int:
        response = await self.head_object(
            bucket=bucket,
            key=key,
        )
        return response["ContentLength"]

    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        client_method: str,
        expires_in: int,
    ) -> str:
        params = {
            "Bucket": bucket,
            "Key": key,
        }
        presigned_url = await self.minio_client.generate_presigned_url(
            ClientMethod=client_method,
            Params=params,
            ExpiresIn=expires_in,
        )
        return cast(str, presigned_url)

    async def head_object(self, bucket: str, key: str) -> dict:
        return await self.minio_client.head_object(Bucket=bucket, Key=key)

    async def get_object(self, bucket: str, key: str) -> BinaryIO:
        file_response = await self.minio_client.get_object(
            Bucket=bucket,
            Key=key,
        )
        file = file_response["Body"]
        file_binary = await file.read()
        logger.debug("Received file, bucket=%s, key=%s", bucket, key)
        return cast(BinaryIO, BytesIO(file_binary))

    async def put_object(
        self,
        bucket: str,
        key: str,
        file: BinaryIO,
    ) -> None:
        await self.minio_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=file,
        )
        logger.debug("Created file, bucket=%s, key=%s", bucket, key)

    async def delete_object(self, bucket: str, key: str) -> None:
        await self.minio_client.delete_object(
            Bucket=bucket,
            Key=key,
        )
        logger.debug("Deleted file, bucket=%s, key=%s", bucket, key)
