from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, Counter, Histogram
import structlog
from .config.firebase import initialize_firebase
from .config.settings import settings
from .middleware import LoggingMiddleware, ErrorHandlingMiddleware, setup_cors_middleware
from .routers import (
    auth_router,
    users_router,
    freelancers_router,
    clients_router,
    companies_router,
    orders_router,
    order_applications_router,
    admin_router,
    help_router
)
from .schemas.common import APIResponse

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.LogfmtRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="Freelance Marketplace API",
    description="A production-ready backend for a freelance marketplace",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

setup_cors_middleware(app)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(freelancers_router)
app.include_router(clients_router)
app.include_router(companies_router)
app.include_router(orders_router)
app.include_router(order_applications_router)
app.include_router(admin_router)
app.include_router(help_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up")
    initialize_firebase()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")


@app.get("/health")
async def health_check():
    from .datastore.firestore import firestore_healthcheck
    firestore_status = await firestore_healthcheck()
    return APIResponse(success=True, data={
        "status": "healthy",
        "firestore": "connected" if firestore_status else "offline"
    })


@app.get("/metrics")
async def metrics():
    return generate_latest()


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content=APIResponse(
            success=False,
            error="Not found"
        ).model_dump()
    )


@app.exception_handler(422)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=APIResponse(
            success=False,
            error="Validation error",
            data=exc.detail
        ).model_dump()
    )
