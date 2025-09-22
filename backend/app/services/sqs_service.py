"""
SQS Service Layer for WhatsApp Business API
Handles all SQS operations with async/await support
"""
import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

import aioboto3
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class QueueType(Enum):
    """Enum for different queue types"""
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    ANALYTICS = "analytics"

@dataclass
class SQSMessage:
    """SQS Message data class"""
    message_id: str
    receipt_handle: str
    body: Dict[str, Any]
    attributes: Dict[str, Any]
    timestamp: int

class SQSService:
    """
    SQS Service for handling message queuing operations
    Provides async methods for sending, receiving, and managing messages
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
    
    async def send_message(
        self, 
        queue_type: QueueType, 
        message_body: Dict[str, Any],
        delay_seconds: int = 0,
        message_attributes: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Send a message to the specified SQS queue
        
        Args:
            queue_type: Type of queue to send to
            message_body: Message content as dictionary
            delay_seconds: Delay before message becomes available
            message_attributes: Additional message attributes
        
        Returns:
            Message ID if successful, None if failed
        """
        try:
            queue_url = self.queue_urls.get(queue_type)
            if not queue_url:
                logger.error(f"❌ Queue URL not configured for {queue_type.value}")
                return None
            
            # Prepare message
            message = {
                "timestamp": int(time.time()),
                "queue_type": queue_type.value,
                "data": message_body
            }
            
            async with self.session.client('sqs', region_name=self.region) as sqs:
                params = {
                    'QueueUrl': queue_url,
                    'MessageBody': json.dumps(message),
                }
                
                if delay_seconds > 0:
                    params['DelaySeconds'] = delay_seconds
                
                if message_attributes:
                    params['MessageAttributes'] = self._format_message_attributes(message_attributes)
                
                response = await sqs.send_message(**params)
                
                message_id = response.get('MessageId')
                logger.info(f"✅ Message sent to {queue_type.value} queue: {message_id}")
                return message_id
                
        except ClientError as e:
            logger.error(f"❌ AWS SQS error sending message to {queue_type.value}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error sending message to {queue_type.value}: {e}")
            return None
    
    async def receive_messages(
        self, 
        queue_type: QueueType,
        max_messages: int = 10,
        wait_time_seconds: int = 20,
        visibility_timeout: Optional[int] = None
    ) -> List[SQSMessage]:
        """
        Receive messages from the specified SQS queue
        
        Args:
            queue_type: Type of queue to receive from
            max_messages: Maximum number of messages to receive (1-10)
            wait_time_seconds: Long polling wait time (0-20)
            visibility_timeout: Override queue's visibility timeout
        
        Returns:
            List of SQSMessage objects
        """
        try:
            queue_url = self.queue_urls.get(queue_type)
            if not queue_url:
                logger.error(f"❌ Queue URL not configured for {queue_type.value}")
                return []
            
            async with self.session.client('sqs', region_name=self.region) as sqs:
                params = {
                    'QueueUrl': queue_url,
                    'MaxNumberOfMessages': min(max_messages, 10),  # AWS limit is 10
                    'WaitTimeSeconds': min(wait_time_seconds, 20),  # AWS limit is 20
                    'MessageAttributeNames': ['All'],
                    'AttributeNames': ['All']
                }
                
                if visibility_timeout:
                    params['VisibilityTimeout'] = visibility_timeout
                
                response = await sqs.receive_message(**params)
                
                messages = []
                for msg in response.get('Messages', []):
                    try:
                        body = json.loads(msg['Body'])
                        sqs_message = SQSMessage(
                            message_id=msg['MessageId'],
                            receipt_handle=msg['ReceiptHandle'],
                            body=body,
                            attributes=msg.get('Attributes', {}),
                            timestamp=body.get('timestamp', int(time.time()))
                        )
                        messages.append(sqs_message)
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Failed to parse message body: {e}")
                        # Delete malformed message
                        await self.delete_message(queue_type, msg['ReceiptHandle'])
                
                if messages:
                    logger.debug(f"📨 Received {len(messages)} messages from {queue_type.value} queue")
                
                return messages
                
        except ClientError as e:
            logger.error(f"❌ AWS SQS error receiving messages from {queue_type.value}: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error receiving messages from {queue_type.value}: {e}")
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
                logger.error(f"❌ Queue URL not configured for {queue_type.value}")
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
                logger.error(f"❌ Queue URL not configured for {queue_type.value}")
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
                logger.error(f"❌ Queue URL not configured for {queue_type.value}")
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
        """
        Check health of all SQS queues
        
        Returns:
            Health status dictionary
        """
        health_status = {
            "sqs_service": "healthy",
            "queues": {},
            "timestamp": int(time.time())
        }
        
        for queue_type in QueueType:
            try:
                attributes = await self.get_queue_attributes(queue_type)
                if attributes:
                    health_status["queues"][queue_type.value] = {
                        "status": "healthy",
                        "approximate_messages": attributes.get('ApproximateNumberOfMessages', '0'),
                        "approximate_messages_not_visible": attributes.get('ApproximateNumberOfMessagesNotVisible', '0'),
                        "approximate_messages_delayed": attributes.get('ApproximateNumberOfMessagesDelayed', '0')
                    }
                else:
                    health_status["queues"][queue_type.value] = {
                        "status": "unhealthy",
                        "error": "Unable to get queue attributes"
                    }
            except Exception as e:
                health_status["queues"][queue_type.value] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Overall health based on queue health
        unhealthy_queues = [q for q in health_status["queues"].values() if q["status"] != "healthy"]
        if unhealthy_queues:
            health_status["sqs_service"] = "degraded" if len(unhealthy_queues) < len(QueueType) else "unhealthy"
        
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

# Helper functions for specific message types
async def send_incoming_message(webhook_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Send incoming WhatsApp message to processing queue"""
    message = {
        "webhook_data": webhook_data,
        "metadata": metadata or {},
        "source": "whatsapp_webhook"
    }
    return await sqs_service.send_message(QueueType.INCOMING, message)

async def send_outgoing_message(phone_number: str, message_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Send outgoing WhatsApp message to sending queue"""
    message = {
        "phone_number": phone_number,
        "message_data": message_data,
        "metadata": metadata or {},
        "source": "api_request"
    }
    return await sqs_service.send_message(QueueType.OUTGOING, message)

async def send_analytics_event(event_type: str, event_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Send analytics event to processing queue"""
    message = {
        "event_type": event_type,
        "event_data": event_data,
        "metadata": metadata or {},
        "source": "analytics"
    }
    return await sqs_service.send_message(QueueType.ANALYTICS, message)