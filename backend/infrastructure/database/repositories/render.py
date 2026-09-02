from typing import cast

from core.interfaces.repositories import AbstractRenderRepository
from core.logging import get_logger
from schemas.render import RenderCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from infrastructure.database.models import Render

logger = get_logger(__name__)


class RenderRepository(AbstractRenderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_render(self, render_id: int) -> Render | None:
        stmt = (
            select(Render)
            .options(joinedload(Render.file))
            .where(Render.id == render_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar()

    async def create_render(self, create_render_data: RenderCreate) -> Render:
        render = Render(**create_render_data.model_dump())
        self.session.add(render)
        await self.session.flush()
        logger.debug(
            "Created render in transaction, transaction_id=%s, render_id=%s, width=%s, height=%s, samples=%s, denoiser=%s, gpu=%s",  # noqa: E501
            id(self.session),
            render.id,
            render.width,
            render.height,
            render.samples,
            render.denoiser,
            render.gpu,
        )
        return render

    async def add_render_file(self, render_id: int, file_id: int) -> Render:
        render = cast(Render, await self.get_render(render_id))
        render.file_id = file_id
        await self.session.flush()
        logger.debug(
            "Added file to render in transaction, transaction_id=%s, render_id=%s, file_id=%s",  # noqa: E501
            id(self.session),
            render.id,
            file_id,
        )
        return render
