"""
High-level messaging service functions
Provides easy-to-use functions for sending messages and events
"""
from typing import Dict, Any, Optional, List
import time

from app.services.sqs_service import send_outgoing_message as _send_outgoing_message
from app.services.sqs_service import send_analytics_event as _send_analytics_event
from app.core.logging import logger

async def send_whatsapp_message(
    phone_number: str,
    message_type: str,
    content: str,
    media_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    priority: str = "normal"
) -> Optional[str]:
    """
    High-level function to send WhatsApp messages via SQS
    
    Args:
        phone_number: Recipient phone number
        message_type: Type of message (text, image, document, etc.)
        content: Message content/text
        media_url: URL for media messages (optional)
        metadata: Additional metadata (optional)
        priority: Message priority (high, normal, low)
    
    Returns:
        Message ID if queued successfully, None otherwise
    """
    try:
        message_data = {
            "type": message_type,
            "content": content
        }
        
        if media_url:
            message_data["media_url"] = media_url
        
        combined_metadata = {
            "priority": priority,
            "requested_at": int(time.time()),
            "source": "messaging_service"
        }
        
        if metadata:
            combined_metadata.update(metadata)
        
        message_id = await _send_outgoing_message(
            phone_number=phone_number,
            message_data=message_data,
            metadata=combined_metadata
        )
        
        if message_id:
            logger.info(f"✅ WhatsApp message queued: {message_id} to {phone_number}")
            
            # Track analytics
            await track_event("whatsapp_message_queued", {
                "phone_number": phone_number,
                "message_type": message_type,
                "priority": priority,
                "queue_message_id": message_id
            })
            
            return message_id
        else:
            logger.error(f"❌ Failed to queue WhatsApp message to {phone_number}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp message: {e}")
        return None

async def send_text_message(
    phone_number: str,
    text: str,
    priority: str = "normal",
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """Convenience function for sending text messages"""
    return await send_whatsapp_message(
        phone_number=phone_number,
        message_type="text",
        content=text,
        priority=priority,
        metadata=metadata
    )

async def send_image_message(
    phone_number: str,
    image_url: str,
    caption: Optional[str] = None,
    priority: str = "normal",
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """Convenience function for sending image messages"""
    return await send_whatsapp_message(
        phone_number=phone_number,
        message_type="image",
        content=caption or "",
        media_url=image_url,
        priority=priority,
        metadata=metadata
    )

async def send_document_message(
    phone_number: str,
    document_url: str,
    filename: str,
    caption: Optional[str] = None,
    priority: str = "normal",
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """Convenience function for sending document messages"""
    document_metadata = {"filename": filename}
    if metadata:
        document_metadata.update(metadata)
    
    return await send_whatsapp_message(
        phone_number=phone_number,
        message_type="document",
        content=caption or filename,
        media_url=document_url,
        priority=priority,
        metadata=document_metadata
    )

async def track_event(
    event_type: str,
    event_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    High-level function to track analytics events via SQS
    
    Args:
        event_type: Type of event (user_action, system_event, etc.)
        event_data: Event data dictionary
        metadata: Additional metadata (optional)
    
    Returns:
        Message ID if queued successfully, None otherwise
    """
    try:
        combined_metadata = {
            "tracked_at": int(time.time()),
            "source": "messaging_service"
        }
        
        if metadata:
            combined_metadata.update(metadata)
        
        message_id = await _send_analytics_event(
            event_type=event_type,
            event_data=event_data,
            metadata=combined_metadata
        )
        
        if message_id:
            logger.debug(f"✅ Analytics event queued: {event_type}")
            return message_id
        else:
            logger.warning(f"⚠️  Failed to queue analytics event: {event_type}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error tracking event {event_type}: {e}")
        return None

async def track_user_action(
    user_id: str,
    action: str,
    details: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """Convenience function for tracking user actions"""
    event_data = {
        "user_id": user_id,
        "action": action
    }
    
    if details:
        event_data["details"] = details
    
    return await track_event("user_action", event_data)

async def track_system_event(
    component: str,
    event: str,
    details: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """Convenience function for tracking system events"""
    event_data = {
        "component": component,
        "event": event
    }
    
    if details:
        event_data["details"] = details
    
    return await track_event("system_event", event_data)

async def track_webhook_event(
    webhook_type: str,
    phone_number: str,
    message_id: str,
    status: str,
    details: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """Convenience function for tracking webhook events"""
    event_data = {
        "webhook_type": webhook_type,
        "phone_number": phone_number,
        "message_id": message_id,
        "status": status
    }
    
    if details:
        event_data["details"] = details
    
    return await track_event("webhook_event", event_data)

# Bulk operations
async def send_bulk_messages(
    messages: List[Dict[str, Any]],
    priority: str = "normal"
) -> Dict[str, Any]:
    """
    Send multiple messages in bulk
    
    Args:
        messages: List of message dictionaries with phone_number, message_type, content, etc.
        priority: Priority for all messages
    
    Returns:
        Dictionary with success/failure counts and message IDs
    """
    results = {
        "total": len(messages),
        "success": 0,
        "failed": 0,
        "message_ids": [],
        "errors": []
    }
    
    for i, message in enumerate(messages):
        try:
            message_id = await send_whatsapp_message(
                phone_number=message["phone_number"],
                message_type=message["message_type"],
                content=message["content"],
                media_url=message.get("media_url"),
                metadata=message.get("metadata"),
                priority=priority
            )
            
            if message_id:
                results["success"] += 1
                results["message_ids"].append(message_id)
            else:
                results["failed"] += 1
                results["errors"].append(f"Message {i}: Failed to queue")
                
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Message {i}: {str(e)}")
    
    logger.info(f"📊 Bulk send completed: {results['success']}/{results['total']} successful")
    
    # Track bulk operation
    await track_event("bulk_message_operation", {
        "total_messages": results["total"],
        "successful": results["success"],
        "failed": results["failed"],
        "priority": priority
    })
    
    return results