import asyncio

from aiokafka import AIOKafkaProducer
from core.logging import configure_logging, get_logger

from outbox_worker.helpers import run_worker

logger = get_logger(__name__)


async def main() -> None:
    configure_logging()
    outbox_worker_producer = AIOKafkaProducer(bootstrap_servers=["kafka:9092"])
    await outbox_worker_producer.start()
    logger.info("Kafka producer for outbox worker started")
    await run_worker(outbox_worker_producer)


if __name__ == "__main__":
    asyncio.run(main())
