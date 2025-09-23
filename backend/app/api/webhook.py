"""
WhatsApp webhook endpoints.
Handles WhatsApp webhook verification and message processing with SQS queuing.
"""
from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session
import json
import time
import os

from app.core.database import get_database_session
from app.core.logging import logger
from app.core.exceptions import WebhookException, DuplicateMessageException
from app.services.whatsapp_service import WhatsAppService
from app.services.sqs_service import send_incoming_message, sqs_service
from app.services.messaging_service import track_webhook_event
from app.models.whatsapp import WhatsAppWebhookPayload
from app.config import get_settings

router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])

@router.get("/", response_class=PlainTextResponse)
@router.get("", response_class=PlainTextResponse)
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
    logger.info(f"Webhook verification attempt: mode={hub_mode}, challenge_provided={bool(hub_challenge)}, token_provided={bool(hub_verify_token)}")
    logger.info(f"Expected verify_token configured: {bool(settings.verify_token)}")
    
    if not hub_mode:
        logger.error("❌ No hub.mode parameter received")
        raise HTTPException(status_code=400, detail="Missing hub.mode parameter")
    
    if not hub_verify_token:
        logger.error("❌ No hub.verify_token parameter received")
        raise HTTPException(status_code=400, detail="Missing hub.verify_token parameter")
    
    if not settings.verify_token:
        logger.error("❌ VERIFY_TOKEN environment variable not configured")
        raise HTTPException(status_code=500, detail="Server configuration error")
    
    if hub_mode == "subscribe" and hub_verify_token == settings.verify_token:
        logger.info("✅ Webhook verification successful")
        return hub_challenge or ""
    
    logger.warning(f"❌ Webhook verification failed - mode: {hub_mode}, token_match: {hub_verify_token == settings.verify_token}")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/")
@router.post("")
async def process_webhook(
    request: Request,
    db: Session = Depends(get_database_session)
):
    """
    WhatsApp webhook message processing endpoint.
    Queues incoming messages for async processing with fallback to direct processing.
    """
    try:
        # Parse incoming payload
        payload = await request.json()
        logger.info(f"📥 Incoming webhook payload: {json.dumps(payload, indent=2)}")
        
        # Quick validation to filter out non-message events early
        if not payload.get("entry"):
            logger.info("⏭️  Ignoring non-entry event")
            return JSONResponse(content={"status": "ignored"}, status_code=200)
        
        # Validate payload structure
        webhook_data = WhatsAppWebhookPayload(**payload)
        
        # Check if this is a message event
        first_message = webhook_data.get_first_message()
        if not first_message:
            logger.info("⏭️  Ignoring non-message event")
            return JSONResponse(content={"status": "ignored"}, status_code=200)
        
        # Try to queue the message for async processing
        message_metadata = {
            "webhook_timestamp": int(time.time()),
            "message_id": webhook_data.message_id,
            "phone_number": first_message.get("from", "unknown"),
            "message_type": first_message.get("type", "unknown")
        }
        
        message_id = await send_incoming_message(payload, message_metadata)
        
        if message_id:
            # Successfully queued - return immediately
            logger.info(f"✅ Message queued for processing: {message_id}")
            
            # Track webhook reception
            await track_webhook_event(
                webhook_type="incoming_message",
                phone_number=first_message.get("from", "unknown"),
                message_id=webhook_data.message_id,
                status="queued",
                details={"queue_message_id": message_id}
            )
            
            return JSONResponse(content={
                "status": "queued",
                "message_id": message_id,
                "queue_message_id": message_id,
                "processing": "async"
            }, status_code=200)
        else:
            # Fallback to direct processing if SQS fails
            logger.warning("⚠️  SQS unavailable, falling back to direct processing")
            return await process_webhook_directly(payload, db)
                
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {str(e)}")
        # Try direct processing as last resort
        try:
            return await process_webhook_directly(await request.json(), db)
        except:
            return JSONResponse(
                content={"status": "error", "message": str(e)}, 
                status_code=500
            )

async def process_webhook_directly(payload: dict, db: Session):
    """
    Direct webhook processing (fallback when SQS is unavailable)
    """
    try:
        webhook_data = WhatsAppWebhookPayload(**payload)
        
        # Process message with business service
        with WhatsAppService(db) as service:
            result = await service.process_incoming_message(payload)
            
            if result["status"] == "duplicate":
                logger.info(f"🔄 Duplicate message: {webhook_data.message_id}")
                return JSONResponse(content=result, status_code=200)
            
            elif result["status"] == "error":
                logger.error(f"❌ Message processing failed: {result['message']}")
                return JSONResponse(content=result, status_code=400)
            
            else:
                logger.info(f"✅ Message processed directly: {webhook_data.message_id}")
                result["processing"] = "direct"  # Mark as direct processing
                return JSONResponse(content=result, status_code=200)
                
    except Exception as e:
        logger.error(f"❌ Direct processing error: {str(e)}")
        return JSONResponse(
            content={"status": "error", "message": str(e), "processing": "failed"}, 
            status_code=500
        )

@router.get("/test")
async def test_webhook():
    """Test endpoint to verify webhook is working"""
    settings = get_settings()
    return {
        "status": "webhook_active",
        "message": "WhatsApp webhook is ready to receive messages",
        "sqs_enabled": bool(sqs_service.queue_urls.get("incoming")),
        "verify_token_configured": bool(settings.verify_token),
        "whatsapp_token_configured": bool(settings.whatsapp_token),
        "environment": settings.environment,
        "timestamp": int(time.time())
    }

@router.get("/health")
async def webhook_health():
    """Health check for webhook and SQS integration"""
    try:
        sqs_health = await sqs_service.health_check()
        return {
            "webhook": "healthy",
            "sqs": sqs_health,
            "timestamp": int(time.time())
        }
    except Exception as e:
        return JSONResponse(
            content={
                "webhook": "healthy",
                "sqs": {"status": "unhealthy", "error": str(e)},
                "timestamp": int(time.time())
            },
            status_code=503
        )

@router.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration (use with caution in production)"""
    settings = get_settings()
    
    # Only show config status, not actual values for security
    config_status = {
        "environment": settings.environment,
        "verify_token_set": bool(settings.verify_token),
        "whatsapp_token_set": bool(settings.whatsapp_token),
        "phone_number_id_set": bool(settings.whatsapp_phone_number_id or settings.phone_number_id),
        "database_url_set": bool(settings.database_url),
        "aws_region": settings.aws_region,
        "debug_mode": settings.debug,
        "log_level": settings.log_level,
        "sqs_queues": {
            "incoming": bool(settings.incoming_queue_url),
            "outgoing": bool(settings.outgoing_queue_url),
            "analytics": bool(settings.analytics_queue_url)
        }
    }
    
    # Add environment variable existence check
    env_vars = {
        "VERIFY_TOKEN": "VERIFY_TOKEN" in os.environ,
        "WHATSAPP_TOKEN": "WHATSAPP_TOKEN" in os.environ,
        "DATABASE_URL": "DATABASE_URL" in os.environ,
        "ENVIRONMENT": "ENVIRONMENT" in os.environ
    }
    
    return {
        "config_status": config_status,
        "environment_variables": env_vars,
        "timestamp": int(time.time())
    }
