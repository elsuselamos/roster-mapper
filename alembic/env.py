"""
Alembic Environment Configuration
==================================
Modified to use Cloud SQL Python Connector when INSTANCE_CONNECTION_NAME is set.

For local development: uses DATABASE_URL from settings.
For production (Cloud Run): uses Cloud SQL Connector from app.db.connector.
"""

from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import models to ensure Base.metadata is populated
from app.db.models import Base
from app.core.config import settings

# Import connector for Cloud SQL
try:
    from app.db.connector import engine as cloud_sql_engine
    USE_CLOUD_SQL = bool(os.getenv("INSTANCE_CONNECTION_NAME"))
except ImportError:
    cloud_sql_engine = None
    USE_CLOUD_SQL = False

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_engine():
    """
    Get database engine for migrations.
    
    Uses Cloud SQL Connector if INSTANCE_CONNECTION_NAME is set,
    otherwise uses standard DATABASE_URL.
    """
    if USE_CLOUD_SQL and cloud_sql_engine:
        # Use Cloud SQL connector engine
        return cloud_sql_engine
    else:
        # Use standard engine from DATABASE_URL
        # Convert asyncpg URL to sync for Alembic
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        elif not db_url.startswith("postgresql"):
            # Default to postgresql
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        
        configuration = config.get_section(config.config_ini_section)
        configuration["sqlalchemy.url"] = db_url
        
        return engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,  # Don't pool connections for migrations
        )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = settings.DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

