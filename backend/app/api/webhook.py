"""
🔒 RACE-SAFE WhatsApp webhook endpoints.
Handles WhatsApp webhook verification and message processing with atomic deduplication and SQS queuing.

Race Condition Prevention:
- Uses atomic DynamoDB operations for deduplication
- Implements fast webhook response (< 5 seconds required by WhatsApp)
- Queues messages for async processing to prevent blocking
- Handles concurrent webhook requests safely
"""
from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session
import json
import time
import uuid
import os
from typing import Dict, Any, List

from app.core.database import get_database_session
from app.core.logging import logger
from app.core.exceptions import WebhookException, DuplicateMessageException
from app.services.whatsapp_service import WhatsAppService
from app.services.sqs_service import send_incoming_message, sqs_service
from app.services.messaging_service import track_webhook_event
from app.models.whatsapp import WhatsAppWebhookPayload
from app.config import get_settings
# 🔒 Import race-safe DynamoDB functions
from app.dynamodb_client import store_message_id_atomic
# Import startup validation for readiness checks
try:
    from app.services.startup_validator import is_application_ready
    STARTUP_VALIDATION_AVAILABLE = True
except ImportError:
    is_application_ready = None
    STARTUP_VALIDATION_AVAILABLE = False

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
    🔒 RACE-SAFE WhatsApp webhook message processing endpoint.
    
    Flow: Webhook → Atomic Dedup Check → SQS Queue → Fast Response
    
    Race Condition Prevention:
    1. Uses atomic DynamoDB operations for deduplication
    2. Fast response (< 5 seconds) required by WhatsApp
    3. Queues messages for async processing
    4. Handles concurrent identical webhooks safely
    
    Returns:
        JSONResponse with processing results and timing information
    """
    webhook_id = str(uuid.uuid4())  # Unique webhook processing ID
    start_time = time.time()
    
    try:
        # 🔒 STEP 0: Check application readiness before processing
        if STARTUP_VALIDATION_AVAILABLE and is_application_ready and not is_application_ready():
            logger.error(f"❌ Webhook {webhook_id}: Application not ready - critical dependencies unavailable")
            return JSONResponse(
                content={
                    "status": "service_unavailable",
                    "message": "Application dependencies not available",
                    "webhook_id": webhook_id,
                    "timestamp": time.time()
                },
                status_code=503
            )
        
        # Parse incoming payload
        payload = await request.json()
        logger.info(f"📥 Webhook {webhook_id}: Processing incoming payload")
        logger.debug(f"Payload content: {json.dumps(payload, indent=2)}")
        
        # Quick validation to filter out non-message events early
        if not payload.get("entry"):
            logger.info(f"⏭️  Webhook {webhook_id}: Ignoring non-entry event")
            return JSONResponse(content={"status": "ignored"}, status_code=200)
        
        # Validate payload structure
        webhook_data = WhatsAppWebhookPayload(**payload)
        
        # Process all messages in the webhook with race-safe deduplication
        processing_results = []
        stats = {"new": 0, "duplicates": 0, "errors": 0}
        
        for entry in payload.get("entry", []):
            entry_id = entry.get("id", "unknown")
            
            for change in entry.get("changes", []):
                if change.get("field") != "messages":
                    continue
                    
                messages = change.get("value", {}).get("messages", [])
                contacts = change.get("value", {}).get("contacts", [])
                metadata = change.get("value", {}).get("metadata", {})
                
                # Process each message with atomic deduplication
                for i, message in enumerate(messages):
                    result = await process_single_message_safe(
                        message=message,
                        contact=contacts[i] if i < len(contacts) else {},
                        metadata=metadata,
                        webhook_id=webhook_id,
                        entry_id=entry_id
                    )
                    
                    processing_results.append(result)
                    stats[result["category"]] += 1
        
        processing_time = time.time() - start_time
        
        # Log summary for monitoring
        logger.info(
            f"🔄 Webhook {webhook_id} completed in {processing_time:.3f}s: "
            f"{stats['new']} new, {stats['duplicates']} duplicates, {stats['errors']} errors"
        )
        
        # 🚀 Fast response to WhatsApp (CRITICAL: Must be < 5 seconds)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "webhook_id": webhook_id,
                "processing_time_ms": int(processing_time * 1000),
                "stats": stats,
                "results": processing_results
            }
        )
        
    except json.JSONDecodeError as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Webhook {webhook_id}: Invalid JSON payload after {processing_time:.3f}s")
        return JSONResponse(
            status_code=400, 
            content={"status": "error", "message": "Invalid JSON payload", "webhook_id": webhook_id}
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Webhook {webhook_id} failed after {processing_time:.3f}s: {e}")
        
        # For critical errors, return error response (don't attempt fallback)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error", 
                "message": "Internal server error", 
                "webhook_id": webhook_id
            }
        )

async def process_single_message_safe(
    message: Dict[str, Any],
    contact: Dict[str, Any],
    metadata: Dict[str, Any],
    webhook_id: str,
    entry_id: str
) -> Dict[str, Any]:
    """
    🔒 RACE-SAFE: Process individual message with atomic deduplication
    
    This function handles each WhatsApp message with complete race condition protection:
    1. Atomic deduplication check using DynamoDB
    2. SQS queuing for async processing
    3. Detailed result tracking
    
    Returns:
        Dict with processing result and categorization for statistics
    """
    message_id = message.get("id")
    phone_number = message.get("from", "unknown")
    message_type = message.get("type", "unknown")
    
    if not message_id:
        logger.error(f"❌ Webhook {webhook_id}: Missing message ID")
        return {
            "message_id": None,
            "phone_number": phone_number,
            "status": "error",
            "category": "errors",
            "error": "Missing message ID"
        }
    
    try:
        # 🔒 STEP 1: Atomic deduplication check (prevents race conditions)
        dedup_result = store_message_id_atomic(message_id, ttl_hours=24)
        
        if not dedup_result.get("is_new", False):
            # Handle duplicate/error cases
            status = dedup_result.get("status", "duplicate")
            logger.debug(f"🔄 Webhook {webhook_id}: Non-new message {message_id} - {status}")
            
            return {
                "message_id": message_id,
                "phone_number": phone_number,
                "message_type": message_type,
                "status": status,
                "category": "duplicates",
                "processing_id": dedup_result.get("processing_id"),
                "webhook_count": dedup_result.get("webhook_count", 1),
                "details": dedup_result
            }
        
        # 🔒 STEP 2: Send new message to SQS for async processing
        sqs_success = await send_incoming_message(
            webhook_data={
                "message": message,
                "contact": contact,
                "metadata": metadata
            },
            metadata={
                "webhook_id": webhook_id,
                "entry_id": entry_id,
                "processing_id": dedup_result["processing_id"],
                "message_id": message_id,
                "phone_number": phone_number,
                "message_type": message_type,
                "received_at": int(time.time()),
                "ttl_hours": 24
            }
        )
        
        if sqs_success:
            logger.info(f"✅ Webhook {webhook_id}: New message queued: {message_id} (type: {message_type})")
            
            # Track successful queuing for analytics
            try:
                await track_webhook_event(
                    webhook_type="incoming_message",
                    phone_number=phone_number,
                    message_id=message_id,
                    status="queued",
                    details={
                        "queue_message_id": sqs_success,
                        "processing_id": dedup_result["processing_id"],
                        "webhook_id": webhook_id
                    }
                )
            except Exception as track_error:
                logger.warning(f"⚠️ Failed to track webhook event: {track_error}")
            
            return {
                "message_id": message_id,
                "phone_number": phone_number,
                "message_type": message_type,
                "status": "queued",
                "category": "new",
                "processing_id": dedup_result["processing_id"],
                "sqs_message_id": sqs_success
            }
        else:
            logger.error(f"❌ Webhook {webhook_id}: Failed to queue message: {message_id}")
            return {
                "message_id": message_id,
                "phone_number": phone_number,
                "message_type": message_type,
                "status": "queue_failed",
                "category": "errors",
                "processing_id": dedup_result["processing_id"],
                "error": "SQS send failed"
            }
            
    except Exception as e:
        logger.error(f"❌ Webhook {webhook_id}: Error processing message {message_id}: {e}")
        return {
            "message_id": message_id,
            "phone_number": phone_number,
            "message_type": message_type,
            "status": "processing_error",
            "category": "errors",
            "error": str(e)
        }


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
