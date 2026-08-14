import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaProducer
from core.logging import get_logger
from infrastructure.database.core import session_factory
from infrastructure.database.unit_of_work import UnitOfWork

from outbox_worker.worker import OutboxWorker

logger = get_logger(__name__)


@asynccontextmanager
async def get_outbox_worker(producer: AIOKafkaProducer) -> AsyncGenerator[OutboxWorker]:
    async with session_factory() as session, UnitOfWork(session) as unit_of_work:
        outbox_worker = OutboxWorker(
            unit_of_work,
            producer,
        )
        yield outbox_worker


async def run_worker(producer: AIOKafkaProducer) -> None:
    logger.info("Outbox worker started")
    while True:
        async with get_outbox_worker(producer) as outbox_worker:
            await outbox_worker.process_messages()
        await asyncio.sleep(5)
