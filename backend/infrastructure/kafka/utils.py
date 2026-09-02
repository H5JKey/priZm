import asyncio
from json import dumps, loads

from aiokafka import AIOKafkaProducer
from aiokafka.errors import (
    BrokerNotAvailableError,
    KafkaConnectionError,
    RequestTimedOutError,
)
from core.exceptions.base import KafkaSendError
from core.logging import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)


def serialize_message[T: BaseModel](message_data: T) -> bytes:
    message_dict = message_data.model_dump()
    serialized_value = dumps(message_dict)
    encoded_serialized_value = serialized_value.encode()
    return encoded_serialized_value


def deserialize_message(message: bytes) -> dict[str, str | int | bool]:
    message_string = message.decode()
    json_message = loads(message_string)
    return json_message  # type: ignore[no-any-return]


async def send_message(
    producer: AIOKafkaProducer,
    topic: str,
    value: bytes | None = None,
    key: str | None = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> None:
    delay = base_delay
    for attempt in range(1, max_retries + 1):
        try:
            await producer.send_and_wait(
                topic=topic,
                key=key,
                value=value,
            )
            logger.info(
                "Sent message, topic=%s, key=%s,value=%s",
                topic,
                key,
                value,
            )
            return  # noqa: TRY300
        except (KafkaConnectionError, RequestTimedOutError, BrokerNotAvailableError):
            logger.warning(
                "Kafka send failed. Retry %s/%s, topic='%s', key='%s', delay=%.2fs",
                attempt,
                max_retries,
                topic,
                key,
                delay,
            )
            await asyncio.sleep(delay)
            delay *= 2

    logger.error(
        "Message sending failed, topic=%s, key=%s,value=%s",
        topic,
        key,
        value,
    )
    error_detail = "Message sending failed"
    raise KafkaSendError(error_detail)
