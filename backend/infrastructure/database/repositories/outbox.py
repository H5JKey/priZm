from typing import cast

from core.constants import EventStatus
from core.interfaces.repositories import AbstractOutboxRepository
from core.logging import get_logger
from schemas.event import EventCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import Outbox

logger = get_logger(__name__)


class OutboxRepository(AbstractOutboxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, event_id: int) -> Outbox | None:
        stmt = select(Outbox).where(Outbox.id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar()

    async def create_event(self, event_create_data: EventCreate) -> Outbox:
        event = Outbox(**event_create_data.model_dump())
        self.session.add(event)
        await self.session.flush()
        logger.debug(
            "Created event in transaction, transaction_id=%s, topic=%s, message=%s",
            id(self.session),
            event_create_data.topic,
            event_create_data.message,
        )
        return event

    async def mark_event_as_sent(self, event_id: int) -> Outbox:
        event = cast(Outbox, await self.get_by_id(event_id))
        event.status = cast(EventStatus, EventStatus.sent.value)
        await self.session.flush()
        logger.debug(
            "Marked event as sent in transaction, transaction_id=%s, event_id=%s, topic=%s, status=%s",  # noqa: E501
            id(self.session),
            event_id,
            event.topic,
            event.status,
        )
        return event

    async def get_pending_event(self) -> Outbox | None:
        stmt = (
            select(Outbox)
            .where(Outbox.status == EventStatus.pending.value)
            .order_by(Outbox.event_date)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar()
