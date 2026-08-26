from core.interfaces.repositories import AbstractTagRepository
from schemas.tag import TagCreate
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import Tag


class TagRepository(AbstractTagRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, tag_id: int) -> Tag | None:
        return await self.session.get(Tag, tag_id)

    async def get_project_tags(self, project_id: int) -> list[Tag] | None:
        stmt = select(Tag).where(Tag.project_id == project_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_tag(self, create_tag_data: TagCreate) -> Tag:
        tag = Tag(**create_tag_data.model_dump())
        self.session.add(tag)
        await self.session.flush()
        return tag

    async def delete_by_id(self, tag_id: int) -> None:
        stmt = delete(Tag).where(Tag.id == tag_id)
        await self.session.execute(stmt)
        await self.session.flush()
