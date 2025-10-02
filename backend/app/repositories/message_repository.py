"""
Message repository for WhatsApp message storage and retrieval.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from .base_repository import BaseRepository
from ..models.whatsapp import WhatsAppMessageDB
from ..models.whatsapp import WhatsAppMessage

class MessageRepository(BaseRepository[WhatsAppMessage]):
    """Repository for WhatsApp message operations"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, WhatsAppMessageDB)
    
    def get_by_message_id(self, message_id: str) -> Optional[WhatsAppMessageDB]:
        """Get message by WhatsApp message ID"""
        return self.db.query(self.model_class).filter(
            self.model_class.message_id == message_id
        ).first()
    
    def get_conversation_history(self, phone_number: str, limit: int = 50) -> List[WhatsAppMessageDB]:
        """Get conversation history for a phone number"""
        return self.db.query(self.model_class).filter(
            self.model_class.from_phone == phone_number
        ).order_by(desc(self.model_class.timestamp)).limit(limit).all()
    
    def get_messages_by_date_range(self, start_date: datetime, end_date: datetime) -> List[WhatsAppMessageDB]:
        """Get messages within date range"""
        return self.db.query(self.model_class).filter(
            and_(
                self.model_class.timestamp >= start_date,
                self.model_class.timestamp <= end_date
            )
        ).order_by(desc(self.model_class.timestamp)).all()
    
    def get_unread_messages(self) -> List[WhatsAppMessageDB]:
        """Get all unread messages"""
        return self.db.query(self.model_class).filter(
            self.model_class.status == "delivered"
        ).order_by(self.model_class.timestamp).all()
    
    def mark_as_read(self, message_id: str) -> Optional[WhatsAppMessageDB]:
        """Mark message as read"""
        message = self.get_by_message_id(message_id)
        if message:
            message.status = "read"
            self.db.commit()
            self.db.refresh(message)
        return message
    
    def get_media_messages(self, media_type: str = None) -> List[WhatsAppMessageDB]:
        """Get messages with media attachments"""
        query = self.db.query(self.model_class).filter(
            self.model_class.media_url.isnot(None)
        )
        
        if media_type:
            query = query.filter(self.model_class.media_type == media_type)
            
        return query.order_by(desc(self.model_class.timestamp)).all()
    
    def get_recent_messages(self, hours: int = 24) -> List[WhatsAppMessageDB]:
        """Get messages from last N hours"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(self.model_class).filter(
            self.model_class.timestamp >= since
        ).order_by(desc(self.model_class.timestamp)).all()
        
    def create_from_dict(self, message_data: dict) -> WhatsAppMessageDB:
        """Create message from dictionary data"""
        message = WhatsAppMessageDB(**message_data)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
