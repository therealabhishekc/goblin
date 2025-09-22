import os
import time
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

from app.core.logging import logger

# Get configuration
try:
    from app.config import get_settings
    settings = get_settings()
    TABLE_NAME = getattr(settings, "dynamodb_table_name", None) or os.getenv("DYNAMODB_TABLE")
    AWS_REGION = getattr(settings, "aws_region", None) or os.getenv("AWS_REGION", "us-east-1")
except Exception:
    # Fallback to environment variables only
    TABLE_NAME = os.getenv("DYNAMODB_TABLE") or os.getenv("DYNAMODB_TABLE_NAME", "whatsapp-dedup-dev")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

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

def store_message_id(message_id: str, ttl_hours: int = 6) -> bool:
    """Store message ID in DynamoDB with TTL.

    Uses conditional put to avoid overwriting existing IDs (idempotency).
    Ensure the table has TTL enabled on attribute 'ttl'.
    """
    if not table:
        logger.error("DynamoDB table not configured; cannot store message_id")
        return False

    try:
        table.put_item(
            Item={
                "msgid": message_id,
                "created_at": datetime.utcnow().isoformat(),
                "ttl": _ttl_in_hours(ttl_hours),
            },
            ConditionExpression="attribute_not_exists(msgid)",
        )
        return True
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code == "ConditionalCheckFailedException":
            # Already exists -> treat as stored (idempotent)
            logger.debug(f"Message ID already exists (dedup): {message_id}")
            return False
        logger.exception(f"DynamoDB put_item failed: {e}")
        return False
    except Exception as e:
        logger.exception(f"DynamoDB put_item unexpected error: {e}")
        return False

def check_message_exists(message_id: str) -> bool:
    """Check if message ID exists in DynamoDB (non-consistent read)."""
    if not table:
        return False

    try:
        response = table.get_item(Key={"msgid": message_id}, ConsistentRead=False)
        return "Item" in response
    except Exception as e:
        logger.exception(f"DynamoDB get_item failed: {e}")
        return False
