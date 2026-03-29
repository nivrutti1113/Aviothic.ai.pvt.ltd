import datetime
import logging
import uuid
from typing import Optional, Dict, Any
from fastapi import Request
from ..db import db

logger = logging.getLogger("security_audit")

class SecurityAuditor:
    """Medical Compliance Audit Logging System (HIPAA & GDPR Compliant)."""
    
    @staticmethod
    async def log_event(
        event_type: str, 
        user_id: Optional[str], 
        status: str, 
        request: Request = None,
        details: Dict[str, Any] = None
    ):
        """Record critical security events into immutable MongoDB collection."""
        
        # Determine client metadata
        ip_addr = request.client.host if request else "unknown"
        user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
        method = request.method if request else "system"
        url = str(request.url) if request else "internal"

        audit_record = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.utcnow(),
            "event_type": event_type, # e.g. "AUTH_LOGIN", "PII_ACCESS", "MODEL_INFERENCE"
            "user_id": user_id or "ANONYMOUS",
            "status": status, # "SUCCESS", "FAILED", "BLOCKED"
            "metadata": {
                "ip_address": ip_addr,
                "user_agent": user_agent,
                "request_method": method,
                "request_url": url,
                "details": details or {}
            }
        }
        
        # Use high priority audit logging to MongoDB
        try:
            # Note: Auditor uses a dedicated MongoDB collection 'security_audit_logs'
            await db.db["security_audit_logs"].insert_one(audit_record)
            
            # Additional localized logging for ELK/Standard logging stack
            logger.info(f"AUDIT {event_type} | User: {user_id} | Status: {status} | IP: {ip_addr}")
        except Exception as e:
            logger.critical(f"AUDIT_FAILURE: Failed to record security event: {e}")

# Singleton Instance
sec_auditor = SecurityAuditor()
