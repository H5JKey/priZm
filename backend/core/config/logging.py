from typing import Literal

from pydantic import BaseModel


class LoggingFormatterConfig(BaseModel):
    format: str = (
        "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"  # noqa: E501
    )
    datefmt: str = "%Y-%m-%d %H:%M:%S"


class LoggingConfig(BaseModel):
    level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "DEBUG"
    formatter: LoggingFormatterConfig = LoggingFormatterConfig()
    base_logger_name: str = "backend"
