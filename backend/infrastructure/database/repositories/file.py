from core.interfaces.repositories import AbstractFileRepository
from core.logging import get_logger
from schemas.file import FileCreate
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import File

logger = get_logger(__name__)


class FileRepository(AbstractFileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, file_id: int) -> File | None:
        stmt = select(File).where(File.id == file_id)
        result = await self.session.execute(stmt)
        return result.scalar()

    async def create_file(self, create_file_data: FileCreate) -> File:
        file = File(
            **create_file_data.model_dump(),
        )
        self.session.add(file)
        await self.session.flush()
        logger.debug(
            "Created file, transaction_id=%s, file_id=%s, bucket=%s, key=%s, name=%s, size=%s",  # noqa: E501
            id(self.session),
            file.id,
            file.bucket,
            file.key,
            file.name,
            file.size,
        )
        return file

    async def delete_by_id(self, file_id: int) -> None:
        stmt = delete(File).where(File.id == file_id)
        await self.session.execute(stmt)
        await self.session.flush()
        logger.debug(
            "Deleted file, transaction_id=%s, file_id=%s",
            id(self.session),
            file_id,
        )
