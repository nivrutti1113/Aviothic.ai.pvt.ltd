import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Production-ready request logging middleware for medical AI platform.
    
    Medical audit compliant structured logging with request tracing,
    performance monitoring, and security audit capabilities.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with structured logging.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response object
        """
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract user information if available
        user_id = "anonymous"
        user_role = "none"
        
        # Try to get user from auth header (without validating)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Store token for potential audit
            request.state.auth_token = auth_header[7:]
        
        start_time = time.time()
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", "unknown"),
                "user_id": user_id,
                "user_role": user_role,
                "timestamp": start_time
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log successful response
            logger.info(
                f"Request completed: {request.method} {request.url} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2),
                    "client_ip": self._get_client_ip(request),
                    "user_id": user_id,
                    "user_role": user_role,
                    "response_size": response.headers.get("content-length", "unknown")
                }
            )
            
            # Add request ID to response headers for client tracing
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url} - {type(e).__name__}: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "process_time_ms": round(process_time * 1000, 2),
                    "client_ip": self._get_client_ip(request),
                    "user_id": user_id,
                    "user_role": user_role
                }
            )
            
            # Re-raise to let exception handlers process it
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client IP address string
        """
        # Check for X-Forwarded-For header (when behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP from comma-separated list
            return forwarded_for.split(",")[0].strip()
        
        # Check for X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        if request.client:
            return request.client.host
        
        return "unknown"


class ModelAuditMiddleware(BaseHTTPMiddleware):
    """Middleware for auditing model usage and predictions.
    
    Medical audit compliant tracking of model inference activities.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with model usage auditing.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response object
        """
        # Only audit prediction endpoints
        if request.url.path.endswith("/predict") and request.method == "POST":
            # Store model version for audit
            request.state.model_version = getattr(request.app.state, 'model_version', 'unknown')
            
            # Log prediction request
            logger.info(
                "Model prediction request received",
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "model_version": request.state.model_version,
                    "endpoint": str(request.url),
                    "method": request.method
                }
            )
        
        response = await call_next(request)
        
        # Log prediction completion
        if request.url.path.endswith("/predict") and request.method == "POST":
            logger.info(
                "Model prediction completed",
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "model_version": getattr(request.state, "model_version", "unknown"),
                    "status_code": response.status_code
                }
            )
        
        return response


# Export middleware classes
__all__ = ["RequestLoggingMiddleware", "ModelAuditMiddleware"]