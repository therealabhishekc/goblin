"""
SQLAlchemy models for PostgreSQL database tables.
These are the actual database table definitions.
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Float, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid

# DEPRECATED: This models file has been replaced by individual model files in app/models/
# Use the newer model files instead:
# - app/models/user.py (UserProfileDB)
# - app/models/whatsapp.py (WhatsAppMessageDB)
# - app/models/business.py (BusinessMetricsDB, MessageTemplateDB)

from app.core.database import Base

class UserProfile(Base):
    """User profile table for customer management"""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    whatsapp_phone = Column(String(20), unique=True, nullable=False, index=True)
    display_name = Column(String(100))
    business_name = Column(String(200))
    email = Column(String(255))
    
    # Customer management fields
    customer_tier = Column(String(20), default="regular")  # regular, premium, vip
    tags = Column(ARRAY(String), default=[])  # PostgreSQL array for tags
    notes = Column(Text)
    
    # Interaction tracking
    first_contact = Column(DateTime, default=datetime.utcnow)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    total_messages = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WhatsAppMessage(Base):
    """WhatsApp message storage table"""
    __tablename__ = "whatsapp_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Message details
    from_phone = Column(String(20), nullable=False, index=True)
    to_phone = Column(String(20))
    message_type = Column(String(20), nullable=False)  # text, image, document, etc.
    content = Column(Text)
    
    # Media information
    media_url = Column(String(500))
    media_type = Column(String(50))  # image/jpeg, application/pdf, etc.
    media_size = Column(Integer)
    
    # Message status
    status = Column(String(20), default="received")  # received, delivered, read, failed
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Context and metadata
    context_message_id = Column(String(100))  # For replies
    webhook_raw_data = Column(JSON)  # Store original webhook payload
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BusinessMetrics(Base):
    """Business analytics and metrics table"""
    __tablename__ = "business_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=False, unique=True, index=True)  # Daily metrics
    
    # Message metrics
    total_messages_received = Column(Integer, default=0)
    total_responses_sent = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    
    # Performance metrics
    response_time_avg_seconds = Column(Float)
    
    # Popular content tracking
    popular_keywords = Column(JSON, default={})  # {"keyword": count}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MessageTemplate(Base):
    """Template messages for automated responses"""
    __tablename__ = "message_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(50), nullable=False)  # greeting, support, marketing
    
    # Template content
    template_text = Column(Text, nullable=False)
    variables = Column(ARRAY(String), default=[])  # Variables like {name}, {business}
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
