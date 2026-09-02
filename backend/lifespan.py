import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from core.logging import configure_logging, get_logger
from fastapi import FastAPI
from infrastructure.kafka.consumer import consume, get_consumer

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """
    Действия до старта приложения.
    """
    configure_logging()
    consumer = await get_consumer()
    asyncio.create_task(  # noqa: RUF006
        consume(consumer),
    )
    logger.info("Application started")
    yield
    await consumer.stop()
    logger.info("Application has completed")
    """
    Действия при завершении работы приложения.
    """
