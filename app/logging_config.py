"""
Centralized logging configuration for all application components.
Controls SQLAlchemy, Uvicorn, and application logs.
"""
import logging
from app.config import settings


def configure_external_loggers():
    """
    Configure logging for external libraries (SQLAlchemy, Uvicorn, etc.)
    Call this once at application startup.
    """
    
    # 1. SQLAlchemy - Database query logging
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    if settings.log_sql_queries:
        sqlalchemy_logger.setLevel(logging.INFO)
    else:
        # Only show warnings and errors
        sqlalchemy_logger.setLevel(logging.WARNING)
    
    # 2. Uvicorn access logs - HTTP request logging
    uvicorn_access = logging.getLogger('uvicorn.access')
    if settings.log_http_requests:
        uvicorn_access.setLevel(logging.INFO)
    else:
        # Suppress HTTP request logs
        uvicorn_access.setLevel(logging.WARNING)
    
    # 3. Uvicorn general logs (startup, shutdown, errors)
    uvicorn_logger = logging.getLogger('uvicorn')
    if settings.debug:
        uvicorn_logger.setLevel(logging.INFO)
    else:
        uvicorn_logger.setLevel(logging.WARNING)
    
    # 4. FastAPI internal logs
    fastapi_logger = logging.getLogger('fastapi')
    fastapi_logger.setLevel(logging.WARNING)  # Only errors
    
    # 5. WatchFiles (development auto-reload)
    watchfiles_logger = logging.getLogger('watchfiles')
    if settings.debug:
        watchfiles_logger.setLevel(logging.INFO)  # Show file changes
    else:
        watchfiles_logger.setLevel(logging.ERROR)  # Production: silent


def get_log_level_recommendations():
    """
    Returns recommended log levels based on environment.
    """
    if settings.environment == "production":
        return {
            "sqlalchemy": logging.WARNING,     # Only errors
            "uvicorn.access": logging.WARNING,  # Disable HTTP logs (use nginx/ALB instead)
            "uvicorn": logging.INFO,            # Startup/shutdown events
            "application": logging.INFO,        # Your custom logs
        }
    elif settings.environment == "staging":
        return {
            "sqlalchemy": logging.WARNING,
            "uvicorn.access": logging.INFO,     # Keep HTTP logs for debugging
            "uvicorn": logging.INFO,
            "application": logging.DEBUG,       # Verbose app logs
        }
    else:  # development
        return {
            "sqlalchemy": logging.INFO if settings.log_sql_queries else logging.WARNING,
            "uvicorn.access": logging.INFO,
            "uvicorn": logging.INFO,
            "application": logging.DEBUG,
        }


# Production-ready configuration
def setup_production_logging():
    """
    Minimal logging for production - only errors and critical events.
    HTTP requests logged by load balancer/nginx, not application.
    """
    logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
    logging.getLogger('uvicorn.access').setLevel(logging.ERROR)  # Disable
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('watchfiles').setLevel(logging.ERROR)
