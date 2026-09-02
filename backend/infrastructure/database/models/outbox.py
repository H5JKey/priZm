from datetime import datetime

from core.constants import (
    OUTBOX_TOPIC_MAX_LENGTH,
    EventStatus,
)
from sqlalchemy import Enum, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.core import Base


class Outbox(Base):
    __tablename__ = "outbox"

    topic: Mapped[str] = mapped_column(String(OUTBOX_TOPIC_MAX_LENGTH))
    message: Mapped[dict] = mapped_column(JSONB)  # type: ignore[type-arg]
    event_date: Mapped[datetime] = mapped_column(
        server_default=func.timezone("UTC", func.now()),
    )
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status"),
        server_default=EventStatus.pending.value,
    )
