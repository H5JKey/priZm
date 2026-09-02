from typing import Annotated

from core.constants import (
    RENDER_HEIGHT_MAX_VALUE,
    RENDER_HEIGHT_MIN_VALUE,
    RENDER_SAMPLES_MAX_VALUE,
    RENDER_SAMPLES_MIN_VALUE,
    RENDER_WIDTH_MAX_VALUE,
    RENDER_WIDTH_MIN_VALUE,
)
from pydantic import Field

WidthConstraint = Annotated[
    int,
    Field(
        ge=RENDER_WIDTH_MIN_VALUE,
        le=RENDER_WIDTH_MAX_VALUE,
    ),
]

HeightConstraint = Annotated[
    int,
    Field(
        ge=RENDER_HEIGHT_MIN_VALUE,
        le=RENDER_HEIGHT_MAX_VALUE,
    ),
]


SampleConstraint = Annotated[
    int,
    Field(
        ge=RENDER_SAMPLES_MIN_VALUE,
        le=RENDER_SAMPLES_MAX_VALUE,
    ),
]
