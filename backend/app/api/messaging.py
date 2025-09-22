"""
SQS-powered messaging API endpoints
Provides async message sending and queue management
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import time

from app.services.sqs_service import send_outgoing_message, send_analytics_event, sqs_service, QueueType
from app.core.logging import logger

router = APIRouter(prefix="/messaging", tags=["Async Messaging"])

class OutgoingMessageRequest(BaseModel):
    """Request model for sending outgoing messages"""
    phone_number: str = Field(..., description="Phone number to send message to")
    message_type: str = Field(..., description="Type of message (text, image, document, etc.)")
    message_data: Dict[str, Any] = Field(..., description="Message content and metadata")
    priority: Optional[str] = Field("normal", description="Message priority (high, normal, low)")
    delay_seconds: Optional[int] = Field(0, description="Delay before processing (0-900 seconds)")

class AnalyticsEventRequest(BaseModel):
    """Request model for sending analytics events"""
    event_type: str = Field(..., description="Type of analytics event")
    event_data: Dict[str, Any] = Field(..., description="Event data")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

@router.post("/send")
async def send_message_async(request: OutgoingMessageRequest):
    """
    Send a WhatsApp message asynchronously via SQS
    Messages are queued for processing by background workers
    """
    try:
        metadata = {
            "priority": request.priority,
            "requested_at": int(time.time()),
            "source": "api_request"
        }
        
        message_id = await send_outgoing_message(
            phone_number=request.phone_number,
            message_data={
                "type": request.message_type,
                **request.message_data
            },
            metadata=metadata
        )
        
        if message_id:
            logger.info(f"✅ Outgoing message queued: {message_id}")
            
            # Send analytics event
            await send_analytics_event("message_queued", {
                "phone_number": request.phone_number,
                "message_type": request.message_type,
                "priority": request.priority,
                "queue_message_id": message_id
            })
            
            return {
                "status": "queued",
                "message_id": message_id,
                "phone_number": request.phone_number,
                "estimated_processing_time": "1-5 minutes",
                "priority": request.priority
            }
        else:
            logger.error("❌ Failed to queue outgoing message")
            raise HTTPException(
                status_code=503,
                detail="Message queuing service unavailable"
            )
            
    except Exception as e:
        logger.error(f"❌ Error queuing outgoing message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue message: {str(e)}"
        )

@router.post("/analytics")
async def send_analytics_event_api(request: AnalyticsEventRequest):
    """
    Send an analytics event asynchronously via SQS
    Events are queued for processing by background workers
    """
    try:
        metadata = {
            "requested_at": int(time.time()),
            "source": "api_request",
            **request.metadata
        }
        
        message_id = await send_analytics_event(
            event_type=request.event_type,
            event_data=request.event_data,
            metadata=metadata
        )
        
        if message_id:
            logger.info(f"✅ Analytics event queued: {message_id}")
            return {
                "status": "queued",
                "message_id": message_id,
                "event_type": request.event_type
            }
        else:
            logger.error("❌ Failed to queue analytics event")
            raise HTTPException(
                status_code=503,
                detail="Analytics queuing service unavailable"
            )
            
    except Exception as e:
        logger.error(f"❌ Error queuing analytics event: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue analytics event: {str(e)}"
        )

@router.get("/queue/status")
async def get_queue_status():
    """
    Get status of all SQS queues
    Shows message counts and health status
    """
    try:
        queue_status = {}
        
        for queue_type in QueueType:
            try:
                attributes = await sqs_service.get_queue_attributes(queue_type)
                queue_status[queue_type.value] = {
                    "status": "healthy" if attributes else "unhealthy",
                    "approximate_messages": int(attributes.get('ApproximateNumberOfMessages', 0)),
                    "approximate_messages_not_visible": int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0)),
                    "approximate_messages_delayed": int(attributes.get('ApproximateNumberOfMessagesDelayed', 0)),
                    "queue_url": sqs_service.queue_urls.get(queue_type, "not_configured")
                }
            except Exception as e:
                queue_status[queue_type.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        overall_status = "healthy"
        total_messages = sum(
            q.get("approximate_messages", 0) 
            for q in queue_status.values() 
            if isinstance(q.get("approximate_messages"), int)
        )
        
        if any(q.get("status") != "healthy" for q in queue_status.values()):
            overall_status = "degraded"
        
        return {
            "overall_status": overall_status,
            "total_messages_pending": total_messages,
            "queues": queue_status,
            "timestamp": int(time.time())
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting queue status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue status: {str(e)}"
        )

@router.post("/queue/{queue_type}/purge")
async def purge_queue(queue_type: str):
    """
    Purge all messages from a specific queue (DANGEROUS - use with caution)
    Only available in development/staging environments
    """
    from app.config import get_settings
    settings = get_settings()
    
    if settings.environment == "production":
        raise HTTPException(
            status_code=403,
            detail="Queue purging is not allowed in production environment"
        )
    
    try:
        # Validate queue type
        try:
            queue_enum = QueueType(queue_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid queue type: {queue_type}. Valid types: {[q.value for q in QueueType]}"
            )
        
        queue_url = sqs_service.queue_urls.get(queue_enum)
        if not queue_url:
            raise HTTPException(
                status_code=404,
                detail=f"Queue {queue_type} not configured"
            )
        
        # Get current message count before purging
        attributes = await sqs_service.get_queue_attributes(queue_enum)
        messages_before = int(attributes.get('ApproximateNumberOfMessages', 0))
        
        # Purge the queue
        import aioboto3
        session = aioboto3.Session()
        async with session.client('sqs', region_name=settings.aws_region) as sqs:
            await sqs.purge_queue(QueueUrl=queue_url)
        
        logger.warning(f"⚠️  Queue {queue_type} purged by API request - {messages_before} messages deleted")
        
        return {
            "status": "purged",
            "queue_type": queue_type,
            "messages_deleted": messages_before,
            "timestamp": int(time.time()),
            "warning": "All messages in the queue have been permanently deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error purging queue {queue_type}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to purge queue: {str(e)}"
        )

@router.get("/health")
async def messaging_health():
    """
    Health check for messaging service
    """
    try:
        # Check SQS health
        sqs_health = await sqs_service.health_check()
        
        # Check if workers are running
        try:
            from app.workers.message_processor import message_processor
            worker_stats = message_processor.get_stats()
            workers_healthy = worker_stats["running"]
        except Exception:
            workers_healthy = False
        
        overall_status = "healthy"
        if sqs_health["sqs_service"] != "healthy":
            overall_status = "degraded"
        if not workers_healthy:
            overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
        
        return {
            "messaging_service": overall_status,
            "sqs": sqs_health,
            "workers": {
                "status": "running" if workers_healthy else "stopped",
                "details": worker_stats if workers_healthy else "not_available"
            },
            "timestamp": int(time.time())
        }
        
    except Exception as e:
        return JSONResponse(
            content={
                "messaging_service": "unhealthy",
                "error": str(e),
                "timestamp": int(time.time())
            },
            status_code=503
        )