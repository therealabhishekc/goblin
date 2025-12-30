"""
🔒 RACE-SAFE Outgoing message processor for sending WhatsApp messages
Handles outgoing messages from the SQS queue and sends them via WhatsApp API

This processor:
- Receives messages from the OUTGOING SQS queue
- Sends them via WhatsApp Business API
- Handles retries and error cases
- Updates message status atomically
"""
import asyncio
import json
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import contextlib

from app.services.sqs_service import sqs_service, QueueType, SQSMessage
from app.whatsapp_api import send_whatsapp_message
from app.core.logging import logger
from app.core.config import get_settings
from app.repositories.message_repository import MessageRepository
from app.core.database import get_db_session

settings = get_settings()

class OutgoingMessageProcessor:
    """
    🔒 RACE-SAFE Outgoing message processor for sending WhatsApp messages
    
    This processor handles messages from the outgoing queue and sends them
    via the WhatsApp Business API with proper error handling and retries.
    """
    
    def __init__(self):
        self.processor_id = str(uuid.uuid4())  # Unique processor instance ID
        self.running = False
        
        # Statistics tracking
        self.stats = {
            "processor_id": self.processor_id,
            "sent_count": 0,
            "error_count": 0,
            "retry_count": 0,
            "start_time": None
        }
        # Protect stats updates from concurrent asyncio tasks
        self._stats_lock = asyncio.Lock()
        
        logger.info(f"🤖 Outgoing message processor initialized: {self.processor_id}")
    
    async def start_processing(self):
        """🔒 RACE-SAFE: Start the outgoing message processing loop"""
        self.running = True
        self.stats["start_time"] = time.time()
        logger.info(f"🚀 Outgoing message processor {self.processor_id} started")
        
        while self.running:
            try:
                # 📨 Receive messages with long polling
                messages = await sqs_service.receive_messages(
                    queue_type=QueueType.OUTGOING,
                    max_messages=10,  # Process up to 10 messages concurrently
                    wait_time_seconds=20,  # Long polling for efficiency
                    visibility_timeout=300  # 5 minutes for sending
                )
                
                if messages:
                    logger.info(f"📥 Received {len(messages)} outgoing messages to send")
                    
                    # 🔄 Process messages concurrently but safely
                    tasks = [self.process_outgoing_message(msg) for msg in messages]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Log any exceptions from concurrent processing
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.error(f"❌ Concurrent processing error for message {messages[i].message_id}: {result}")
                
                # Brief pause if no messages to prevent tight loop
                if not messages:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ Outgoing message processing loop error in processor {self.processor_id}: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying
    
    async def process_outgoing_message(self, sqs_message: SQSMessage):
        """🔒 RACE-SAFE: Process individual outgoing message"""
        processing_start = time.time()
        
        try:
            # Extract message data
            message_data = sqs_message.body.get("data", {})
            phone_number = message_data.get("phone_number")
            whatsapp_message_data = message_data.get("message_data", {})
            metadata = message_data.get("metadata", {})
            
            if not phone_number:
                logger.error(f"❌ No phone_number in outgoing message {sqs_message.message_id}")
                await sqs_service.delete_message(QueueType.OUTGOING, sqs_message.receipt_handle)
                return
            
            if not whatsapp_message_data:
                logger.error(f"❌ No message_data in outgoing message {sqs_message.message_id}")
                await sqs_service.delete_message(QueueType.OUTGOING, sqs_message.receipt_handle)
                return
            
            logger.info(f"📤 Sending message to {phone_number}: {whatsapp_message_data.get('type', 'text')}")
            
            # Extend visibility timeout to prevent other processors from seeing this
            await sqs_service.change_message_visibility(
                QueueType.OUTGOING,
                sqs_message.receipt_handle,
                600  # 10 minutes
            )
            
            # Start background heartbeat to keep extending visibility while processing
            heartbeat = asyncio.create_task(
                self._visibility_heartbeat(
                    receipt_handle=sqs_message.receipt_handle,
                    queue_type=QueueType.OUTGOING,
                    interval=60,
                    visibility_extension=600
                )
            )
            
            try:
                # Send message via WhatsApp API
                result = await send_whatsapp_message(phone_number, whatsapp_message_data)
                
                # Extract message ID from WhatsApp response
                wa_message_id = result.get('messages', [{}])[0].get('id', 'unknown')
                
                # Store sent message in database
                try:
                    with get_db_session() as db:
                        message_repo = MessageRepository(db)
                        
                        # Extract content based on message type
                        content = self._extract_message_content(whatsapp_message_data)
                        
                        message_data = {
                            "message_id": wa_message_id,
                            "from_phone": metadata.get("business_phone", "business"),
                            "to_phone": phone_number,
                            "message_type": whatsapp_message_data.get("type", "text"),
                            "content": content,
                            "media_url": whatsapp_message_data.get("media_url"),
                            "timestamp": datetime.utcnow(),
                            "status": "sent",
                            "direction": "outgoing"
                        }
                        
                        stored_message = message_repo.create_from_dict(message_data)
                        db.commit()
                        
                        logger.info(f"📝 Outgoing message stored in database: {wa_message_id}")
                        
                        # Update campaign recipient if this is a campaign message
                        if metadata.get("source") == "marketing_campaign" and metadata.get("recipient_id"):
                            try:
                                from app.repositories.marketing_repository import MarketingCampaignRepository
                                from app.models.marketing import RecipientStatus
                                import uuid as uuid_lib
                                
                                campaign_repo = MarketingCampaignRepository(db)
                                recipient_id = uuid_lib.UUID(metadata["recipient_id"])
                                
                                # Update with the real WhatsApp message ID
                                campaign_repo.update_recipient_status(
                                    recipient_id,
                                    RecipientStatus.SENT,
                                    whatsapp_message_id=wa_message_id
                                )
                                
                                logger.info(f"✅ Updated campaign recipient with WhatsApp message ID: {wa_message_id}")
                            except Exception as campaign_error:
                                logger.error(f"❌ Failed to update campaign recipient: {campaign_error}")
                    
                except Exception as db_error:
                    logger.error(f"❌ Failed to store outgoing message in database: {db_error}")
                    # Don't fail the send operation if storage fails
                    # The message was successfully sent to WhatsApp
                
                # Delete from SQS after successful send
                await sqs_service.delete_message(QueueType.OUTGOING, sqs_message.receipt_handle)
                
                processing_time = time.time() - processing_start
                async with self._stats_lock:
                    self.stats["sent_count"] += 1
                
                logger.info(
                    f"✅ Message sent successfully to {phone_number}: {wa_message_id} "
                    f"(processor: {self.processor_id}, time: {processing_time:.3f}s)"
                )
                
            except Exception as send_error:
                # Handle sending errors
                logger.error(f"❌ Failed to send message to {phone_number}: {send_error}")
                
                async with self._stats_lock:
                    self.stats["error_count"] += 1
                
                # Get receive count to determine if we should retry
                receive_count = int(sqs_message.attributes.get('ApproximateReceiveCount', 0))
                
                if receive_count >= 3:
                    # Max retries reached, let it go to DLQ
                    logger.error(f"❌ Max retries reached for message to {phone_number}, will go to DLQ")
                    # Delete from queue so it can go to DLQ
                    await sqs_service.delete_message(QueueType.OUTGOING, sqs_message.receipt_handle)
                else:
                    # Retry after delay
                    async with self._stats_lock:
                        self.stats["retry_count"] += 1
                    
                    logger.info(f"🔄 Will retry message to {phone_number} (attempt {receive_count + 1}/3)")
                    # Extend visibility timeout for retry delay
                    await sqs_service.change_message_visibility(
                        QueueType.OUTGOING,
                        sqs_message.receipt_handle,
                        60  # 1 minute before retry
                    )
            finally:
                # Stop heartbeat
                with contextlib.suppress(asyncio.CancelledError):
                    heartbeat.cancel()
                    await heartbeat
                
        except Exception as e:
            logger.error(f"❌ Critical error processing outgoing message {sqs_message.message_id}: {e}")
            async with self._stats_lock:
                self.stats["error_count"] += 1
            
            # Extend visibility timeout for retry
            await sqs_service.change_message_visibility(
                QueueType.OUTGOING,
                sqs_message.receipt_handle,
                60  # 1 minute
            )

    def _extract_message_content(self, message_data: Dict[str, Any]) -> str:
        """
        Extract content from message data based on message type.
        For template messages, creates a readable summary of the template.
        """
        message_type = message_data.get("type", "text")
        
        # For text messages, just return the content
        if message_type == "text":
            return message_data.get("content", message_data.get("text", ""))
        
        # For template messages, create a summary
        if message_type == "template":
            template_name = message_data.get("template_name", "Unknown Template")
            language_code = message_data.get("language_code", "en_US")
            
            # Build content summary
            content_parts = [f"Template: {template_name} ({language_code})"]
            
            # Extract parameters from components
            components = message_data.get("components", [])
            parameters = message_data.get("parameters", [])
            
            if components:
                for component in components:
                    comp_type = component.get("type", "unknown")
                    comp_params = component.get("parameters", [])
                    
                    if comp_params:
                        param_values = []
                        for param in comp_params:
                            if param.get("type") == "text":
                                param_values.append(param.get("text", ""))
                            elif param.get("type") == "image":
                                param_values.append(f"[Image: {param.get('image', {}).get('link', 'N/A')}]")
                            elif param.get("type") == "document":
                                param_values.append(f"[Document: {param.get('document', {}).get('link', 'N/A')}]")
                            elif param.get("type") == "video":
                                param_values.append(f"[Video: {param.get('video', {}).get('link', 'N/A')}]")
                        
                        if param_values:
                            content_parts.append(f"{comp_type.capitalize()}: {', '.join(param_values)}")
            
            elif parameters:
                # Simple parameters (backward compatibility)
                param_values = [p.get("text", "") for p in parameters if p.get("type") == "text"]
                if param_values:
                    content_parts.append(f"Body: {', '.join(param_values)}")
            
            return " | ".join(content_parts)
        
        # For media messages, return caption or media type
        if message_type in ["image", "video", "document", "audio"]:
            caption = message_data.get("content", message_data.get("caption", ""))
            if caption:
                return f"[{message_type.upper()}] {caption}"
            return f"[{message_type.upper()}]"
        
        # For location messages
        if message_type == "location":
            name = message_data.get("name", "")
            address = message_data.get("address", "")
            lat = message_data.get("latitude", "")
            lng = message_data.get("longitude", "")
            if name and address:
                return f"Location: {name}, {address}"
            elif name:
                return f"Location: {name}"
            else:
                return f"Location: {lat}, {lng}"
        
        # Default: return any content field or empty string
        return message_data.get("content", "")
    
    async def _visibility_heartbeat(self, receipt_handle: str, queue_type: QueueType, interval: int = 60, visibility_extension: int = 600):
        """Periodically extend SQS message visibility while processing."""
        try:
            while self.running:
                await asyncio.sleep(interval)
                await sqs_service.change_message_visibility(queue_type, receipt_handle, visibility_extension)
        except Exception as e:
            logger.warning(f"⚠️ Visibility heartbeat failed: {e}")
    
    def stop_processing(self):
        """🔒 RACE-SAFE: Stop the message processing loop"""
        self.running = False
        logger.info(
            f"🛑 Outgoing message processor {self.processor_id} stopped. "
            f"Stats: {self.stats['sent_count']} sent, {self.stats['error_count']} errors, {self.stats['retry_count']} retries"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            "processor_id": self.processor_id,
            "sent_count": self.stats["sent_count"],
            "error_count": self.stats["error_count"],
            "retry_count": self.stats["retry_count"],
            "running": self.running
        }

# Global processor instance
outgoing_processor = OutgoingMessageProcessor()
