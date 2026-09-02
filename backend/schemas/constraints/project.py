from typing import Annotated

from annotated_types import Len
from core.constants import (
    PROJECT_DESCRIPTION_MAX_LENGTH,
    PROJECT_DESCRIPTION_MIN_LENGTH,
    PROJECT_NAME_MAX_LENGTH,
    PROJECT_NAME_MIN_LENGTH,
)

NameConstraint = Annotated[
    str,
    Len(
        min_length=PROJECT_NAME_MIN_LENGTH,
        max_length=PROJECT_NAME_MAX_LENGTH,
    ),
]


DescriptionConstraint = Annotated[
    str,
    Len(
        min_length=PROJECT_DESCRIPTION_MIN_LENGTH,
        max_length=PROJECT_DESCRIPTION_MAX_LENGTH,
    ),
]
