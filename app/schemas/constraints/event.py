from typing import Annotated

from annotated_types import MaxLen
from core.constants import OUTBOX_MESSAGE_MAX_LENGTH, OUTBOX_TOPIC_MAX_LENGTH

TopicConstraint = Annotated[
    str,
    MaxLen(
        max_length=OUTBOX_TOPIC_MAX_LENGTH,
    ),
]

MessageConstraint = Annotated[
    str,
    MaxLen(
        max_length=OUTBOX_MESSAGE_MAX_LENGTH,
    ),
]
