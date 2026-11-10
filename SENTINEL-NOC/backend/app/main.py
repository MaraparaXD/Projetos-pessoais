import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from redis import Redis
from sqlalchemy import text

from app.application.bootstrap import bootstrap
from app.core.config import get_settings
from app.infrastructure.database import SessionLocal, engine
from app.interfaces.dependencies import admin
from app.interfaces.middleware import SafetyMiddleware
from app.interfaces.routes import router
from app.interfaces.schemas import EventIn

logging.basicConfig(level=logging.INFO, format="%(message)s")


@asynccontextmanager
async def lifespan(app):
    with SessionLocal() as db:
        bootstrap(db)
    yield
    engine.dispose()


def create_app(with_bootstrap=True):
    settings = get_settings()
    app = FastAPI(
        title="SENTINEL NOC",
        version="0.1.0",
        lifespan=lifespan if with_bootstrap else None,
        description="Fases 1 e 2. Dados do laboratório são sintéticos. Autenticação Bearer revogável.",
    )
    app.include_router(router)

    def openapi():
        if app.openapi_schema is None:
            schema = get_openapi(
                title=app.title, version=app.version, description=app.description, routes=app.routes
            )
            event_schema = EventIn.model_json_schema(ref_template="#/components/schemas/{model}")
            definitions = event_schema.pop("$defs", {})
            schema["components"]["schemas"].update(definitions)
            schema["components"]["schemas"]["EventIn"] = event_schema
            operation = schema["paths"]["/api/webhooks/checkmk/{integration_id}"]["post"]
            operation["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/EventIn"}}},
            }
            operation["description"] = (
                "HMAC SHA-256 over timestamp + '.' + exact body. 201 new; 200 exact replay; 409 conflicting source ID."
            )
            operation["responses"]["201"] = {"description": "New event committed"}
            app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = openapi
    app.add_middleware(SafetyMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Sentinel-Timestamp", "X-Sentinel-Signature"],
        expose_headers=["X-Correlation-ID"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {"loc": list(error["loc"]), "type": error["type"], "msg": error["msg"]}
                    for error in exc.errors()
                ]
            },
        )

    @app.get("/health", tags=["observability"])
    def health():
        return {"status": "ok"}

    @app.get("/ready", tags=["observability"])
    def ready():
        try:
            with engine.connect() as connection:
                revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
                if revision != "0001":
                    raise ValueError("Unexpected migration revision")
            if settings.redis_url:
                with Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1) as redis:
                    redis.ping()
        except Exception:
            raise HTTPException(503, "Database, migrations or rate limiter not ready") from None
        return {
            "status": "ready",
            "database": "ok",
            "revision": revision,
            "redis": "ok" if settings.redis_url else "not_configured",
        }

    from fastapi import Depends

    @app.get("/metrics", dependencies=[Depends(admin)], include_in_schema=False)
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
