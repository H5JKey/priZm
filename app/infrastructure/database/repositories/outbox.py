from typing import cast

from core.constants import EventStatus
from core.interfaces.repositories import AbstractOutboxRepository
from schemas.event import EventCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import Outbox


class OutboxRepository(AbstractOutboxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, event_id: int) -> Outbox | None:
        stmt = select(Outbox).where(Outbox.id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar()

    async def send_event(self, event_id: int) -> Outbox:
        event = cast(Outbox, await self.get_by_id(event_id))
        event.status = cast(EventStatus, EventStatus.sent.value)
        await self.session.flush()
        return event

    async def create_event(self, event_create_data: EventCreate) -> Outbox:
        event = Outbox(**event_create_data.model_dump())
        self.session.add(event)
        await self.session.flush()
        return event
