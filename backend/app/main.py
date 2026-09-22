import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import AppException
from app.routers import (
    auth,
    dashboard,
    collection,
    upload,
    recon,
    exceptions,
    sla,
    refunds,
    citizen,
    devolution,
    accounting,
    reports,
    masters,
    audit,
    config,
    testsuite,
    notifications,
    help as help_router,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ifms_revenue")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} backend service...")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME} backend service...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_type": exc.__class__.__name__},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred.", "error": str(exc)},
    )

# Include all routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(collection.router)
app.include_router(upload.router)
app.include_router(recon.router)
app.include_router(exceptions.router)
app.include_router(sla.router)
app.include_router(refunds.router)
app.include_router(citizen.router)
app.include_router(devolution.router)
app.include_router(accounting.router)
app.include_router(reports.router)
app.include_router(masters.router)
app.include_router(audit.router)
app.include_router(config.router)
app.include_router(testsuite.router)
app.include_router(notifications.router)
app.include_router(help_router.router)

@app.get("/health", tags=["System Health"])
async def health_check():
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "database": "PostgreSQL (ifms_budget)",
        "schema": "ifms_budget",
        "version": "1.0.0"
    }
