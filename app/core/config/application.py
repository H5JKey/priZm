from pathlib import Path
from typing import ClassVar

from fastapi.security import OAuth2PasswordBearer
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.config.database import DataBaseConfig
from core.config.jwt import JWTConfig
from core.config.kafka import KafkaConfig
from core.config.logging import LoggingConfig
from core.config.minio import MinioConfig


class Settings(BaseSettings):
    base_dir: Path = Path(__file__).parent.parent.parent
    database: DataBaseConfig = DataBaseConfig()
    minio: MinioConfig = MinioConfig()
    kafka: KafkaConfig = KafkaConfig()
    jwt: JWTConfig = JWTConfig()
    logging: LoggingConfig = LoggingConfig()
    oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(
        tokenUrl="/api/v1/auth/login",
    )

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        case_sensitive=False,
        env_file=base_dir / ".env",
        env_nested_delimiter="__",
    )


settings = Settings()
