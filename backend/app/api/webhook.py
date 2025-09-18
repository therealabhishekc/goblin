"""
WhatsApp webhook endpoints.
Handles WhatsApp webhook verification and message processing.
"""
from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session
import json
import os

from app.core.database import get_database_session
from app.core.logging import logger
from app.core.exceptions import WebhookException, DuplicateMessageException
from app.services.whatsapp_service import WhatsAppService
from app.models.whatsapp import WhatsAppWebhookPayload
from app.config import get_settings

router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])

@router.get("/", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    WhatsApp webhook verification endpoint.
    Called by WhatsApp to verify the webhook URL.
    """
    settings = get_settings()
    logger.info(f"Webhook verification attempt: mode={hub_mode}, token_provided={bool(hub_verify_token)}")
    
    if hub_mode == "subscribe" and hub_verify_token == settings.verify_token:
        logger.info("✅ Webhook verification successful")
        return hub_challenge or ""
    
    logger.warning("❌ Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/")
async def process_webhook(
    request: Request,
    db: Session = Depends(get_database_session)
):
    """
    WhatsApp webhook message processing endpoint.
    Receives and processes incoming WhatsApp messages.
    """
    try:
        # Parse incoming payload
        payload = await request.json()
        logger.info(f"📥 Incoming webhook payload: {json.dumps(payload, indent=2)}")
        
        # Validate payload structure
        webhook_data = WhatsAppWebhookPayload(**payload)
        
        # Check if this is a message event
        first_message = webhook_data.get_first_message()
        if not first_message:
            logger.info("⏭️  Ignoring non-message event")
            return JSONResponse(content={"status": "ignored"}, status_code=200)
        
        # Process message with business service
        with WhatsAppService(db) as service:
            result = service.process_incoming_message(payload)
            
            if result["status"] == "duplicate":
                logger.info(f"🔄 Duplicate message: {webhook_data.message_id}")
                return JSONResponse(content=result, status_code=200)
            
            elif result["status"] == "error":
                logger.error(f"❌ Message processing failed: {result['message']}")
                return JSONResponse(content=result, status_code=400)
            
            else:
                logger.info(f"✅ Message processed successfully: {webhook_data.message_id}")
                return JSONResponse(content=result, status_code=200)
                
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {str(e)}")
        return JSONResponse(
            content={"status": "error", "message": str(e)}, 
            status_code=500
        )

@router.get("/test")
async def test_webhook():
    """Test endpoint to verify webhook is working"""
    return {
        "status": "webhook_active",
        "message": "WhatsApp webhook is ready to receive messages",
        "timestamp": json.dumps({"now": "test"})
    }
