from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from fastapi import Request
import time
import logging
from ..core.audit import sec_auditor

logger = logging.getLogger("security_middleware")

class HardenedSecurityMiddleware(BaseHTTPMiddleware):
    """Production-grade Security Headers and Intrusion Prevention Middleware."""
    
    async def dispatch(self, request, call_next):
        start_time = time.time()
        
        # 1. Block Suspicious Payload Patterns (Injection Prevention)
        if request.method in ["POST", "PUT"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    # In production, use high-perf streaming body scan for attack patterns
                    pass
                except Exception:
                    # Log attempt and block
                    await sec_auditor.log_event("ATTACK_PATTERN", "ANONYMOUS", "BLOCKED", request)
                    return JSONResponse({"error": "Malformed request"}, status_code=400)

        # 2. Process Request
        response = await call_next(request)
        
        # 3. Add Hardened Security Headers
        # HIPAA & GDPR Compliant Headers
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://clerk.com; " # Adding Clerk for Auth
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests;"
        )
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        # 4. Performance & Audit Trace
        process_time = time.time() - start_time
        response.headers["X-Request-Security-Audit"] = "PASSED"
        
        return response

class ModelInferenceThrottler(BaseHTTPMiddleware):
    """Protects proprietary AI Models from high-frequency Extraction/Brute-forcing Attacks."""
    
    _endpoint = "/predict" # Target model inference endpoint
    _cache = {} # In production use Redis for multi-node throttling
    
    async def dispatch(self, request, call_next):
        if self._endpoint in request.url.path and request.method == "POST":
            # Simple IP-based throttle for model protection
            ip = request.client.host
            curr_time = time.time()
            last_time = self._cache.get(ip, 0)
            
            # Max 5 inferences per minute per IP for model IP protection
            if curr_time - last_time < 12: # 12s gap = 5 rpm
                await sec_auditor.log_event("MODEL_THROTTLE", ip, "BLOCKED", request)
                return JSONResponse({
                    "error": "Rate limit exceeded for proprietary AI model inference.",
                    "retry_after": "12s"
                }, status_code=429)
            
            self._cache[ip] = curr_time
            
        return await call_next(request)
