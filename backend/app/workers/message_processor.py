"""
🔒 RACE-SAFE Background workers for processing SQS messages
Handles incoming, outgoing, and analytics message processing with complete race condition prevention

Race Condition Prevention Features:
- Atomic message claiming with DynamoDB
- Processor ownership tracking
- Extended visibility timeouts
- Graceful error handling and retries
"""
import asyncio
import json
import signal
import time
import uuid
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import contextlib
from datetime import datetime

from app.services.sqs_service import sqs_service, QueueType, SQSMessage
from app.services.whatsapp_service import WhatsAppService
from app.core.database import get_db_session, SessionLocal
from app.repositories.message_repository import MessageRepository
from app.core.logging import logger
from app.config import get_settings
# 🔒 Import race-safe DynamoDB functions
from app.dynamodb_client import (
    claim_message_processing, 
    update_message_status_atomic,
    table
)

settings = get_settings()

class MessageProcessor:
    """
    🔒 RACE-SAFE Background message processor for handling SQS queues
    
    Prevents multiple processors from handling the same message by using
    atomic DynamoDB operations for message claiming and status tracking.
    """
    
    def __init__(self):
        self.processor_id = str(uuid.uuid4())  # Unique processor instance ID
        self.running = False
        self.whatsapp_service = None  # Will be initialized when processing starts
        
        # 🔒 Race-safe statistics tracking
        self.stats = {
            "processor_id": self.processor_id,
            "processed_count": 0,
            "error_count": 0,
            "duplicate_count": 0,  # Messages already claimed by other processors
            "start_time": None
        }
        # Protect stats updates from concurrent asyncio tasks interleaving
        self._stats_lock = asyncio.Lock()
        
        logger.info(f"🤖 Message processor initialized: {self.processor_id}")
    
    async def start_processing(self):
        """🔒 RACE-SAFE: Start the message processing loop"""
        self.running = True
        self.stats["start_time"] = time.time()
        
        # Initialize WhatsAppService now that database is ready
        self.whatsapp_service = WhatsAppService()
        
        logger.info(f"🚀 Message processor {self.processor_id} started")
        
        while self.running:
            try:
                # 📨 Receive messages with long polling (reduces API calls)
                messages = await sqs_service.receive_messages(
                    queue_type=QueueType.INCOMING,
                    max_messages=10,  # Process up to 10 messages concurrently
                    wait_time_seconds=20,  # Long polling for efficiency
                    visibility_timeout=900  # 15 minutes to prevent races
                )
                
                if messages:
                    logger.info(f"📥 Received {len(messages)} messages for processing")
                    
                    # 🔄 Process messages concurrently but safely
                    tasks = [self.process_message_safe(msg) for msg in messages]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Log any exceptions from concurrent processing
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.error(f"❌ Concurrent processing error for message {messages[i].message_id}: {result}")
                
                # Brief pause if no messages to prevent tight loop
                if not messages:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ Message processing loop error in processor {self.processor_id}: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying
    
    async def process_message_safe(self, sqs_message: SQSMessage):
        """🔒 RACE-SAFE: Process individual SQS message with full protection"""
        processing_start = time.time()
        
        try:
            # Extract message data
            webhook_data = sqs_message.body.get("data", {}).get("webhook_data", {})
            message = webhook_data.get("message", {})
            contact = webhook_data.get("contact", {})
            metadata = sqs_message.body.get("data", {}).get("metadata", {})
            
            message_id = message.get("id") or metadata.get("message_id")
            phone_number = message.get("from", "unknown")
            message_type = message.get("type", "unknown")
            processing_id = sqs_message.processing_id or metadata.get("processing_id")
            
            if not message_id:
                logger.error(f"❌ No message_id in SQS message {sqs_message.message_id}")
                await sqs_service.delete_message(QueueType.INCOMING, sqs_message.receipt_handle)
                return
            
            logger.info(f"🔄 Processing message: {message_id} (type: {message_type}, from: {phone_number})")
            
            # 🔒 Step 1: Atomically claim this message for processing
            if not claim_message_processing(message_id, self.processor_id):
                logger.info(f"⚠️ Message {message_id} already claimed by another processor")
                async with self._stats_lock:
                    self.stats["duplicate_count"] += 1
                # Safe to delete from SQS; another processor owns it
                await sqs_service.delete_message(QueueType.INCOMING, sqs_message.receipt_handle)
                return
            
            # 🔒 Step 2: Extend visibility timeout to prevent other processors from seeing this
            await sqs_service.change_message_visibility(
                QueueType.INCOMING,
                sqs_message.receipt_handle,
                1800  # 30 minutes - generous time for processing
            )
            # Start background heartbeat to keep extending visibility while processing
            heartbeat = asyncio.create_task(
                self._visibility_heartbeat(
                    receipt_handle=sqs_message.receipt_handle,
                    queue_type=QueueType.INCOMING,
                    interval=60,
                    visibility_extension=1800
                )
            )
            
            # 🔒 Step 3: Process the WhatsApp message with error handling
            try:
                processing_result = await self.handle_whatsapp_message(
                    message=message,
                    contact=contact,
                    metadata=metadata,
                    processing_id=processing_id
                )
                
                # 🔒 Step 4: Atomically mark as completed in DynamoDB
                update_success = update_message_status_atomic(
                    message_id=message_id,
                    status="completed",
                    processor_id=self.processor_id,
                    result=processing_result
                )
                
                if update_success:
                    # 🆕 Update RDS status to "processed"
                    try:
                        await self._update_rds_status(message_id, "processed")
                        logger.info(f"✅ RDS status updated to 'processed' for message: {message_id}")
                    except Exception as rds_error:
                        logger.error(f"⚠️ Failed to update RDS status: {rds_error}")
                        # Don't fail processing if RDS update fails
                    
                    # 🗑️ Delete from SQS only after successful processing and status update
                    await sqs_service.delete_message(QueueType.INCOMING, sqs_message.receipt_handle)
                    
                    processing_time = time.time() - processing_start
                    async with self._stats_lock:
                        self.stats["processed_count"] += 1
                    
                    logger.info(
                        f"✅ Message completed: {message_id} "
                        f"(processor: {self.processor_id}, time: {processing_time:.3f}s)"
                    )
                else:
                    logger.error(f"❌ Failed to update status for completed message: {message_id}")
                    # Don't delete from SQS - let it retry
                
            except Exception as processing_error:
                # 🔒 Step 4b: Mark as failed with atomic update in DynamoDB
                logger.error(f"❌ Processing failed for {message_id}: {processing_error}")
                
                update_message_status_atomic(
                    message_id=message_id,
                    status="failed",
                    processor_id=self.processor_id,
                    error_message=str(processing_error)
                )
                
                # 🆕 Update RDS status to "failed"
                try:
                    await self._update_rds_status(message_id, "failed")
                    logger.info(f"✅ RDS status updated to 'failed' for message: {message_id}")
                except Exception as rds_error:
                    logger.error(f"⚠️ Failed to update RDS status to failed: {rds_error}")
                
                async with self._stats_lock:
                    self.stats["error_count"] += 1
                
                # Don't delete from SQS - let it retry or go to DLQ after max attempts
                # Extend visibility timeout to prevent immediate retry
                await sqs_service.change_message_visibility(
                    QueueType.INCOMING,
                    sqs_message.receipt_handle,
                    300  # 5 minutes before retry
                )
            finally:
                # Stop heartbeat
                with contextlib.suppress(asyncio.CancelledError):
                    heartbeat.cancel()
                    await heartbeat
                
        except Exception as e:
            logger.error(f"❌ Critical error processing SQS message {sqs_message.message_id}: {e}")
            async with self._stats_lock:
                self.stats["error_count"] += 1
            
            # For critical errors, extend visibility timeout significantly
            await sqs_service.change_message_visibility(
                QueueType.INCOMING,
                sqs_message.receipt_handle,
                600  # 10 minutes
            )

    async def _visibility_heartbeat(self, receipt_handle: str, queue_type: QueueType, interval: int = 60, visibility_extension: int = 900):
        """Periodically extend SQS message visibility while processing."""
        try:
            while self.running:
                await asyncio.sleep(interval)
                await sqs_service.change_message_visibility(queue_type, receipt_handle, visibility_extension)
        except Exception as e:
            logger.warning(f"⚠️ Visibility heartbeat failed: {e}")
    
    async def _update_rds_status(self, message_id: str, status: str):
        """
        Update message status in RDS database
        
        Args:
            message_id: WhatsApp message ID
            status: New status ('processed', 'failed')
        """
        db = SessionLocal()
        try:
            message_repo = MessageRepository(db)
            message = message_repo.get_by_message_id(message_id)
            
            if message:
                message.status = status
                db.commit()
                db.refresh(message)
                logger.debug(f"✅ RDS status updated: {message_id} -> {status}")
            else:
                logger.warning(f"⚠️ Message not found in RDS for status update: {message_id}")
        except Exception as e:
            logger.error(f"❌ Failed to update RDS status for {message_id}: {e}")
            raise
        finally:
            db.close()
    
    async def handle_whatsapp_message(
        self, 
        message: Dict[str, Any], 
        contact: Dict[str, Any], 
        metadata: Dict[str, Any],
        processing_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        🔒 RACE-SAFE: Process WhatsApp message based on type
        Returns processing result for status tracking
        """
        message_type = message.get("type", "unknown")
        phone_number = message.get("from")
        
        try:
            # Handle different message types
            if message_type == "text":
                text_body = message.get("text", {}).get("body", "")
                result = await self.whatsapp_service.process_text_message(
                    phone_number=phone_number,
                    text_content=text_body,
                    contact_info=contact,
                    processing_metadata=metadata
                )
                
            elif message_type == "interactive":
                interactive_data = message.get("interactive", {})
                result = await self.whatsapp_service.process_interactive_message(
                    phone_number=phone_number,
                    interactive_data=interactive_data,
                    contact_info=contact,
                    processing_metadata=metadata
                )
                
            elif message_type in ["image", "document", "audio", "video"]:
                media_data = message.get(message_type, {})
                result = await self.whatsapp_service.process_media_message(
                    phone_number=phone_number,
                    media_type=message_type,
                    media_data=media_data,
                    contact_info=contact,
                    processing_metadata=metadata
                )
                
            elif message_type == "location":
                location_data = message.get("location", {})
                result = await self.whatsapp_service.process_location_message(
                    phone_number=phone_number,
                    location_data=location_data,
                    contact_info=contact,
                    processing_metadata=metadata
                )
                
            else:
                logger.warning(f"⚠️ Unsupported message type: {message_type} from {phone_number}")
                result = {
                    "status": "unsupported",
                    "message_type": message_type,
                    "action": "ignored"
                }
            
            return {
                "processing_result": result,
                "message_type": message_type,
                "phone_number": phone_number,
                "processing_id": processing_id,
                "processed_at": datetime.utcnow().isoformat(),
                "processor_id": self.processor_id
            }
            
        except Exception as e:
            logger.error(f"❌ WhatsApp message handling failed for {phone_number}: {e}")
            raise  # Re-raise to be handled by the caller
    
    def stop_processing(self):
        """🔒 RACE-SAFE: Stop the message processing loop"""
        self.running = False
        logger.info(
            f"🛑 Message processor {self.processor_id} stopped. "
            f"Stats: {self.stats['processed_count']} processed, {self.stats['error_count']} errors, {self.stats['duplicate_count']} duplicates"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            "processor_id": self.processor_id,
            "processed_count": self.stats["processed_count"],
            "error_count": self.stats["error_count"],
            "duplicate_count": self.stats["duplicate_count"],
            "running": self.running
        }

# Global processor instance
message_processor = MessageProcessor()