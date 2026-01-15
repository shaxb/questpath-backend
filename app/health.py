"""
Health check endpoint for monitoring application status.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.db import get_db
from app.cache import redis_client
from app.logger import logger
from app.metrics import metrics
import sys

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: Annotated[AsyncSession, Depends(get_db)]):
    """
    Health check endpoint - returns status of all critical services.
    
    Use this for:
    - Load balancer health checks
    - Monitoring alerts
    - Deployment validation
    
    Returns 200 if all services healthy, 503 if any service is down.
    """
    health_status = {
        "status": "healthy",
        "checks": {},
        "version": "1.0.0",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }
    
    errors = []
    
    # 1. Check Database
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health_status["checks"]["database"] = "connected"
    except Exception as e:
        health_status["checks"]["database"] = "disconnected"
        errors.append(f"Database: {str(e)}")
        logger.error("health_check_database_failed", error=str(e))
    
    # 2. Check Redis
    try:
        redis_client.ping()
        health_status["checks"]["redis"] = "connected"
    except Exception as e:
        health_status["checks"]["redis"] = "disconnected"
        errors.append(f"Redis: {str(e)}")
        logger.error("health_check_redis_failed", error=str(e))
    
    # If any service is down, return 503
    if errors:
        health_status["status"] = "unhealthy"
        health_status["errors"] = errors
        
        logger.warning("health_check_failed", 
                      status="unhealthy", 
                      errors=errors)
        
        raise HTTPException(
            status_code=503,
            detail={
                "status": "Service Unavailable",
                "health": health_status
            }
        )
    
    return health_status


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check - is the application ready to receive traffic?
    
    Use this for Kubernetes readiness probes.
    Returns immediately without checking external services.
    """
    return {
        "status": "ready",
        "message": "Application is ready to receive traffic"
    }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check - is the application process alive?
    
    Use this for Kubernetes liveness probes.
    Returns immediately to confirm the process is responsive.
    """
    return {
        "status": "alive",
        "message": "Application process is alive"
    }


@router.get("/metrics")
async def get_metrics():
    """
    Application metrics endpoint.
    
    Returns current metrics for monitoring:
    - Request counts by endpoint
    - Error counts
    - Response times
    - Active requests
    
    Use this for:
    - Prometheus scraping
    - Grafana dashboards
    - Performance monitoring
    """
    return metrics.get_stats()
