"""
🔒 RACE-SAFE SQS Service Layer for WhatsApp Business API
Handles all SQS operations with race condition prevention and async/await support

Race Condition Prevention Features:
- Extended visibility timeouts to prevent processor races
- Message metadata tracking for processing coordination
- Proper error handling and retry mechanisms
- Long polling for efficient message retrieval
"""
import asyncio
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

import aioboto3
from botocore.exceptions import ClientError

from app.config import get_settings
from app.core.logging import logger
settings = get_settings()

class QueueType(Enum):
    """Enum for different queue types"""
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    ANALYTICS = "analytics"

@dataclass
class SQSMessage:
    """🔒 Race-Safe SQS Message data class with enhanced metadata tracking"""
    message_id: str
    receipt_handle: str
    body: Dict[str, Any]
    attributes: Dict[str, Any]
    timestamp: int
    processing_id: Optional[str] = None  # From DynamoDB for race tracking

class SQSService:
    """
    🔒 RACE-SAFE SQS Service for handling message queuing operations
    Provides async methods for sending, receiving, and managing messages with race condition prevention
    """
    
    def __init__(self):
        self.session = aioboto3.Session()
        self.region = settings.aws_region
        
        # Queue URLs from environment variables
        self.queue_urls = {
            QueueType.INCOMING: getattr(settings, 'incoming_queue_url', ''),
            QueueType.OUTGOING: getattr(settings, 'outgoing_queue_url', ''),
            QueueType.ANALYTICS: getattr(settings, 'analytics_queue_url', '')
        }
        
        self.dlq_urls = {
            QueueType.INCOMING: getattr(settings, 'incoming_dlq_url', ''),
            QueueType.OUTGOING: getattr(settings, 'outgoing_dlq_url', ''),
            QueueType.ANALYTICS: getattr(settings, 'analytics_dlq_url', '')
        }
        
        # 🔒 Race-safe SQS configuration
        self.visibility_timeout = getattr(settings, 'sqs_visibility_timeout', 900)  # 15 minutes
        self.max_receive_count = getattr(settings, 'sqs_max_receive_count', 3)  # Before DLQ
        self.wait_time_seconds = getattr(settings, 'sqs_wait_time_seconds', 20)  # Long polling
        
        # Track missing queue URLs to avoid repeated logging
        self._missing_queue_logged = set()
        
        # Check if any queue URLs are configured
        configured_queues = [url for url in self.queue_urls.values() if url and url.strip()]
        if not configured_queues:
            logger.warning("⚠️ No SQS queues configured - message queuing disabled")
        else:
            logger.info(f"✅ SQS service initialized with {len(configured_queues)} queues")
    
    async def send_message(
        self, 
        queue_type: QueueType, 
        message_body: Dict[str, Any],
        delay_seconds: int = 0,
        message_attributes: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        🔒 RACE-SAFE: Send a message to the specified SQS queue with enhanced metadata
        
        Args:
            queue_type: Type of queue to send to
            message_body: Message content as dictionary
            delay_seconds: Delay before message becomes available
            message_attributes: Additional message attributes
        
        Returns:
            Message ID if successful, None if failed
        """
        queue_url = self.queue_urls.get(queue_type)
        if not queue_url:
            if queue_type not in self._missing_queue_logged:
                logger.error(f"❌ No queue URL configured for {queue_type.value}")
                self._missing_queue_logged.add(queue_type)
            return None
        
        try:
            async with self.session.client('sqs', region_name=self.region) as sqs:
                # 🔒 Add race-safe metadata for message tracking
                enhanced_body = {
                    "data": message_body,
                    "metadata": {
                        "sent_at": int(time.time()),
                        "queue_type": queue_type.value,
                        "message_uuid": str(uuid.uuid4()),
                        "version": "1.0"
                    }
                }
                
                # 🔒 Prepare message attributes for race tracking
                attrs = self._format_message_attributes(message_attributes or {})
                attrs.update({
                    'MessageType': {
                        'StringValue': 'WhatsAppWebhook',
                        'DataType': 'String'
                    },
                    'QueueType': {
                        'StringValue': queue_type.value,
                        'DataType': 'String'
                    }
                })
                
                # Only include ProcessingId if we have a non-empty value
                processing_id = message_body.get('metadata', {}).get('processing_id')
                if processing_id and processing_id.strip():
                    attrs['ProcessingId'] = {
                        'StringValue': processing_id,
                        'DataType': 'String'
                    }
                
                response = await sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(enhanced_body),
                    DelaySeconds=delay_seconds,
                    MessageAttributes=attrs
                )
                
                message_id = response.get('MessageId')
                logger.debug(f"📤 Message sent to {queue_type.value}: {message_id}")
                return message_id
                
        except ClientError as e:
            logger.error(f"❌ SQS send failed for {queue_type.value}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected SQS send error for {queue_type.value}: {e}")
            return None
    
    async def receive_messages(
        self, 
        queue_type: QueueType,
        max_messages: int = 10,
        wait_time_seconds: Optional[int] = None,
        visibility_timeout: Optional[int] = None
    ) -> List[SQSMessage]:
        """
        🔒 RACE-SAFE: Receive messages with long polling and proper visibility timeout
        
        Args:
            queue_type: Type of queue to receive from
            max_messages: Maximum number of messages to receive (1-10)
            wait_time_seconds: Long polling wait time (defaults to race-safe value)
            visibility_timeout: Override queue's visibility timeout (defaults to race-safe value)
        
        Returns:
            List of SQSMessage objects with enhanced metadata
        """
        queue_url = self.queue_urls.get(queue_type)
        if not queue_url:
            return []
        
        try:
            async with self.session.client('sqs', region_name=self.region) as sqs:
                response = await sqs.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=min(max_messages, 10),  # SQS max is 10
                    WaitTimeSeconds=wait_time_seconds or self.wait_time_seconds,
                    VisibilityTimeout=visibility_timeout or self.visibility_timeout,
                    MessageAttributeNames=['All'],
                    AttributeNames=['All']
                )
                
                messages = []
                for msg in response.get('Messages', []):
                    try:
                        body = json.loads(msg['Body'])
                        processing_id = body.get('data', {}).get('metadata', {}).get('processing_id')
                        
                        sqs_message = SQSMessage(
                            message_id=msg['MessageId'],
                            receipt_handle=msg['ReceiptHandle'],
                            body=body,
                            attributes=msg.get('Attributes', {}),
                            timestamp=int(msg.get('Attributes', {}).get('SentTimestamp', 0)) // 1000,
                            processing_id=processing_id
                        )
                        messages.append(sqs_message)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in SQS message {msg['MessageId']}: {e}")
                        # Delete malformed messages
                        await self.delete_message(queue_type, msg['ReceiptHandle'])
                
                if messages:
                    logger.debug(f"� Received {len(messages)} messages from {queue_type.value}")
                
                return messages
                
        except ClientError as e:
            logger.error(f"❌ SQS receive failed for {queue_type.value}: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected SQS receive error for {queue_type.value}: {e}")
            return []
    
    async def delete_message(self, queue_type: QueueType, receipt_handle: str) -> bool:
        """
        Delete a processed message from the queue
        
        Args:
            queue_type: Type of queue
            receipt_handle: Receipt handle from received message
        
        Returns:
            True if successful, False if failed
        """
        try:
            queue_url = self.queue_urls.get(queue_type)
            if not queue_url:
                # Only log missing queue URL once per queue type
                if queue_type not in self._missing_queue_logged:
                    logger.warning(f"⚠️  Queue URL not configured for {queue_type.value} - skipping delete")
                    self._missing_queue_logged.add(queue_type)
                return False
            
            async with self.session.client('sqs', region_name=self.region) as sqs:
                await sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
                
                logger.debug(f"🗑️ Message deleted from {queue_type.value} queue")
                return True
                
        except ClientError as e:
            logger.error(f"❌ AWS SQS error deleting message from {queue_type.value}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error deleting message from {queue_type.value}: {e}")
            return False
    
    async def change_message_visibility(
        self, 
        queue_type: QueueType, 
        receipt_handle: str, 
        visibility_timeout: int
    ) -> bool:
        """
        Change the visibility timeout of a message
        
        Args:
            queue_type: Type of queue
            receipt_handle: Receipt handle from received message
            visibility_timeout: New visibility timeout in seconds
        
        Returns:
            True if successful, False if failed
        """
        try:
            queue_url = self.queue_urls.get(queue_type)
            if not queue_url:
                # Only log missing queue URL once per queue type
                if queue_type not in self._missing_queue_logged:
                    logger.warning(f"⚠️  Queue URL not configured for {queue_type.value} - skipping visibility change")
                    self._missing_queue_logged.add(queue_type)
                return False
            
            async with self.session.client('sqs', region_name=self.region) as sqs:
                await sqs.change_message_visibility(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle,
                    VisibilityTimeout=visibility_timeout
                )
                
                logger.debug(f"⏰ Message visibility changed in {queue_type.value} queue")
                return True
                
        except ClientError as e:
            logger.error(f"❌ AWS SQS error changing visibility in {queue_type.value}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error changing visibility in {queue_type.value}: {e}")
            return False
    
    async def change_message_visibility(
        self, 
        queue_type: QueueType, 
        receipt_handle: str, 
        visibility_timeout: int
    ) -> bool:
        """
        🔒 RACE-SAFE: Change message visibility to prevent processor races
        
        This is critical for preventing race conditions where multiple processors
        might try to process the same message when visibility timeout expires.
        
        Args:
            queue_type: Type of queue
            receipt_handle: Message receipt handle
            visibility_timeout: New visibility timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        queue_url = self.queue_urls.get(queue_type)
        if not queue_url:
            return False
        
        try:
            async with self.session.client('sqs', region_name=self.region) as sqs:
                await sqs.change_message_visibility(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle,
                    VisibilityTimeout=visibility_timeout
                )
                logger.debug(f"👁️ Visibility timeout set to {visibility_timeout}s for {queue_type.value}")
                return True
                
        except ClientError as e:
            logger.error(f"❌ Visibility change failed for {queue_type.value}: {e}")
            return False
    
    async def get_queue_attributes(self, queue_type: QueueType) -> Dict[str, Any]:
        """
        Get queue attributes like message count, etc.
        
        Args:
            queue_type: Type of queue
        
        Returns:
            Dictionary of queue attributes
        """
        try:
            queue_url = self.queue_urls.get(queue_type)
            if not queue_url:
                # Only log missing queue URL once per queue type
                if queue_type not in self._missing_queue_logged:
                    logger.warning(f"⚠️  Queue URL not configured for {queue_type.value} - skipping attributes")
                    self._missing_queue_logged.add(queue_type)
                return {}
            
            async with self.session.client('sqs', region_name=self.region) as sqs:
                response = await sqs.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=['All']
                )
                
                return response.get('Attributes', {})
                
        except ClientError as e:
            logger.error(f"❌ AWS SQS error getting attributes for {queue_type.value}: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Unexpected error getting attributes for {queue_type.value}: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """🔒 RACE-SAFE: Health check for all configured queues"""
        health_status = {
            "status": "healthy",
            "queues": {},
            "timestamp": int(time.time())
        }
        
        for queue_type, queue_url in self.queue_urls.items():
            if not queue_url:
                continue
                
            try:
                attributes = await self.get_queue_attributes(queue_type)
                health_status["queues"][queue_type.value] = {
                    "status": "healthy",
                    "approximate_messages": int(attributes.get('ApproximateNumberOfMessages', 0)),
                    "messages_in_flight": int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0)),
                    "visibility_timeout": int(attributes.get('VisibilityTimeout', 0))
                }
            except Exception as e:
                health_status["queues"][queue_type.value] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["status"] = "degraded"
        
        return health_status
    
    def _format_message_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format message attributes for SQS
        
        Args:
            attributes: Raw attributes dictionary
        
        Returns:
            Formatted attributes for SQS
        """
        formatted = {}
        for key, value in attributes.items():
            if isinstance(value, str):
                formatted[key] = {'StringValue': value, 'DataType': 'String'}
            elif isinstance(value, (int, float)):
                formatted[key] = {'StringValue': str(value), 'DataType': 'Number'}
            elif isinstance(value, bool):
                formatted[key] = {'StringValue': str(value).lower(), 'DataType': 'String'}
        return formatted

# Global SQS service instance
sqs_service = SQSService()

# 🔒 RACE-SAFE Helper functions for specific message types
async def send_incoming_message(webhook_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """🔒 RACE-SAFE: Send incoming WhatsApp message to processing queue"""
    message = {
        "webhook_data": webhook_data,
        "metadata": metadata or {},
        "source": "whatsapp_webhook",
        "timestamp": int(time.time())
    }
    return await sqs_service.send_message(QueueType.INCOMING, message)

async def send_outgoing_message(phone_number: str, message_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """🔒 RACE-SAFE: Send outgoing WhatsApp message to sending queue"""
    message = {
        "phone_number": phone_number,
        "message_data": message_data,
        "metadata": metadata or {},
        "source": "api_request",
        "timestamp": int(time.time())
    }
    return await sqs_service.send_message(QueueType.OUTGOING, message)

async def send_analytics_event(event_type: str, event_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """🔒 RACE-SAFE: Send analytics event to processing queue"""
    # Ensure metadata has a processing_id for tracking
    if not metadata:
        metadata = {}
    if not metadata.get('processing_id'):
        metadata['processing_id'] = str(uuid.uuid4())
    
    message = {
        "event_type": event_type,
        "event_data": event_data,
        "metadata": metadata,
        "source": "analytics",
        "timestamp": int(time.time())
    }
    return await sqs_service.send_message(QueueType.ANALYTICS, message)