from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tributaria_api.api.http_errors import register_exception_handlers
from tributaria_api.api.router import api_router
from tributaria_api.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Plataforma Tributaria API",
        version="0.2.0",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
    )
    register_exception_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type", "X-Correlation-ID", "X-CSRF-Token"],
    )
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
