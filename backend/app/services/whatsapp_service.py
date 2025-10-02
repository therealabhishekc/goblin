"""
WhatsApp service for handling business logic around WhatsApp operations.
This service coordinates between repositories and implements business rules.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..repositories.user_repository import UserRepository
from ..repositories.message_repository import MessageRepository
from ..repositories.analytics_repository import AnalyticsRepository
from ..models.whatsapp import WhatsAppMessage
from ..models.user import UserProfile
from ..core.database import get_db_session
from ..core.logging import logger

class WhatsAppService:
    """Service for WhatsApp business logic"""
    
    def __init__(self, db_session: Session = None):
        """Initialize service with database session"""
        self.db = db_session or get_db_session()
        self.user_repo = UserRepository(self.db)
        self.message_repo = MessageRepository(self.db)
        self.analytics_repo = AnalyticsRepository(self.db)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    async def process_incoming_message(self, webhook_data: dict) -> Dict[str, str]:
        """
        Process incoming WhatsApp message from webhook.
        This is the main business logic for handling new messages.
        """
        try:
            # Extract message data
            phone_number = self._extract_phone_number(webhook_data)
            message_id = self._extract_message_id(webhook_data)
            
            if not phone_number or not message_id:
                return {"status": "error", "message": "Invalid webhook data"}
            
            # Check if message already processed (deduplication)
            existing_message = self.message_repo.get_by_message_id(message_id)
            if existing_message:
                return {"status": "duplicate", "message": "Message already processed"}
            
            # Create or update user profile
            user = self._ensure_user_exists(phone_number, webhook_data)
            
            # Store the message
            message = self._store_message(webhook_data)
            
            # Update analytics
            self._update_analytics()
            
            # Update user interaction
            self.user_repo.update_last_interaction(phone_number)
            
            # Process automated replies
            await self._process_automated_reply(phone_number, webhook_data)
            
            return {
                "status": "success", 
                "message": "Message processed successfully",
                "message_id": message_id,
                "user_id": str(user.id) if user else None
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Processing failed: {str(e)}"}
    
    async def send_message(self, phone_number: str, message_data: Dict[str, Any]) -> bool:
        """
        Send a WhatsApp message using the WhatsApp API
        This method is called by the outgoing message worker
        
        Args:
            phone_number: Recipient phone number
            message_data: Message data with type and content
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            from app.whatsapp_api import send_whatsapp_message
            
            # Send message via WhatsApp API
            result = await send_whatsapp_message(phone_number, message_data)
            
            # Store the sent message in database
            sent_message_data = {
                "message_id": result.get('messages', [{}])[0].get('id'),
                "from_phone": "business",  # This is an outgoing message
                "to_phone": phone_number,
                "message_type": message_data.get("type", "text"),
                "content": message_data.get("content", str(message_data)),
                "timestamp": datetime.utcnow(),
                "status": "sent",
                "direction": "outgoing"
            }
            
            # Store in database if we have the structure
            try:
                from app.models.whatsapp import WhatsAppMessage
                sent_message = WhatsAppMessage(**sent_message_data)
                self.message_repo.create(sent_message)
            except Exception as db_e:
                logger.warning(f"Failed to store sent message in database: {db_e}")
            
            # Update analytics
            self.analytics_repo.increment_responses_sent()
            
            logger.info(f"✅ Message sent successfully to {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send message to {phone_number}: {e}")
            return False
    
    async def process_text_message(self, phone_number: str, text_content: str, contact_info: Dict[str, Any], processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process an individual text message (called by message processor)"""
        try:
            # Store the message in database
            message_data = {
                "message_id": processing_metadata.get("message_id"),
                "from_phone": phone_number,
                "message_type": "text",
                "content": text_content,
                "timestamp": datetime.utcnow(),
                "status": "processing"
            }
            
            # Create or update user profile
            user = self._ensure_user_exists_from_contact(phone_number, contact_info)
            
            # Store the message
            stored_message = self.message_repo.create_from_dict(message_data)
            
            # Update analytics
            self._update_analytics()
            
            # Update user interaction
            self.user_repo.update_last_interaction(phone_number)
            
            # Process automated replies
            reply_message_id = await self._process_automated_reply_direct(
                phone_number=phone_number,
                message_text=text_content,
                message_type="text",
                user_context={
                    "phone_number": phone_number,
                    "user_profile": self.get_user_profile(phone_number),
                    "contact_info": contact_info
                }
            )
            
            return {
                "status": "success",
                "message_stored": True,
                "reply_sent": reply_message_id is not None,
                "reply_message_id": reply_message_id,
                "user_id": str(user.id) if user else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing text message from {phone_number}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def process_interactive_message(self, phone_number: str, interactive_data: Dict[str, Any], contact_info: Dict[str, Any], processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process an interactive message (buttons, lists, etc.)"""
        try:
            # Store the message in database
            message_data = {
                "message_id": processing_metadata.get("message_id"),
                "from_phone": phone_number,
                "message_type": "interactive",
                "content": str(interactive_data),
                "timestamp": datetime.utcnow(),
                "status": "processing"
            }
            
            # Create or update user profile
            user = self._ensure_user_exists_from_contact(phone_number, contact_info)
            
            # Store the message
            stored_message = self.message_repo.create_from_dict(message_data)
            
            # Update analytics
            self._update_analytics()
            
            # Update user interaction
            self.user_repo.update_last_interaction(phone_number)
            
            return {
                "status": "success",
                "message_stored": True,
                "user_id": str(user.id) if user else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing interactive message from {phone_number}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def process_media_message(self, phone_number: str, media_type: str, media_data: Dict[str, Any], contact_info: Dict[str, Any], processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a media message (image, document, audio, video)"""
        try:
            # Store the message in database
            message_data = {
                "message_id": processing_metadata.get("message_id"),
                "from_phone": phone_number,
                "message_type": media_type,
                "content": media_data.get("caption", ""),
                "media_url": media_data.get("url"),
                "media_type": media_data.get("mime_type"),
                "timestamp": datetime.utcnow(),
                "status": "processing"
            }
            
            # Create or update user profile
            user = self._ensure_user_exists_from_contact(phone_number, contact_info)
            
            # Store the message
            stored_message = self.message_repo.create_from_dict(message_data)
            
            # Update analytics
            self._update_analytics()
            
            # Update user interaction
            self.user_repo.update_last_interaction(phone_number)
            
            return {
                "status": "success",
                "message_stored": True,
                "media_type": media_type,
                "user_id": str(user.id) if user else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing media message from {phone_number}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def process_location_message(self, phone_number: str, location_data: Dict[str, Any], contact_info: Dict[str, Any], processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a location message"""
        try:
            # Store the message in database
            message_data = {
                "message_id": processing_metadata.get("message_id"),
                "from_phone": phone_number,
                "message_type": "location",
                "content": f"Location: {location_data.get('latitude')}, {location_data.get('longitude')}",
                "timestamp": datetime.utcnow(),
                "status": "processing"
            }
            
            # Create or update user profile
            user = self._ensure_user_exists_from_contact(phone_number, contact_info)
            
            # Store the message
            stored_message = self.message_repo.create_from_dict(message_data)
            
            # Update analytics
            self._update_analytics()
            
            # Update user interaction
            self.user_repo.update_last_interaction(phone_number)
            
            return {
                "status": "success",
                "message_stored": True,
                "user_id": str(user.id) if user else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing location message from {phone_number}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _process_automated_reply(self, phone_number: str, webhook_data: dict):
        """Process automated replies for incoming messages"""
        try:
            from app.services.reply_automation import reply_automation
            
            # Extract message text
            message_text = self._extract_message_text(webhook_data)
            message_type = self._extract_message_type(webhook_data)
            
            if message_text:
                # Get user context for better replies
                user_context = {
                    "phone_number": phone_number,
                    "user_profile": self.get_user_profile(phone_number)
                }
                
                # Process automated reply
                reply_message_id = await reply_automation.process_incoming_message(
                    phone_number=phone_number,
                    message_text=message_text,
                    message_type=message_type,
                    user_context=user_context
                )
                
                if reply_message_id:
                    logger.info(f"🤖 Automated reply queued for {phone_number}: {reply_message_id}")
        
        except Exception as e:
            logger.error(f"❌ Error processing automated reply: {e}")
            
    async def _process_automated_reply_direct(self, phone_number: str, message_text: str, message_type: str, user_context: Dict[str, Any]) -> Optional[str]:
        """Process automated replies for direct message processing (called by message processor)"""
        try:
            from app.services.reply_automation import reply_automation
            
            # Process automated reply
            reply_message_id = await reply_automation.process_incoming_message(
                phone_number=phone_number,
                message_text=message_text,
                message_type=message_type,
                user_context=user_context
            )
            
            if reply_message_id:
                logger.info(f"🤖 Automated reply queued for {phone_number}: {reply_message_id}")
                
            return reply_message_id
        
        except Exception as e:
            logger.error(f"❌ Error processing automated reply: {e}")
            return None
    
    def get_user_conversation(self, phone_number: str, limit: int = 50) -> List[dict]:
        """Get conversation history for a user"""
        messages = self.message_repo.get_conversation_history(phone_number, limit)
        return [self._message_to_dict(msg) for msg in messages]
    
    def get_user_profile(self, phone_number: str) -> Optional[dict]:
        """Get user profile by phone number"""
        user = self.user_repo.get_by_phone_number(phone_number)
        return self._user_to_dict(user) if user else None
    
    def update_user_profile(self, phone_number: str, update_data: dict) -> Optional[dict]:
        """Update user profile"""
        user = self.user_repo.get_by_phone_number(phone_number)
        if user:
            updated_user = self.user_repo.update(user.id, update_data)
            return self._user_to_dict(updated_user)
        return None
    
    def get_daily_analytics(self, date: datetime = None) -> Optional[dict]:
        """Get analytics for a specific day"""
        if not date:
            date = datetime.utcnow()
        
        metrics = self.analytics_repo.get_metrics_by_date(date)
        return self._metrics_to_dict(metrics) if metrics else None
    
    def get_analytics_summary(self) -> dict:
        """Get overall analytics summary"""
        return self.analytics_repo.get_total_metrics_summary()
    
    def search_users(self, query: str) -> List[dict]:
        """Search users by business name"""
        users = self.user_repo.get_by_business_name(query)
        return [self._user_to_dict(user) for user in users]
    
    def get_recent_messages(self, hours: int = 24) -> List[dict]:
        """Get recent messages"""
        messages = self.message_repo.get_recent_messages(hours)
        return [self._message_to_dict(msg) for msg in messages]
    
    # Private helper methods
    def _extract_phone_number(self, webhook_data: dict) -> Optional[str]:
        """Extract phone number from webhook data"""
        try:
            return webhook_data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0].get("from")
        except (IndexError, KeyError):
            return None
    
    def _extract_message_id(self, webhook_data: dict) -> Optional[str]:
        """Extract message ID from webhook data"""
        try:
            return webhook_data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0].get("id")
        except (IndexError, KeyError):
            return None
    
    def _extract_message_text(self, webhook_data: dict) -> Optional[str]:
        """Extract message text from webhook data"""
        try:
            message = webhook_data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]
            if message.get("type") == "text":
                return message.get("text", {}).get("body")
        except (IndexError, KeyError):
            pass
        return None
    
    def _extract_message_type(self, webhook_data: dict) -> str:
        """Extract message type from webhook data"""
        try:
            return webhook_data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0].get("type", "text")
        except (IndexError, KeyError):
            return "text"
    
    def _ensure_user_exists(self, phone_number: str, webhook_data: dict):
        """Create user if doesn't exist, return existing user otherwise"""
        user = self.user_repo.get_by_phone_number(phone_number)
        
        if not user:
            # Extract user info from webhook
            profile_name = self._extract_profile_name(webhook_data)
            
            user_data = UserProfile(
                whatsapp_phone=phone_number,
                display_name=profile_name,
                first_contact=datetime.utcnow(),
                last_interaction=datetime.utcnow(),
                total_messages=1
            )
            user = self.user_repo.create(user_data)
        else:
            # Update message count
            user.total_messages += 1
            self.db.commit()
        
        return user
        
    def _ensure_user_exists_from_contact(self, phone_number: str, contact_info: Dict[str, Any]):
        """Create user if doesn't exist, return existing user otherwise (from contact info)"""
        user = self.user_repo.get_by_phone_number(phone_number)
        
        if not user:
            # Extract user info from contact
            profile_name = contact_info.get("profile", {}).get("name") if contact_info else None
            
            user_data = UserProfile(
                whatsapp_phone=phone_number,
                display_name=profile_name,
                first_contact=datetime.utcnow(),
                last_interaction=datetime.utcnow(),
                total_messages=1
            )
            user = self.user_repo.create(user_data)
        else:
            # Update message count
            user.total_messages += 1
            self.db.commit()
        
        return user
    
    def _extract_profile_name(self, webhook_data: dict) -> Optional[str]:
        """Extract profile name from webhook data"""
        try:
            contacts = webhook_data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("contacts", [])
            if contacts:
                return contacts[0].get("profile", {}).get("name")
        except (IndexError, KeyError):
            pass
        return None
    
    def _store_message(self, webhook_data: dict):
        """Store message in database"""
        # Extract message details
        message_data = self._parse_webhook_message(webhook_data)
        
        message = WhatsAppMessage(**message_data)
        return self.message_repo.create(message)
    
    def _parse_webhook_message(self, webhook_data: dict) -> dict:
        """Parse webhook data into message format"""
        try:
            msg_data = webhook_data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]
            
            return {
                "message_id": msg_data.get("id"),
                "from_phone": msg_data.get("from"),
                "message_type": msg_data.get("type", "text"),
                "content": msg_data.get("text", {}).get("body") if msg_data.get("type") == "text" else None,
                "timestamp": datetime.utcnow(),
                "webhook_raw_data": webhook_data,
                "status": "received"
            }
        except (IndexError, KeyError):
            return {}
    
    def _update_analytics(self):
        """Update daily analytics counters"""
        self.analytics_repo.increment_messages_received()
        self.analytics_repo.update_unique_users_count()
    
    def _message_to_dict(self, message) -> dict:
        """Convert message object to dictionary"""
        return {
            "id": str(message.id),
            "message_id": message.message_id,
            "from_phone": message.from_phone,
            "message_type": message.message_type,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "status": message.status
        }
    
    def _user_to_dict(self, user) -> dict:
        """Convert user object to dictionary"""
        return {
            "id": str(user.id),
            "whatsapp_phone": user.whatsapp_phone,
            "display_name": user.display_name,
            "business_name": user.business_name,
            "customer_tier": user.customer_tier,
            "tags": user.tags,
            "total_messages": user.total_messages,
            "last_interaction": user.last_interaction.isoformat() if user.last_interaction else None,
            "is_active": user.is_active
        }
    
    def _metrics_to_dict(self, metrics) -> dict:
        """Convert metrics object to dictionary"""
        return {
            "date": metrics.date.isoformat(),
            "total_messages_received": metrics.total_messages_received,
            "total_responses_sent": metrics.total_responses_sent,
            "unique_users": metrics.unique_users,
            "response_time_avg_seconds": metrics.response_time_avg_seconds,
            "popular_keywords": metrics.popular_keywords
        }
