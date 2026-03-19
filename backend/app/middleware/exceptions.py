import logging
import traceback
from typing import Any, Dict
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for medical AI platform.
    
    Medical audit compliant error handling that prevents internal
    tracebacks from leaking to clients while maintaining proper logging.
    
    Args:
        request: FastAPI request object
        exc: Exception that was raised
        
    Returns:
        JSONResponse with safe error message
    """
    # Log the full error for audit purposes
    logger.error(
        f"Unhandled exception in {request.method} {request.url}: {exc}",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "user_id": getattr(request.state, "user_id", "anonymous"),
            "traceback": traceback.format_exc()
        }
    )
    
    # Return generic error to client for security
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with proper logging.
    
    Args:
        request: FastAPI request object
        exc: HTTPException that was raised
        
    Returns:
        JSONResponse with error details
    """
    # Log client errors for audit
    if exc.status_code >= 400:
        logger.warning(
            f"HTTP {exc.status_code} error for {request.method} {request.url}: {exc.detail}",
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "user_id": getattr(request.state, "user_id", "anonymous"),
                "status_code": exc.status_code
            }
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": f"HTTP_{exc.status_code}"
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors.
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError that was raised
        
    Returns:
        JSONResponse with validation error details
    """
    logger.warning(
        f"Validation error for {request.method} {request.url}: {exc.errors()}",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "user_id": getattr(request.state, "user_id", "anonymous"),
            "validation_errors": exc.errors()
        }
    )
    
    # Format validation errors for client
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "errors": errors
        }
    )


async def rate_limit_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle rate limit exceeded exceptions.
    
    Args:
        request: FastAPI request object
        exc: Rate limit exception
        
    Returns:
        JSONResponse with rate limit error
    """
    logger.warning(
        f"Rate limit exceeded for {request.method} {request.url}",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "user_id": getattr(request.state, "user_id", "anonymous"),
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded",
            "error_code": "RATE_LIMIT_EXCEEDED"
        }
    )


def create_error_response(status_code: int, detail: str, error_code: str = None) -> Dict[str, Any]:
    """Create standardized error response structure.
    
    Args:
        status_code: HTTP status code
        detail: Error message
        error_code: Internal error code
        
    Returns:
        Dictionary with error response structure
    """
    response = {
        "detail": detail,
        "error_code": error_code or f"HTTP_{status_code}"
    }
    
    if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        response["errors"] = []
    
    return response


# Exception handler mappings
exception_handlers = {
    Exception: global_exception_handler,
    HTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
    StarletteHTTPException: http_exception_handler,
}

__all__ = [
    "global_exception_handler",
    "http_exception_handler", 
    "validation_exception_handler",
    "rate_limit_exception_handler",
    "create_error_response",
    "exception_handlers"
]