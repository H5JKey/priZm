from abc import ABC, abstractmethod
from typing import BinaryIO

from schemas.file import FileResponse


class AbstractFileUploader(ABC):
    """
    Интерфейс для сервиса загрузки файлов.
    """

    @abstractmethod
    async def upload(
        self,
        file_name: str,
        file: BinaryIO,
    ) -> FileResponse:
        """
        Метод для загрузки файла.
        """
