from pydantic import BaseModel


class DataBaseConfig(BaseModel):
    username: str = "username"
    password: str = "password"
    host: str = "localhost"
    port: int = 5432
    db_name: str = "renderer"

    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    expire_on_commit: bool = True
    echo: bool = False

    naming_convention: dict[str, str] = {
        "pk": "pk_%(table_name)s_%(column_0_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "ix": "ix_%(table_name)s_%(column_0_name)s",
    }

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"
