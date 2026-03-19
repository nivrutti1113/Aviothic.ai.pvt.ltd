import logging
import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ..config import settings

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW}seconds"]
)


class RateLimitMiddleware:
    """Production-ready rate limiting middleware for medical AI platform.
    
    Medical audit compliant rate limiting to prevent abuse and ensure service availability.
    """
    
    def __init__(self):
        self.request_counts: Dict[str, Dict] = {}
        self.limit = settings.RATE_LIMIT_REQUESTS
        self.window = settings.RATE_LIMIT_WINDOW
    
    def _get_client_key(self, request: Request) -> str:
        """Get unique client identifier for rate limiting.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client identifier string
        """
        # Use IP address as client identifier
        client_ip = request.client.host if request.client else "unknown"
        
        # If behind proxy, check for X-Forwarded-For header
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
            
        return client_ip
    
    def _cleanup_old_records(self):
        """Clean up old rate limit records to prevent memory leaks."""
        current_time = time.time()
        expired_keys = []
        
        for client_key, record in self.request_counts.items():
            if current_time - record["timestamp"] > self.window:
                expired_keys.append(client_key)
        
        for key in expired_keys:
            del self.request_counts[key]
    
    async def check_rate_limit(self, request: Request) -> Optional[HTTPException]:
        """Check if request exceeds rate limit.
        
        Args:
            request: FastAPI request object
            
        Returns:
            HTTPException if rate limit exceeded, None otherwise
        """
        client_key = self._get_client_key(request)
        current_time = time.time()
        
        # Clean up old records periodically
        if len(self.request_counts) > 1000:  # Prevent memory issues
            self._cleanup_old_records()
        
        # Get or create client record
        if client_key not in self.request_counts:
            self.request_counts[client_key] = {
                "count": 1,
                "timestamp": current_time
            }
            return None
        
        record = self.request_counts[client_key]
        
        # Check if window has expired
        if current_time - record["timestamp"] > self.window:
            # Reset counter for new window
            record["count"] = 1
            record["timestamp"] = current_time
            return None
        
        # Check rate limit
        if record["count"] >= self.limit:
            logger.warning(f"Rate limit exceeded for client: {client_key}")
            return HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.limit} requests per {self.window} seconds."
            )
        
        # Increment counter
        record["count"] += 1
        return None


# Global rate limit middleware instance
rate_limit_middleware = RateLimitMiddleware()

__all__ = ["limiter", "rate_limit_middleware", "RateLimitExceeded"]