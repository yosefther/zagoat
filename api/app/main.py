from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.errors import install_error_handlers
from app.monitoring import init_sentry
from app.routes import auth, csrf, health, jobs, me, problems, waitlist


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    init_sentry(settings)
    app = FastAPI(
        title="zagoat API",
        # Interactive docs are for local development only.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", settings.csrf_header_name],
    )
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(csrf.router)
    app.include_router(waitlist.router)
    app.include_router(auth.router)
    app.include_router(me.router)
    app.include_router(problems.router)
    app.include_router(jobs.router)
    app.include_router(jobs.internal)
    return app


app = create_app()
