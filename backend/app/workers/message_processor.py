"""
Background workers for processing SQS messages
Handles incoming, outgoing, and analytics message processing
"""
import asyncio
import json
import logging
import signal
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from app.services.sqs_service import sqs_service, QueueType, SQSMessage
from app.services.whatsapp_service import WhatsAppService
from app.core.database import get_db_session
from app.core.logging import logger
from app.config import get_settings

settings = get_settings()

class MessageProcessor:
    """
    Background message processor for handling SQS queues
    """
    
    def __init__(self):
        self.running = False
        self.workers = {}
        self.stats = {
            "incoming_processed": 0,
            "outgoing_processed": 0,
            "analytics_processed": 0,
            "errors": 0,
            "start_time": None
        }
    
    async def start(self):
        """Start all background workers"""
        if self.running:
            logger.warning("⚠️  Message processor already running")
            return
        
        self.running = True
        self.stats["start_time"] = time.time()
        logger.info("🚀 Starting message processor workers")
        
        # Create worker tasks
        self.workers = {
            "incoming": asyncio.create_task(self._process_incoming_messages()),
            "outgoing": asyncio.create_task(self._process_outgoing_messages()),
            "analytics": asyncio.create_task(self._process_analytics_messages()),
            "health_monitor": asyncio.create_task(self._health_monitor())
        }
        
        try:
            # Wait for all workers to complete
            await asyncio.gather(*self.workers.values())
        except asyncio.CancelledError:
            logger.info("🛑 Message processor workers cancelled")
        except Exception as e:
            logger.error(f"❌ Error in message processor: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop all background workers gracefully"""
        if not self.running:
            return
        
        logger.info("🛑 Stopping message processor workers...")
        self.running = False
        
        # Cancel all worker tasks
        for name, task in self.workers.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"✅ Worker {name} stopped")
        
        # Log final stats
        uptime = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        logger.info(f"📊 Final stats - Uptime: {uptime:.1f}s, "
                   f"Incoming: {self.stats['incoming_processed']}, "
                   f"Outgoing: {self.stats['outgoing_processed']}, "
                   f"Analytics: {self.stats['analytics_processed']}, "
                   f"Errors: {self.stats['errors']}")
    
    async def _process_incoming_messages(self):
        """Process incoming WhatsApp messages from SQS"""
        logger.info("📨 Starting incoming message worker")
        
        while self.running:
            try:
                # Receive messages from incoming queue
                messages = await sqs_service.receive_messages(
                    QueueType.INCOMING,
                    max_messages=10,
                    wait_time_seconds=20
                )
                
                if not messages:
                    continue
                
                logger.debug(f"📥 Processing {len(messages)} incoming messages")
                
                # Process messages concurrently
                tasks = [
                    self._process_single_incoming_message(msg) 
                    for msg in messages
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
                
            except Exception as e:
                logger.error(f"❌ Error in incoming message worker: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _process_single_incoming_message(self, message: SQSMessage):
        """Process a single incoming message"""
        try:
            webhook_data = message.body.get("data", {}).get("webhook_data", {})
            metadata = message.body.get("data", {}).get("metadata", {})
            
            if not webhook_data:
                logger.error("❌ No webhook data in message")
                await sqs_service.delete_message(QueueType.INCOMING, message.receipt_handle)
                return
            
            # Process with WhatsApp service
            with get_db_session() as db:
                with WhatsAppService(db) as service:
                    result = service.process_incoming_message(webhook_data)
                    
                    if result["status"] in ["success", "duplicate"]:
                        # Message processed successfully
                        await sqs_service.delete_message(QueueType.INCOMING, message.receipt_handle)
                        self.stats["incoming_processed"] += 1
                        logger.debug(f"✅ Processed incoming message: {result['status']}")
                        
                        # Send analytics event for successful processing
                        if result["status"] == "success":
                            await self._send_analytics_event("message_processed", {
                                "message_id": result.get("message_id"),
                                "processing_time": time.time() - message.timestamp,
                                "source": "sqs_worker",
                                "metadata": metadata
                            })
                    else:
                        # Processing failed, let it retry
                        logger.warning(f"⚠️  Message processing failed, will retry: {result}")
                        self.stats["errors"] += 1
            
        except Exception as e:
            logger.error(f"❌ Error processing incoming message: {e}")
            self.stats["errors"] += 1
            # Don't delete the message, let it retry
    
    async def _process_outgoing_messages(self):
        """Process outgoing WhatsApp messages from SQS"""
        logger.info("📤 Starting outgoing message worker")
        
        while self.running:
            try:
                # Receive messages from outgoing queue
                messages = await sqs_service.receive_messages(
                    QueueType.OUTGOING,
                    max_messages=5,  # Fewer concurrent outgoing messages
                    wait_time_seconds=20
                )
                
                if not messages:
                    continue
                
                logger.debug(f"📤 Processing {len(messages)} outgoing messages")
                
                # Process messages with some delay to respect rate limits
                for message in messages:
                    await self._process_single_outgoing_message(message)
                    await asyncio.sleep(0.1)  # Small delay between sends
                
            except Exception as e:
                logger.error(f"❌ Error in outgoing message worker: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(5)
    
    async def _process_single_outgoing_message(self, message: SQSMessage):
        """Process a single outgoing message"""
        try:
            data = message.body.get("data", {})
            phone_number = data.get("phone_number")
            message_data = data.get("message_data", {})
            metadata = data.get("metadata", {})
            
            if not phone_number or not message_data:
                logger.error("❌ Invalid outgoing message data")
                await sqs_service.delete_message(QueueType.OUTGOING, message.receipt_handle)
                return
            
            # Send message with WhatsApp service
            with get_db_session() as db:
                with WhatsAppService(db) as service:
                    success = await service.send_message(phone_number, message_data)
                    
                    if success:
                        # Message sent successfully
                        await sqs_service.delete_message(QueueType.OUTGOING, message.receipt_handle)
                        self.stats["outgoing_processed"] += 1
                        logger.debug(f"✅ Sent outgoing message to {phone_number}")
                        
                        # Send analytics event
                        await self._send_analytics_event("message_sent", {
                            "phone_number": phone_number,
                            "message_type": message_data.get("type", "unknown"),
                            "processing_time": time.time() - message.timestamp,
                            "metadata": metadata
                        })
                    else:
                        # Sending failed, let it retry
                        logger.warning(f"⚠️  Failed to send message to {phone_number}, will retry")
                        self.stats["errors"] += 1
            
        except Exception as e:
            logger.error(f"❌ Error processing outgoing message: {e}")
            self.stats["errors"] += 1
    
    async def _process_analytics_messages(self):
        """Process analytics events from SQS"""
        logger.info("📊 Starting analytics worker")
        
        while self.running:
            try:
                # Receive messages from analytics queue
                messages = await sqs_service.receive_messages(
                    QueueType.ANALYTICS,
                    max_messages=10,
                    wait_time_seconds=20
                )
                
                if not messages:
                    continue
                
                logger.debug(f"📊 Processing {len(messages)} analytics events")
                
                # Process messages in batches
                for message in messages:
                    await self._process_single_analytics_event(message)
                
            except Exception as e:
                logger.error(f"❌ Error in analytics worker: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(5)
    
    async def _process_single_analytics_event(self, message: SQSMessage):
        """Process a single analytics event"""
        try:
            data = message.body.get("data", {})
            event_type = data.get("event_type")
            event_data = data.get("event_data", {})
            
            if not event_type:
                logger.error("❌ No event type in analytics message")
                await sqs_service.delete_message(QueueType.ANALYTICS, message.receipt_handle)
                return
            
            # Process analytics event
            logger.debug(f"📊 Processing analytics event: {event_type}")
            
            # Mark as processed
            await sqs_service.delete_message(QueueType.ANALYTICS, message.receipt_handle)
            self.stats["analytics_processed"] += 1
            logger.debug(f"✅ Processed analytics event: {event_type}")
            
        except Exception as e:
            logger.error(f"❌ Error processing analytics event: {e}")
            self.stats["errors"] += 1
    
    async def _send_analytics_event(self, event_type: str, event_data: Dict[str, Any]):
        """Helper to send analytics events"""
        try:
            from app.services.sqs_service import send_analytics_event
            await send_analytics_event(event_type, event_data)
        except Exception as e:
            logger.warning(f"⚠️  Failed to send analytics event: {e}")
    
    async def _health_monitor(self):
        """Monitor worker health and log stats periodically"""
        logger.info("💓 Starting health monitor")
        
        while self.running:
            try:
                await asyncio.sleep(60)  # Log stats every minute
                
                if not self.running:
                    break
                
                uptime = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
                logger.info(f"💓 Worker stats - Uptime: {uptime:.1f}s, "
                           f"Incoming: {self.stats['incoming_processed']}, "
                           f"Outgoing: {self.stats['outgoing_processed']}, "
                           f"Analytics: {self.stats['analytics_processed']}, "
                           f"Errors: {self.stats['errors']}")
                
            except Exception as e:
                logger.error(f"❌ Error in health monitor: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current worker statistics"""
        uptime = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "running": self.running,
            "workers": {name: not task.done() for name, task in self.workers.items()}
        }

# Global message processor instance
message_processor = MessageProcessor()

# Context manager for message processor lifecycle
@asynccontextmanager
async def message_processor_lifespan():
    """Context manager for message processor lifecycle"""
    try:
        # Start the processor
        processor_task = asyncio.create_task(message_processor.start())
        yield message_processor
    finally:
        # Stop the processor
        await message_processor.stop()
        if not processor_task.done():
            processor_task.cancel()
            try:
                await processor_task
            except asyncio.CancelledError:
                pass