from typing import Annotated

from core.constants import (
    PROJECT_PAGINATION_PAGE_MIN_VALUE,
    PROJECT_PAGINATION_SIZE_MIN_VALUE,
)
from pydantic import Field

SizeConstraint = Annotated[
    int,
    Field(ge=PROJECT_PAGINATION_SIZE_MIN_VALUE),
]

PageConstraint = Annotated[
    int,
    Field(ge=PROJECT_PAGINATION_PAGE_MIN_VALUE),
]
