from core.exceptions.base import NotFoundError


class ProjectNotFoundError(NotFoundError):
    """
    Ошибка, связанная с ненахождением проекта.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)


class ProjectIdNotFoundError(ProjectNotFoundError):
    """
    Ошибка, связанная с ненахождением id проекта.
    """

    def __init__(self, project_id: int) -> None:
        self.project_id = project_id
        detail = f"Project with id = {project_id} not found."
        super().__init__(detail)
