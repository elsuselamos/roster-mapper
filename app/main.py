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
from app.api.v1 import upload, admin, batch, dashboard, no_db_files
import asyncio

# Setup logging
setup_logging()
logger = get_logger(__name__)


# Removed periodic_cleanup() - using No-DB cleanup task from no_db_files.py instead
# The old database-backed cleanup is no longer needed in v1.2.0+ (No-DB architecture)


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
    
    # Start no-DB cleanup task (v1.2.0+ - No-DB architecture)
    try:
        from app.api.v1 import no_db_files
        no_db_files.start_cleanup_task()
        logger.info("Started no-DB cleanup task")
    except Exception as e:
        logger.warning(f"Failed to start no-DB cleanup task: {e}")
    
    yield
    
    # Shutdown
    # No-DB cleanup task is handled by no_db_files module
    # No need to cancel here as it's managed internally
    
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
    version="1.3.0",
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

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging."""
    # Always log requests to /api/v1/pdf/*
    if request.url.path.startswith("/api/v1/pdf"):
        logger.info(
            "PDF API request",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params)
        )
    response = await call_next(request)
    # Always log PDF API responses
    if request.url.path.startswith("/api/v1/pdf"):
        logger.info(
            "PDF API response",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code
        )
        # Log 404 errors with route details
        if response.status_code == 404:
            all_pdf_routes = [r.path for r in app.routes if hasattr(r, 'path') and 'pdf' in r.path.lower()]
            logger.error(
                "PDF API 404 Not Found",
                method=request.method,
                path=request.url.path,
                registered_routes=all_pdf_routes
            )
    return response


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 404 Not Found errors with detailed logging."""
    logger.warning(
        "404 Not Found",
        path=request.url.path,
        method=request.method,
        all_pdf_routes=[r.path for r in app.routes if hasattr(r, 'path') and 'pdf' in r.path.lower()]
    )
    return JSONResponse(
        status_code=404,
        content={"detail": f"Not Found: {request.url.path}"}
    )

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
    
    # No-DB architecture: no database check needed
    # Overall status based on storage only
    overall_ok = storage_ok
    
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
        "architecture": "no-db",
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
logger.info("Registering API routers...")

app.include_router(
    upload.router,
    prefix="/api/v1",
    tags=["Upload"]
)
logger.debug("Upload router registered")

app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    tags=["Admin"]
)
logger.debug("Admin router registered")

app.include_router(
    batch.router,
    prefix="/api/v1",
    tags=["Batch"]
)
logger.debug("Batch router registered")

app.include_router(
    dashboard.router,
    prefix="/api/v1/dashboard",
    tags=["Dashboard"]
)
logger.debug("Dashboard router registered")

app.include_router(
    no_db_files.router,
    tags=["No-DB Files"]
)
logger.debug("No-DB Files router registered")

# Import and register PDF router
try:
    logger.info("Importing PDF router module...")
    from app.api.v1 import pdf_files
    logger.info("PDF router module imported successfully")
    
    logger.info("Registering PDF router...", prefix=pdf_files.router.prefix)
    app.include_router(
        pdf_files.router,
        tags=["PDF"]
    )
    
    # Log all registered routes from PDF router
    pdf_routes = []
    for r in pdf_files.router.routes:
        if hasattr(r, 'path') and hasattr(r, 'methods'):
            pdf_routes.append({
                "path": r.path,
                "methods": list(r.methods) if r.methods else []
            })
    logger.info("PDF router registered successfully", routes=pdf_routes, count=len(pdf_routes))
    
    # Also log all app routes for verification
    all_app_routes = []
    for r in app.routes:
        if hasattr(r, 'path') and 'pdf' in r.path.lower():
            all_app_routes.append(r.path)
    logger.info("All PDF routes in app", routes=all_app_routes)
    
except ImportError as e:
    logger.error(f"Failed to import PDF router module: {e}", exc_info=True)
    raise
except Exception as e:
    logger.error(f"Failed to register PDF router: {e}", exc_info=True)
    raise

# UI router already included above (before static files)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

