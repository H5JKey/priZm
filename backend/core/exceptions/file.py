from core.exceptions.base import NotFoundError


class FileNotFoundError(NotFoundError):
    """
    Ошибка, связанная с ненахождением файла.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)


class FileIdNotFoundError(FileNotFoundError):
    """
    Ошибка, связанная с ненахождением id файла.
    """

    def __init__(self, file_id: int) -> None:
        self.file_id = file_id
        detail = f"File with id = {file_id} not found."
        super().__init__(detail)
