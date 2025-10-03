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

async def send_template_message(
    phone_number: str,
    template_name: str,
    parameters: Optional[List[Dict[str, Any]]] = None,
    priority: str = "normal",
    metadata: Optional[Dict[str, Any]] = None,
    check_subscription: bool = True  # ⭐ Check subscription by default
) -> Optional[str]:
    """
    Send WhatsApp template message
    
    Args:
        phone_number: Recipient phone number
        template_name: Name of the WhatsApp template
        parameters: Template parameters
        priority: Message priority
        metadata: Additional metadata
        check_subscription: If True, only send to subscribed users (default: True)
    
    Returns:
        Message ID if queued successfully, None if user unsubscribed or error
    """
    try:
        # ⭐ CHECK SUBSCRIPTION STATUS ⭐
        if check_subscription:
            from app.core.database import get_db_session
            from app.repositories.user_repository import UserRepository
            
            with get_db_session() as db:
                user_repo = UserRepository(db)
                is_subscribed = user_repo.is_user_subscribed(phone_number)
            
            if not is_subscribed:
                logger.warning(f"📵 User {phone_number} is unsubscribed - template not sent")
                return None
        
        # User is subscribed - proceed
        message_data = {
            "type": "template",
            "template_name": template_name,
            "parameters": parameters or []
        }
        
        combined_metadata = {
            "priority": priority,
            "requested_at": int(time.time()),
            "source": "messaging_service",
            "template_name": template_name,
            "subscription_checked": check_subscription
        }
        
        if metadata:
            combined_metadata.update(metadata)
        
        message_id = await _send_outgoing_message(
            phone_number=phone_number,
            message_data=message_data,
            metadata=combined_metadata
        )
        
        if message_id:
            logger.info(f"✅ Template message queued: {template_name} to {phone_number}")
            await track_event("template_message_queued", {
                "phone_number": phone_number,
                "template_name": template_name,
                "priority": priority,
                "queue_message_id": message_id
            })
            return message_id
        else:
            logger.error(f"❌ Failed to queue template to {phone_number}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error sending template: {e}")
        return None

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

async def send_bulk_templates(
    template_name: str,
    recipients: List[str],  # List of phone numbers
    parameters: Optional[List[Dict[str, Any]]] = None,
    priority: str = "normal",
    check_subscription: bool = True
) -> Dict[str, Any]:
    """
    Send template messages to multiple recipients
    Only sends to subscribed users if check_subscription=True
    
    Args:
        template_name: Name of the WhatsApp template
        recipients: List of phone numbers
        parameters: Template parameters
        priority: Message priority
        check_subscription: If True, only send to subscribed users
    
    Returns:
        Dictionary with success/failure/blocked counts
    """
    results = {
        "total": len(recipients),
        "success": 0,
        "failed": 0,
        "blocked": 0,  # Users who are unsubscribed
        "message_ids": [],
        "blocked_users": [],
        "errors": []
    }
    
    # Get all subscribed users if checking subscription
    subscribed_phones = None
    if check_subscription:
        from app.core.database import get_db_session
        from app.repositories.user_repository import UserRepository
        
        with get_db_session() as db:
            user_repo = UserRepository(db)
            subscribed_users = user_repo.get_subscribed_users()
            subscribed_phones = {user.whatsapp_phone for user in subscribed_users}
        
        logger.info(f"📊 Found {len(subscribed_phones)} subscribed users out of {len(recipients)} recipients")
    
    for phone_number in recipients:
        try:
            # Check subscription
            if check_subscription and subscribed_phones and phone_number not in subscribed_phones:
                results["blocked"] += 1
                results["blocked_users"].append(phone_number)
                logger.debug(f"📵 Skipping unsubscribed user: {phone_number}")
                continue
            
            # Send template
            message_id = await send_template_message(
                phone_number=phone_number,
                template_name=template_name,
                parameters=parameters,
                priority=priority,
                check_subscription=False  # Already checked above for efficiency
            )
            
            if message_id:
                results["success"] += 1
                results["message_ids"].append(message_id)
            else:
                results["failed"] += 1
                results["errors"].append(f"{phone_number}: Failed to queue")
                
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"{phone_number}: {str(e)}")
    
    logger.info(f"📊 Bulk template send: {results['success']} sent, {results['blocked']} blocked (unsubscribed), {results['failed']} failed")
    
    # Track bulk operation
    await track_event("bulk_template_operation", {
        "template_name": template_name,
        "total_recipients": results["total"],
        "successful": results["success"],
        "blocked": results["blocked"],
        "failed": results["failed"],
        "priority": priority
    })
    
    return results