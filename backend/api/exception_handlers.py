from collections.abc import Callable

from core.exceptions.base import (
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundError, not_found_error_exception_handler)
    app.add_exception_handler(ConflictError, conflict_error_exception_handler)
    app.add_exception_handler(
        AuthenticationError,
        authentication_error_exception_handler,
    )
    app.add_exception_handler(ForbiddenError, forbidden_error_exception_handler)


def exception_handler_factory(
    status_code: int,
) -> Callable[[Request, Exception], JSONResponse]:
    def exception_handler(
        request: Request,  # noqa: ARG001
        exception: Exception,
    ) -> JSONResponse:
        detail = getattr(exception, "detail", str(exception))
        return JSONResponse(
            content={"message": detail},
            status_code=status_code,
        )

    return exception_handler


not_found_error_exception_handler = exception_handler_factory(
    status_code=status.HTTP_404_NOT_FOUND,
)
conflict_error_exception_handler = exception_handler_factory(
    status_code=status.HTTP_400_BAD_REQUEST,
)
authentication_error_exception_handler = exception_handler_factory(
    status_code=status.HTTP_403_FORBIDDEN,
)
forbidden_error_exception_handler = exception_handler_factory(
    status_code=status.HTTP_401_UNAUTHORIZED,
)
