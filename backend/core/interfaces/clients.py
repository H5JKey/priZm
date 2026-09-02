from abc import ABC, abstractmethod
from types import TracebackType
from typing import BinaryIO, Self

from core.interfaces.repositories import AbstractRepository


class AbstractS3Client(ABC):
    """
    Интерфейс для работы с s3 хранилищем.
    """

    @abstractmethod
    async def get_file_size(self, bucket: str, key: str) -> int:
        """
        Получить размер файла в байтах.
        """

    @abstractmethod
    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        client_method: str,
        expires_in: int,
    ) -> str:
        """
        Получить ссылку для временного доступа.
        """

    @abstractmethod
    async def get_object(self, bucket: str, key: str) -> BinaryIO:
        """
        Метод для получения файла из s3 хранилища.
        """

    @abstractmethod
    async def put_object(self, bucket: str, key: str, file: BinaryIO) -> None:
        """
        Метод для загрузки файла в s3 хранилище.
        """

    @abstractmethod
    async def delete_object(self, bucket: str, key: str) -> None:
        """
        Метод для удаления файла из s3 хранилища.
        """


class AbstractUnitOfWorkClient(ABC):
    """
    Интерфейс для использования unit of work паттерна.
    """

    @abstractmethod
    async def __aenter__(self) -> Self:
        """
        Метод для выполнения действий при входе
        в асинхронный контекстный менеджер.
        """

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Метод для выполнения действий при выходе
        из асинхронного контекстного менеджера.
        """

    @abstractmethod
    def get_repository(  # type: ignore[no-untyped-def] # noqa: ANN201
        self,
        repository_class: type[AbstractRepository],
    ):
        """
        Метод для получения репозитория
        """

    @abstractmethod
    async def rollback(self) -> None:
        """
        Метод для отмены действий в транзакции.
        """

    @abstractmethod
    async def commit(self) -> None:
        """
        Метод для коммита транзакции.
        """
