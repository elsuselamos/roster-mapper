"""
Logging Module
==============
Structured JSON logging setup for the application.

Author: datnguyentien@vietjetair.com
"""

import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    
    Uses structlog for structured JSON logging in production,
    and colored console output in development.
    """
    # Determine if we should use JSON formatting
    use_json = settings.is_production
    
    # Common processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    if use_json:
        # Production: JSON formatting
        shared_processors.extend([
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ])
    else:
        # Development: Colored console output
        shared_processors.append(
            structlog.dev.ConsoleRenderer(colors=True)
        )
    
    # Configure structlog
    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DB_ECHO else logging.WARNING
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name, typically __name__ of the calling module.
        
    Returns:
        A bound structlog logger instance.
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing file", filename="roster.xlsx", station="SGN")
    """
    return structlog.get_logger(name)


class LoggerAdapter:
    """
    Adapter class for logging with additional context.
    
    Provides a convenient way to add persistent context to all log messages.
    """
    
    def __init__(self, logger: structlog.BoundLogger, context: Optional[Dict[str, Any]] = None):
        """
        Initialize the logger adapter.
        
        Args:
            logger: The underlying structlog logger.
            context: Optional persistent context to add to all messages.
        """
        self._logger = logger
        self._context = context or {}
    
    def bind(self, **kwargs: Any) -> "LoggerAdapter":
        """
        Create a new adapter with additional context.
        
        Args:
            **kwargs: Additional context key-value pairs.
            
        Returns:
            A new LoggerAdapter with merged context.
        """
        new_context = {**self._context, **kwargs}
        return LoggerAdapter(self._logger, new_context)
    
    def _log(self, level: str, message: str, **kwargs: Any) -> None:
        """Internal method to log with merged context."""
        merged = {**self._context, **kwargs}
        getattr(self._logger, level)(message, **merged)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log("debug", message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log("error", message, **kwargs)
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self._log("exception", message, **kwargs)

