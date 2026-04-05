import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import app.models  # noqa: F401
from app.api.routes.audit import router as audit_router
from app.api.routes.auth import router as auth_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.exports import router as exports_router
from app.api.routes.health import router as health_router
from app.api.routes.matches import router as matches_router
from app.api.routes.scheduling import router as scheduling_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.students import router as students_router
from app.api.routes.teachers import router as teachers_router
from app.core.config import get_settings
from app.core.db import SessionLocal, engine
from app.models.base import Base


settings = get_settings()
logger = logging.getLogger("timetabling")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class RawPreflightLoggingMiddleware:
    def __init__(self, app, *, enabled: bool):
        self.app = app
        self.enabled = enabled

    async def __call__(self, scope, receive, send):
        if self.enabled and scope["type"] == "http" and scope["method"] == "OPTIONS":
            headers = {
                key.decode("latin-1").lower(): value.decode("latin-1")
                for key, value in scope.get("headers", [])
            }
            logger.info(
                "PRE-CORS OPTIONS %s origin=%s acr-method=%s acr-headers=%s",
                scope.get("path"),
                headers.get("origin"),
                headers.get("access-control-request-method"),
                headers.get("access-control-request-headers"),
            )
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.auto_create_schema:
        Base.metadata.create_all(bind=engine)
    if settings.app_env != "test":
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    yield


fastapi_app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if settings.expose_docs else None,
    redoc_url="/redoc" if settings.expose_docs else None,
    openapi_url="/openapi.json" if settings.expose_docs else None,
)
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.resolved_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@fastapi_app.middleware("http")
async def security_middleware(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.request_size_limit_bytes:
        return JSONResponse(status_code=413, content={"detail": "Request body is too large"})

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
    return response


@fastapi_app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})


@fastapi_app.exception_handler(IntegrityError)
async def integrity_exception_handler(_: Request, __: IntegrityError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": "Request violates a database constraint."})


fastapi_app.include_router(health_router, prefix=settings.api_prefix)
fastapi_app.include_router(auth_router, prefix=settings.api_prefix)
fastapi_app.include_router(dashboard_router, prefix=settings.api_prefix)
fastapi_app.include_router(audit_router, prefix=settings.api_prefix)
fastapi_app.include_router(exports_router, prefix=settings.api_prefix)
fastapi_app.include_router(teachers_router, prefix=settings.api_prefix)
fastapi_app.include_router(students_router, prefix=settings.api_prefix)
fastapi_app.include_router(sessions_router, prefix=settings.api_prefix)
fastapi_app.include_router(matches_router, prefix=settings.api_prefix)
fastapi_app.include_router(scheduling_router, prefix=settings.api_prefix)

app = RawPreflightLoggingMiddleware(fastapi_app, enabled=settings.cors_debug_logging)
