from fastapi import APIRouter, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
import stripe
import logging
import os
from typing import Optional
from ..config import settings
from ..core.audit import sec_auditor
from ..db import db

logger = logging.getLogger("payments_security")
router = APIRouter()

# Initialize Stripe with Secret Key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock_key")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock_secret")

class PaymentManager:
    """Secure Payment Orchestration & Anti-Tampering Manager."""
    
    @staticmethod
    async def process_successful_payment(session: dict):
        """Handle successful checkout after signature verification."""
        customer_email = session.get("customer_details", {}).get("email")
        amount = session.get("amount_total", 0) / 100 # Convert from cents
        
        # Verify idempotency by checking if transaction was already processed
        tx_id = session.get("id")
        existing = await db.db["transactions"].find_one({"stripe_id": tx_id})
        if existing:
            return # Prevent duplicate billing logic
            
        # Store secure transaction record
        await db.db["transactions"].insert_one({
            "stripe_id": tx_id,
            "email": customer_email,
            "amount": amount,
            "status": "COMPLETED",
            "timestamp": stripe.util.convert_to_datetime(session.get("created", 0))
        })
        
        await sec_auditor.log_event("PAYMENT_SUCCESS", customer_email, "SUCCESS", details={"amount": amount})

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request, 
    stripe_signature: Optional[str] = Header(None)
):
    """Hardened Stripe Webhook with Signature Verification."""
    
    if not stripe_signature:
        await sec_auditor.log_event("PAYMENT_TAMPER", "ANONYMOUS", "BLOCKED", request, {"error": "Missing signature"})
        raise HTTPException(status_code=400, detail="Missing Stripe Signature")

    payload = await request.body()
    
    try:
        # 1. AUTHENTICITY: Strict cryptographic signature verification
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return JSONResponse({"error": "Invalid payload"}, status_code=400)
    except stripe.error.SignatureVerificationError as e:
        # 2. ANTI-TAMPER: Log suspicious webhook forgery attempt
        await sec_auditor.log_event("WEBHOOK_FORGERY_DETECTED", "ANONYMOUS", "BLOCKED", request)
        return JSONResponse({"error": "Invalid signature"}, status_code=400)

    # 3. EVENT PROCESSING: Handle only validated Stripe events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await PaymentManager.process_successful_payment(session)
    elif event['type'] == 'invoice.payment_failed':
        session = event['data']['object']
        await sec_auditor.log_event("PAYMENT_FAILED", session.get("customer_email"), "FAILED")
        # Notify user etc.
        
    return JSONResponse({"status": "received"})
