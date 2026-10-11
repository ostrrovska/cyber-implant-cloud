from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Cyber-Implant Cloud Control Center",
        description="Cloud control center for cyber-implants: mass async OTA firmware rollout",
        version="0.1.0",
        lifespan=lifespan,
    )
    register_exception_handlers(app)  # Lab2/Lab3
    app.include_router(api_router)

    # Lab3: optional demo-error route for the security-modes demonstration.
    if get_settings().enable_demo_error_route:
        from app.api.routes import diagnostics

        app.include_router(diagnostics.router)

    return app


app = create_app()
