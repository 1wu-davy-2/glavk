from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.auth import router as auth_router
from .api.projects import router as projects_router
from .api.security import router as security_router
from .auth import AuthService
from .config import Settings
from .db import create_session_factory, ensure_schema
from .services.projects import ProjectService
from .screenshot_service import ScreenshotService
from .transport_crypto import TransportCrypto
from . import models  # noqa: F401


def create_app(*, settings: Settings | None = None, session_factory=None, screenshot_service=None) -> FastAPI:
    app_settings = settings or Settings()
    app_settings.validate_production_security()
    engine = None
    if session_factory is None:
        engine, session_factory = create_session_factory(app_settings.database_url)
    auth_service = AuthService(app_settings)
    project_service = ProjectService(app_settings)
    transport_crypto = TransportCrypto(app_settings.transport_private_key_b64)
    screenshot_service = screenshot_service or ScreenshotService(app_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if engine is not None:
            ensure_schema(engine)
        with session_factory() as session:
            auth_service.ensure_default_admin(session)
        yield

    app = FastAPI(title="glavk API", version="0.1.0", lifespan=lifespan)
    app.state.settings = app_settings
    app.state.session_factory = session_factory
    app.state.auth_service = auth_service
    app.state.project_service = project_service
    app.state.transport_crypto = transport_crypto
    app.state.screenshot_service = screenshot_service
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if app_settings.cors_allow_all else list(app_settings.cors_origins),
        allow_credentials=not app_settings.cors_allow_all,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "glavk-api"}

    app.include_router(auth_router, prefix="/api")
    app.include_router(projects_router, prefix="/api")
    app.include_router(security_router, prefix="/api")

    return app


app = create_app()
