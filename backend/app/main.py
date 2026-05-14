import logging
from contextlib import asynccontextmanager

from app.database import get_engine
from app.api.v1 import router as v1_router
from app.auth.middleware import AuthMiddleware
from app.config import settings
from app.middleware.audit import AuditMiddleware
from app.middleware.compression import GzipMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.metrics import PrometheusMiddleware
from app.middleware.security import RateLimitMiddleware, WebhookAuthMiddleware
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---- Sentry Integration ----
def setup_sentry():
    """Initialize Sentry error tracking if configured."""
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.celery import CeleryIntegration
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                integrations=[
                    FastApiIntegration(),
                    CeleryIntegration(),
                    SqlalchemyIntegration(),
                ],
                traces_sample_rate=getattr(settings, "SENTRY_TRACES_SAMPLE_RATE", 1.0),
                environment=getattr(settings, "ENVIRONMENT", "production"),
            )
            logger.info("Sentry initialized")
        except ImportError:
            logger.warning("sentry-sdk not installed — skipping Sentry integration")


setup_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle hook."""
    logger.info("Starting up AutoBiz Engine API...")
    try:

        engine = get_engine()
        if "sqlite" in str(engine.url):
            from app.models.base import Base

            Base.metadata.create_all(bind=engine)
            logger.info("SQLite tables created automatically")
    except Exception as e:
        logger.warning(f"Auto table creation skipped: {e}")
    yield
    logger.info("Shutting down AutoBiz Engine API...")


app = FastAPI(
    title="AutoBiz Engine API",
    description="API for autonomous business building and operation",
    version="1.0.0",
    lifespan=lifespan,
)

# ---- Middleware (order matters) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(GzipMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(AuditMiddleware)

app.add_middleware(RateLimitMiddleware)

app.add_middleware(WebhookAuthMiddleware)

# ---- Prometheus metrics endpoint ----
_prometheus = PrometheusMiddleware(app)


@app.get("/metrics")
async def metrics_endpoint():
    """Expose Prometheus metrics."""
    return PlainTextResponse(
        _prometheus.get_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.get("/metrics/stats")
async def metrics_stats():
    """Get human-readable metrics stats."""
    return _prometheus.get_stats()


# ---- Routers ----
app.include_router(v1_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "AutoBiz Engine API is running"}


@app.get("/health")
async def health_check():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "healthy", "database": "disconnected", "detail": str(e)}


@app.get("/health/ready")
async def readiness_check():
    return {"status": "ready"}


@app.get("/health/live")
async def liveness_check():
    return {"status": "alive"}


@app.exception_handler(400)
async def bad_request_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=400,
        content={"error": "Bad Request", "detail": str(exc)},
    )


@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=401,
        content={"error": "Unauthorized", "detail": str(exc)},
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=403,
        content={"error": "Forbidden", "detail": str(exc)},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "detail": str(exc)},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred"},
    )
