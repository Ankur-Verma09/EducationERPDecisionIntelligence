"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from education_erp import __version__
from education_erp.api.connectors import router as connectors_router
from education_erp.api.health import router as health_router
from education_erp.api.phase2 import router as phase2_router
from education_erp.api.phase2_extended import router as phase2_extended_router
from education_erp.api.phase3 import router as phase3_router
from education_erp.config import Settings, get_settings
from education_erp.database import create_database_engine
from education_erp.errors import install_error_handlers
from education_erp.identity.oidc import OidcJwtVerifier
from education_erp.logging import configure_logging
from education_erp.middleware import RequestContextMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the application and its process-scoped dependencies."""

    resolved = settings or get_settings()
    engine = create_database_engine(resolved)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        app.state.database_engine.dispose()

    app = FastAPI(
        title=resolved.app_name,
        version=__version__,
        docs_url="/docs" if resolved.docs_enabled else None,
        redoc_url="/redoc" if resolved.docs_enabled else None,
        openapi_url="/openapi.json" if resolved.docs_enabled else None,
        lifespan=lifespan,
    )
    app.state.settings = resolved
    app.state.database_engine = engine
    app.state.token_verifier = (
        OidcJwtVerifier(resolved) if resolved.oidc_issuer_url and resolved.oidc_audience else None
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(resolved.allowed_hosts))
    app.add_middleware(RequestContextMiddleware)
    install_error_handlers(app)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(connectors_router, prefix="/api/v1")
    app.include_router(phase2_router, prefix="/api/v1")
    app.include_router(phase2_extended_router, prefix="/api/v1")
    app.include_router(phase3_router, prefix="/api/v1")
    return app


_default_settings = get_settings()
configure_logging(_default_settings.log_level)
app = create_app(_default_settings)
