"""
Roster Mapper - FastAPI Application
===================================
Main entry point for the Roster Mapper API.

Author: datnguyentien@vietjetair.com
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.v1 import upload, admin, batch, dashboard

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "Starting Roster Mapper",
        extra={
            "app_name": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "version": "1.0.0"
        }
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down Roster Mapper")


# Create FastAPI application
app = FastAPI(
    title="Roster Mapper API",
    description="Vietjet Maintenance Department - Excel Roster Code Mapping Service",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
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
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health check endpoint.
    Returns service status for load balancers and monitoring.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0"
    }


# API info endpoint (moved to /api for UI at root)
@app.get("/api", tags=["Root"])
async def api_info() -> dict:
    """API information endpoint."""
    return {
        "service": "Roster Mapper API",
        "description": "Vietjet Maintenance Department - Excel Roster Code Mapping",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "Disabled in production"
    }


# Include UI router FIRST (serves at root)
from app.ui.routes import router as ui_router
app.include_router(ui_router, tags=["UI"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(
    upload.router,
    prefix="/api/v1",
    tags=["Upload"]
)

app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    tags=["Admin"]
)

app.include_router(
    batch.router,
    prefix="/api/v1",
    tags=["Batch"]
)

app.include_router(
    dashboard.router,
    prefix="/api/v1/dashboard",
    tags=["Dashboard"]
)

# UI router already included above (before static files)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

