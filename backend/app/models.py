from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

# Enums for better type safety
class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contacts"
    INTERACTIVE = "interactive"
    BUTTON = "button"
    TEMPLATE = "template"

class MessageStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    REPLIED = "replied"
    FAILED = "failed"
    IGNORED = "ignored"

# WhatsApp specific models
class WhatsAppMessage(BaseModel):
    """Model for incoming WhatsApp messages"""
    message_id: str = Field(..., description="WhatsApp message ID")
    from_number: str = Field(..., description="Sender's phone number")
    message_type: MessageType = Field(default=MessageType.TEXT)
    text_content: Optional[str] = Field(None, description="Text message content")
    media_url: Optional[str] = Field(None, description="Media file URL if applicable")
    media_id: Optional[str] = Field(None, description="WhatsApp media ID")
    mime_type: Optional[str] = Field(None, description="Media MIME type")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_webhook_data: Optional[Dict[str, Any]] = Field(None, description="Original webhook payload")
    
    # Processing status
    status: MessageStatus = Field(default=MessageStatus.RECEIVED)
    processed_at: Optional[datetime] = None
    response_sent: Optional[str] = Field(None, description="Response template sent back")
    
    class Config:
        use_enum_values = True

class WhatsAppWebhookPayload(BaseModel):
    """Model for the entire WhatsApp webhook payload"""
    object: str = Field(..., description="Should be 'whatsapp_business_account'")
    entry: List[Dict[str, Any]] = Field(..., description="Entry array from webhook")
    
    @property
    def messages(self) -> List[Dict[str, Any]]:
        """Extract messages from the webhook payload"""
        if not self.entry:
            return []
        
        changes = self.entry[0].get("changes", [])
        if not changes:
            return []
            
        value = changes[0].get("value", {})
        return value.get("messages", [])
    
    @property
    def statuses(self) -> List[Dict[str, Any]]:
        """Extract message statuses from webhook payload"""
        if not self.entry:
            return []
        
        changes = self.entry[0].get("changes", [])
        if not changes:
            return []
            
        value = changes[0].get("value", {})
        return value.get("statuses", [])

class UserProfile(BaseModel):
    """Model for user profiles/contacts"""
    phone_number: str = Field(..., description="User's phone number")
    display_name: Optional[str] = Field(None, description="User's display name")
    first_interaction: datetime = Field(default_factory=datetime.utcnow)
    last_interaction: Optional[datetime] = None
    total_messages: int = Field(default=0)
    preferred_language: Optional[str] = Field(default="en")
    tags: List[str] = Field(default_factory=list, description="User tags/categories")
    
    # Business context
    customer_status: Literal["new", "active", "inactive", "blocked"] = "new"
    notes: Optional[str] = Field(None, description="Admin notes about user")

class TemplateMessage(BaseModel):
    """Model for WhatsApp template messages to send"""
    template_name: str = Field(..., description="Template name from WhatsApp")
    to_number: str = Field(..., description="Recipient phone number")
    language_code: str = Field(default="en_US")
    parameters: Optional[List[str]] = Field(default_factory=list)
    
class BusinessMetrics(BaseModel):
    """Model for tracking business metrics"""
    date: datetime = Field(default_factory=lambda: datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
    total_messages_received: int = Field(default=0)
    total_responses_sent: int = Field(default=0)
    unique_users: int = Field(default=0)
    response_time_avg_seconds: Optional[float] = None
    popular_keywords: Dict[str, int] = Field(default_factory=dict)

# Keep your original models for future chat features
class Message(BaseModel):
    """Generic message model for future chat features"""
    message_id: str
    chat_id: str
    sender: str
    content: str
    timestamp: datetime
    type: str = "text"
    media_url: Optional[str] = None

class Chat(BaseModel):
    """Generic chat model for future features"""
    chat_id: str
    participants: List[str]
    last_message: Optional[Message] = None
