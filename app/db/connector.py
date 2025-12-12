"""
Cloud SQL Python Connector
==========================
Database connection using Google Cloud SQL Python Connector for Cloud Run.

This module provides SQLAlchemy engine and session factory that connects
to Cloud SQL (Postgres) using the Cloud SQL Python Connector.

For local development, use DATABASE_URL with asyncpg.
For production (Cloud Run), use Cloud SQL Connector with pg8000.

Author: datnguyentien@vietjetair.com
"""

import os
from typing import Optional

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Cloud SQL connection settings
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")  # project:region:instance
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "roster")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "3"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))

# Determine if we should use Cloud SQL Connector
USE_CLOUD_SQL_CONNECTOR = bool(INSTANCE_CONNECTION_NAME and settings.is_cloud_run)

engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None
_connector = None


def _create_cloud_sql_engine() -> Engine:
    """
    Create SQLAlchemy engine using Cloud SQL Python Connector.
    
    Requires:
    - INSTANCE_CONNECTION_NAME env var
    - DB_USER, DB_PASS, DB_NAME env vars
    - google-cloud-sql-connector[pg8000] package installed
    
    Returns:
        SQLAlchemy engine configured for Cloud SQL
    """
    try:
        from google.cloud.sql.connector import Connector, IPTypes
        import pg8000
    except ImportError:
        raise ImportError(
            "Cloud SQL Connector not installed. "
            "Install with: pip install google-cloud-sql-connector[pg8000] pg8000"
        )
    
    global _connector
    _connector = Connector()
    
    def getconn():
        """Get connection using Cloud SQL Connector."""
        conn = _connector.connect(
            INSTANCE_CONNECTION_NAME,
            "pg8000",
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
            ip_type=IPTypes.PRIVATE  # Use private IP (recommended for Cloud Run)
        )
        return conn
    
    # Create engine with connection creator
    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        poolclass=QueuePool,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_timeout=30,
        pool_pre_ping=True,  # Verify connections before using
        echo=settings.DB_ECHO,
    )
    
    logger.info(
        "Cloud SQL engine created",
        extra={
            "instance": INSTANCE_CONNECTION_NAME,
            "database": DB_NAME,
            "pool_size": DB_POOL_SIZE,
            "max_overflow": DB_MAX_OVERFLOW
        }
    )
    
    return engine


def _create_standard_engine() -> Engine:
    """
    Create standard SQLAlchemy engine using DATABASE_URL.
    
    For local development or when not using Cloud SQL Connector.
    Uses asyncpg for async operations (if DATABASE_URL has asyncpg driver).
    For sync operations (Alembic), converts to sync URL.
    """
    db_url = settings.DATABASE_URL
    
    # Convert asyncpg URL to psycopg2/pg8000 for sync operations
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    elif db_url.startswith("postgresql://"):
        pass  # Already sync
    else:
        # Default to postgresql://
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        echo=settings.DB_ECHO,
    )
    
    logger.info(
        "Standard database engine created",
        extra={
            "database_url": db_url.split("@")[-1] if "@" in db_url else "local",
            "pool_size": DB_POOL_SIZE
        }
    )
    
    return engine


def get_engine() -> Engine:
    """
    Get or create database engine.
    
    Returns:
        SQLAlchemy engine (sync)
    """
    global engine
    
    if engine is None:
        if USE_CLOUD_SQL_CONNECTOR:
            engine = _create_cloud_sql_engine()
        else:
            engine = _create_standard_engine()
    
    return engine


def get_session() -> sessionmaker:
    """
    Get or create session factory.
    
    Returns:
        SQLAlchemy sessionmaker
    """
    global SessionLocal
    
    if SessionLocal is None:
        engine = get_engine()
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            expire_on_commit=False
        )
    
    return SessionLocal


def close_connector():
    """Close Cloud SQL connector (call on shutdown)."""
    global _connector
    if _connector:
        try:
            _connector.close()
            logger.info("Cloud SQL connector closed")
        except Exception as e:
            logger.warning(f"Error closing connector: {e}")


# Initialize engine and session on module import
try:
    engine = get_engine()
    SessionLocal = get_session()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}", exc_info=True)
    # Don't raise - allow app to start and fail on first DB access
    engine = None
    SessionLocal = None


# Export for use in Alembic and application code
__all__ = ["engine", "SessionLocal", "get_engine", "get_session", "close_connector"]

