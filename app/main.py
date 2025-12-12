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
from app.api.v1 import upload, admin, batch, dashboard, files, no_db_files
import asyncio

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def periodic_cleanup():
    """
    Background task to periodically clean up expired files.
    Runs every 10 minutes.
    """
    from app.api.v1.files import cleanup_expired_files
    
    CLEANUP_INTERVAL_SECONDS = 10 * 60  # 10 minutes
    
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            await cleanup_expired_files()
        except Exception as e:
            logger.error(f"Cleanup task error: {e}", exc_info=True)
            # Continue running even if cleanup fails
            await asyncio.sleep(60)  # Wait 1 minute before retry


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
            "version": settings.APP_VERSION,
            "storage_type": settings.STORAGE_TYPE,
            "storage_dir": str(settings.STORAGE_DIR),
            "output_dir": str(settings.OUTPUT_DIR),
            "port": settings.PORT,
            "cloud_run": settings.is_cloud_run
        }
    )
    
    # Ensure directories exist
    settings.ensure_directories()
    
    # Start cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    logger.info("Started periodic cleanup task")
    
    # Start no-DB cleanup task if using no-DB endpoints
    try:
        from app.api.v1 import no_db_files
        no_db_files.start_cleanup_task()
        logger.info("Started no-DB cleanup task")
    except Exception as e:
        logger.warning(f"Failed to start no-DB cleanup task: {e}")
    
    yield
    
    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    # Close Cloud SQL connector if used
    try:
        from app.db.connector import close_connector
        close_connector()
    except Exception as e:
        logger.warning(f"Error closing database connector: {e}")
    
    logger.info("Shutting down Roster Mapper")


# Create FastAPI application
# Note: docs_url and redoc_url are always enabled (no auth required per spec)
app = FastAPI(
    title="Roster Mapper API",
    description="Vietjet Maintenance Department - Excel Roster Code Mapping Service",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
    Includes storage write permission check and database connectivity.
    """
    import os
    from pathlib import Path
    
    # Check storage write permission
    storage_ok = False
    try:
        test_path = settings.STORAGE_DIR / ".health_check"
        test_path.write_text("ok")
        test_path.unlink()
        storage_ok = True
    except Exception:
        storage_ok = False
    
    # Check database connectivity
    db_ok = False
    db_error = None
    try:
        from app.db.connector import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_ok = True
    except Exception as e:
        db_error = str(e)
        logger.warning(f"Database health check failed: {e}")
    
    # Overall status
    overall_ok = storage_ok and db_ok
    
    return {
        "status": "ok" if overall_ok else "degraded",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "storage": {
            "type": settings.STORAGE_TYPE,
            "writable": storage_ok,
            "storage_dir": str(settings.STORAGE_DIR),
            "output_dir": str(settings.OUTPUT_DIR)
        },
        "database": {
            "connected": db_ok,
            "error": db_error if not db_ok else None
        },
        "cloud_run": settings.is_cloud_run
    }


# API info endpoint (moved to /api for UI at root)
@app.get("/api", tags=["Root"])
async def api_info() -> dict:
    """API information endpoint."""
    return {
        "service": "Roster Mapper API",
        "description": "Vietjet Maintenance Department - Excel Roster Code Mapping",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
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

app.include_router(
    files.router,
    prefix="/api/v1/files",
    tags=["Files"]
)

app.include_router(
    no_db_files.router,
    tags=["No-DB Files"]
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

