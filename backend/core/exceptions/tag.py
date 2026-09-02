from core.exceptions.base import NotFoundError


class TagNotFoundError(NotFoundError):
    """
    Класс для ошибок, связанных с
    ненахождением тэга проекта.
    """

    def __init__(self, detail: str) -> None:
        self.detail = detail


class TagIdNotFoundError(TagNotFoundError):
    """
    Класс для ошибок, связанных с
    ненахождением тэга по id.
    """

    def __init__(self, tag_id: int) -> None:
        self.tag_id = tag_id
        detail = f"Tag with id = {tag_id} not found."
        super().__init__(detail)
