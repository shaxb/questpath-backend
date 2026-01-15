"""
Middleware for request tracking, monitoring, and observability.
"""
import time
import uuid
from fastapi import Request
from app.logger import logger
from app.metrics import metrics


async def add_request_tracking(request: Request, call_next):
    """
    Add request ID and track request duration.
    
    - Generates unique request ID for tracing
    - Logs request start/end
    - Tracks slow requests
    - Adds request ID to response headers
    """
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Track request in metrics
    metrics.increment_request(request.url.path, request.method)
    
    # Log request start
    logger.info(
        "request_started",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown"
    )
    
    # Process request and track duration
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Record metrics
        metrics.record_response_time(request.url.path, duration_ms)
        if response.status_code >= 400:
            metrics.increment_error(request.url.path, response.status_code)
        
        # Log request completion
        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        # Warn about slow requests (> 1 second)
        if duration_ms > 1000:
            logger.warning(
                "slow_request_detected",
                request_id=request_id,
                path=request.url.path,
                duration_ms=duration_ms,
                threshold_ms=1000
            )
        
        # Add request ID to response headers for debugging
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log request failure
        logger.error(
            "request_failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            duration_ms=duration_ms,
            error=str(e),
            error_type=type(e).__name__
        )
        
        # Re-raise so FastAPI can handle it
        raise


async def add_security_headers(request: Request, call_next):
    """
    Add security headers to all responses.
    
    Protects against:
    - XSS attacks
    - Clickjacking
    - MIME sniffing
    - Forces HTTPS in production
    """
    response = await call_next(request)
    
    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # XSS protection (legacy but still good)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Force HTTPS for 1 year (only in production)
    from app.config import settings
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response
