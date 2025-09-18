"""
WhatsApp service for handling business logic around WhatsApp operations.
This service coordinates between repositories and implements business rules.
"""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from ..repositories.user_repository import UserRepository
from ..repositories.message_repository import MessageRepository
from ..repositories.analytics_repository import AnalyticsRepository
from ..models.whatsapp import WhatsAppMessage
from ..models.user import UserProfile
from ..core.database import get_db_session

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
    
    def process_incoming_message(self, webhook_data: dict) -> Dict[str, str]:
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
            
            return {
                "status": "success", 
                "message": "Message processed successfully",
                "message_id": message_id,
                "user_id": str(user.id) if user else None
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Processing failed: {str(e)}"}
    
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
