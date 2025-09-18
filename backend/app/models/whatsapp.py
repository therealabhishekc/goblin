"""
WhatsApp-related data models.
Includes message models, webhook payloads, and WhatsApp-specific types.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base

# Enums
class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    VOICE = "voice"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACTS = "contacts"
    BUTTON = "button"
    INTERACTIVE = "interactive"

class MessageStatus(str, Enum):
    RECEIVED = "received"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    SENT = "sent"

# Pydantic Models for API
class WhatsAppMessage(BaseModel):
    """WhatsApp message data model"""
    message_id: str = Field(..., description="WhatsApp message ID")
    from_phone: str = Field(..., description="Sender phone number")
    to_phone: Optional[str] = Field(None, description="Recipient phone number")
    message_type: MessageType = Field(..., description="Type of message")
    content: Optional[str] = Field(None, description="Message content")
    media_url: Optional[str] = Field(None, description="Media file URL")
    media_type: Optional[str] = Field(None, description="MIME type of media")
    media_size: Optional[int] = Field(None, description="Media file size in bytes")
    status: MessageStatus = Field(MessageStatus.RECEIVED, description="Message status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_message_id: Optional[str] = Field(None, description="ID of message being replied to")

class WhatsAppWebhookPayload(BaseModel):
    """WhatsApp webhook payload structure"""
    object: str
    entry: List[Dict[str, Any]]
    
    def get_first_message(self) -> Optional[Dict[str, Any]]:
        """Extract first message from webhook payload"""
        try:
            return self.entry[0]["changes"][0]["value"]["messages"][0]
        except (IndexError, KeyError):
            return None
    
    def get_contact_info(self) -> Optional[Dict[str, str]]:
        """Extract contact information"""
        try:
            contacts = self.entry[0]["changes"][0]["value"]["contacts"]
            return contacts[0] if contacts else None
        except (IndexError, KeyError):
            return None
    
    @property
    def message_id(self) -> Optional[str]:
        """Get message ID from payload"""
        message = self.get_first_message()
        return message.get("id") if message else None
    
    @property
    def sender_phone(self) -> Optional[str]:
        """Get sender phone number"""
        message = self.get_first_message()
        return message.get("from") if message else None

class TemplateMessage(BaseModel):
    """Template message for sending"""
    name: str = Field(..., description="Template name")
    language: str = Field(default="en_US", description="Template language")
    components: Optional[List[Dict[str, Any]]] = Field(default=None, description="Template components")

# SQLAlchemy Database Models
class WhatsAppMessageDB(Base):
    """WhatsApp message database table"""
    __tablename__ = "whatsapp_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Message details
    from_phone = Column(String(20), nullable=False, index=True)
    to_phone = Column(String(20))
    message_type = Column(String(20), nullable=False)
    content = Column(Text)
    
    # Media information
    media_url = Column(String(500))
    media_type = Column(String(50))
    media_size = Column(Integer)
    
    # Message status and context
    status = Column(String(20), default="received")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    context_message_id = Column(String(100))
    webhook_raw_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
