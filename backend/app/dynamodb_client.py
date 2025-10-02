import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

from app.core.logging import logger

# Get configuration - prioritize environment variables over config defaults
TABLE_NAME = os.getenv("DYNAMODB_TABLE") or os.getenv("DYNAMODB_TABLE_NAME")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# If no environment variable is set, fall back to config.py settings
if not TABLE_NAME:
    try:
        from app.config import get_settings
        settings = get_settings()
        TABLE_NAME = getattr(settings, "dynamodb_table_name", "whatsapp-dedup-dev")
    except Exception:
        TABLE_NAME = "whatsapp-dedup-dev"

# Initialize DynamoDB client
try:
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None
    if table:
        logger.info(f"✅ DynamoDB client initialized for table: {TABLE_NAME}")
    else:
        logger.warning("⚠️  DYNAMODB_TABLE not configured; dedup store disabled")
except Exception as e:
    logger.error(f"❌ DynamoDB initialization failed: {e}")
    dynamodb = None
    table = None

def _ttl_in_hours(hours: int) -> int:
    """Return TTL epoch seconds in given hours from now."""
    return int(time.time() + hours * 3600)

def store_message_id_atomic(message_id: str, ttl_hours: int = 24) -> Dict[str, Any]:
    """
    🔒 RACE-SAFE: Atomic deduplication with processing tracking
    
    This function prevents race conditions by using DynamoDB's atomic conditional put operation.
    Multiple concurrent webhook requests with the same message_id will be handled safely:
    - First request: Creates the record and returns {"is_new": True}
    - Subsequent requests: Fail the condition and return {"is_new": False}
    
    Args:
        message_id: WhatsApp message ID to check/store
        ttl_hours: Hours before the record automatically expires (default 24h)
    
    Returns:
        Dict containing:
        - is_new: True if this is a new message, False if duplicate
        - processing_id: Unique ID for tracking this processing attempt
        - status: Current processing status
        - error: Error message if something went wrong
    """
    if not table:
        return {"is_new": False, "error": "DynamoDB not configured"}

    processing_id = str(uuid.uuid4())  # Unique ID for this processing attempt
    now = datetime.utcnow().isoformat()
    
    try:
        # 🔒 ATOMIC OPERATION: Only succeeds if message doesn't exist
        # This prevents race condition where multiple webhooks process the same message
        table.put_item(
            Item={
                "msgid": message_id,
                "created_at": now,
                "ttl": _ttl_in_hours(ttl_hours),
                "status": "received",           # Initial status
                "processing_id": processing_id, # Unique processing identifier
                "processing_started_at": now,
                "processor_id": None,          # Will be set when claimed for processing
                "webhook_count": 1             # Track webhook duplicate attempts
            },
            # 🔒 CRITICAL: This condition prevents race conditions
            ConditionExpression="attribute_not_exists(msgid)",
        )
        
        logger.info(f"🆕 New message stored: {message_id} (processing_id: {processing_id})")
        return {
            "is_new": True,
            "processing_id": processing_id,
            "status": "received"
        }
        
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            # Message already exists - this is a duplicate webhook
            try:
                # 🔒 Use strong consistency to get accurate status (prevents race conditions)
                response = table.get_item(
                    Key={"msgid": message_id},
                    ConsistentRead=True  # IMPORTANT: Strong consistency prevents race conditions
                )
                
                if "Item" in response:
                    item = response["Item"]
                    
                    # Atomically increment webhook count to track duplicates
                    try:
                        table.update_item(
                            Key={"msgid": message_id},
                            UpdateExpression="ADD webhook_count :inc",
                            ExpressionAttributeValues={":inc": 1}
                        )
                    except Exception:
                        pass  # Non-critical operation
                    
                    logger.debug(f"🔄 Duplicate message: {message_id} (status: {item.get('status')})")
                    return {
                        "is_new": False,
                        "processing_id": item.get("processing_id"),
                        "status": item.get("status", "unknown"),
                        "created_at": item.get("created_at"),
                        "webhook_count": item.get("webhook_count", 1) + 1
                    }
                    
            except Exception as get_error:
                logger.error(f"Failed to get existing message status: {get_error}")
                
            return {"is_new": False, "status": "duplicate"}
            
        logger.error(f"DynamoDB put_item failed: {e}")
        return {"is_new": False, "error": str(e)}

def claim_message_processing(message_id: str, processor_id: str) -> bool:
    """
    🔒 RACE-SAFE: Atomically claim a message for processing
    
    This prevents multiple processors from handling the same message by using
    atomic conditional updates. Only one processor can successfully claim a message.
    
    Args:
        message_id: WhatsApp message ID to claim
        processor_id: Unique processor instance identifier
        
    Returns:
        True if successfully claimed, False if already claimed by another processor
    """
    if not table:
        return False
        
    try:
        # 🔒 ATOMIC OPERATION: Only succeeds if message is in 'received' state and unclaimed
        # This prevents race condition where multiple processors try to handle same message
        table.update_item(
            Key={"msgid": message_id},
            UpdateExpression="""
                SET #status = :processing, 
                    processor_id = :processor_id,
                    processing_claimed_at = :claimed_at
            """,
            # 🔒 CRITICAL CONDITIONS: Prevents processor race conditions
            ConditionExpression="#status = :received AND attribute_not_exists(processor_id)",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":processing": "processing",
                ":received": "received",
                ":processor_id": processor_id,
                ":claimed_at": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"🔒 Message claimed for processing: {message_id} by {processor_id}")
        return True
        
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            logger.debug(f"Message {message_id} already claimed by another processor")
            return False
        logger.error(f"Failed to claim message processing: {e}")
        return False

def update_message_status_atomic(
    message_id: str, 
    status: str, 
    processor_id: str,
    error_message: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None
) -> bool:
    """
    🔒 RACE-SAFE: Atomic status update with processor ownership verification
    
    Only the processor that owns the message can update its status.
    This prevents race conditions where multiple processors try to update the same message.
    
    Args:
        message_id: WhatsApp message ID to update
        status: New status (processing, completed, failed)
        processor_id: ID of processor making the update
        error_message: Error details if status is 'failed'
        result: Processing result data
        
    Returns:
        True if update successful, False if rejected (different processor owns message)
    """
    if not table:
        return False
        
    try:
        update_expr = """
            SET #status = :status, 
                updated_at = :updated_at
        """
        expr_values = {
            ":status": status,
            ":updated_at": datetime.utcnow().isoformat(),
            ":processor_id": processor_id
        }
        expr_names = {"#status": "status"}
        
        # Add optional fields
        if error_message:
            update_expr += ", error_message = :error_msg"
            expr_values[":error_msg"] = error_message
            
        if result:
            update_expr += ", processing_result = :result"
            expr_values[":result"] = result
        
        # 🔒 CRITICAL CONDITION: Only update if this processor owns the message
        # This prevents race conditions between multiple processors
        table.update_item(
            Key={"msgid": message_id},
            UpdateExpression=update_expr,
            ConditionExpression="processor_id = :processor_id",  # Ownership check
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames=expr_names
        )
        
        logger.info(f"✅ Message status updated: {message_id} -> {status}")
        return True
        
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            logger.warning(f"❌ Status update rejected - message {message_id} owned by different processor")
            return False
        else:
            logger.error(f"Failed to update message status: {e}")
            return False

# Legacy functions for backward compatibility
def store_message_id(message_id: str, ttl_hours: int = 6) -> bool:
    """
    Legacy function - use store_message_id_atomic for race safety
    
    This function is kept for backward compatibility but should be replaced
    with store_message_id_atomic for proper race condition handling.
    """
    result = store_message_id_atomic(message_id, ttl_hours)
    return result.get("is_new", False)

def check_message_exists(message_id: str) -> bool:
    """
    Check if message ID exists in DynamoDB with strong consistency for race safety.
    
    Uses ConsistentRead=True to prevent race conditions where a message might
    appear to not exist due to eventual consistency, while another process
    has just created it.
    """
    if not table:
        return False

    try:
        response = table.get_item(
            Key={"msgid": message_id}, 
            ConsistentRead=True  # 🔒 Strong consistency prevents race conditions
        )
        return "Item" in response
    except Exception as e:
        logger.exception(f"DynamoDB get_item failed: {e}")
        return False
