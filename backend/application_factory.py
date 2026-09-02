from api import router as api_router
from api.exception_handlers import register_exception_handlers
from api.main_views import router as main_router
from fastapi import FastAPI
from lifespan import lifespan


def include_routers(app: FastAPI) -> None:
    app.include_router(main_router)
    app.include_router(api_router)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Renderer",
        lifespan=lifespan,  # type[arg-type]
    )
    include_routers(app)
    register_exception_handlers(app)
    return app
