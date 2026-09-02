from typing import Annotated

from annotated_types import Len, MaxLen
from core.constants import (
    FILE_BUCKET_MAX_LENGTH,
    FILE_KEY_MAX_LENGTH,
    FILE_NAME_MAX_LENGTH,
    FILE_NAME_MIN_LENGTH,
    FILE_SIZE_MAX_VALUE_BYTES,
    FILE_SIZE_MIN_VALUE_BYTES,
)
from pydantic import Field

NameConstraint = Annotated[
    str,
    Len(
        min_length=FILE_NAME_MIN_LENGTH,
        max_length=FILE_NAME_MAX_LENGTH,
    ),
]

SizeConstraint = Annotated[
    int,
    Field(
        gt=FILE_SIZE_MIN_VALUE_BYTES,
        le=FILE_SIZE_MAX_VALUE_BYTES,
    ),
]

BucketConstraint = Annotated[
    str,
    MaxLen(max_length=FILE_BUCKET_MAX_LENGTH),
]

KeyConstraint = Annotated[
    str,
    MaxLen(max_length=FILE_KEY_MAX_LENGTH),
]
