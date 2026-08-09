import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from core.logging import configure_logging, get_logger
from fastapi import FastAPI
from infrastructure.kafka import (
    add_render_to_project_consume,
    consumer,
    producer,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """
    Действия до старта приложения.
    """
    configure_logging()
    await producer.start()
    asyncio.create_task(  # noqa: RUF006
        add_render_to_project_consume(consumer),
    )
    logger.info("Application started")
    yield
    await producer.stop()
    await consumer.stop()
    logger.info("Application has completed")
    """
    Действия при завершении работы приложения.
    """
