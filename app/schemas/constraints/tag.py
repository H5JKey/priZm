from typing import Annotated

from annotated_types import Len
from core.constants import TAG_MAX_LENGTH, TAG_MIN_LENGTH

NameConstraint = Annotated[
    str,
    Len(
        min_length=TAG_MIN_LENGTH,
        max_length=TAG_MAX_LENGTH,
    ),
]
