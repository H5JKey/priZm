from json import dumps
from types import TracebackType
from typing import Self

from aiokafka import AIOKafkaProducer
from core.constants import kafka_topic
from core.interfaces.clients import AbstractUnitOfWorkClient
from core.logging import get_logger
from infrastructure.database.repositories.outbox import OutboxRepository
from sqlalchemy.dialects.postgresql import JSONB

logger = get_logger(__name__)


class OutboxWorker:
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWorkClient,
        producer: AIOKafkaProducer,
    ) -> None:
        self._unit_of_work = unit_of_work
        self.outbox_repository = self._unit_of_work.get_repository(OutboxRepository)
        self.producer = producer

    async def __aenter__(self) -> "Self":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Выполняется при выходе из контекстного менеджера OutboxWorker.
        """

    async def process_messages(self) -> None:
        event = await self.outbox_repository.get_pending_event()
        if event is None:
            return

        logger.info("Received message, message=%s", event.message)
        message = self._serialize_message(event.message)
        await self.outbox_repository.mark_event_as_sent(event.id)
        await self.producer.send(
            topic=kafka_topic.create_project,
            value=message,
        )
        logger.info(
            "Sent message, topic=%s, message=%s",
            kafka_topic.create_project,
            message,
        )

    @staticmethod
    def _serialize_message(message: JSONB) -> bytes:
        json_data = dumps(message)
        json_data_bytes = json_data.encode()
        return json_data_bytes
