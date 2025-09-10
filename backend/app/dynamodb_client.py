import boto3
import os
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# DynamoDB configuration
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "ttest")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize DynamoDB client
try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(TABLE_NAME)
    print(f"DynamoDB client initialized for table: {TABLE_NAME}", flush=True)
except Exception as e:
    print(f"DynamoDB initialization failed: {e}", flush=True)
    dynamodb = None
    table = None

def store_message_id(message_id, ttl_hours=6):
    """Store message ID in DynamoDB with TTL"""
    if not table:
        return False
    
    try:
        # Calculate TTL (Time To Live) timestamp
        ttl_timestamp = int((datetime.utcnow() + timedelta(hours=ttl_hours)).timestamp())
        
        table.put_item(
            Item={
                'message_id': message_id,
                'created_at': datetime.utcnow().isoformat(),
                'ttl': ttl_timestamp
            }
        )
        return True
    except Exception as e:
        print(f"DynamoDB put_item failed: {e}", flush=True)
        return False

def check_message_exists(message_id):
    """Check if message ID exists in DynamoDB"""
    if not table:
        return False
    
    try:
        response = table.get_item(
            Key={'message_id': message_id}
        )
        return 'Item' in response
    except Exception as e:
        print(f"DynamoDB get_item failed: {e}", flush=True)
        return False
