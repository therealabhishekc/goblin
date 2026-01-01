"""
Marketing Campaign Models
Supports sending marketing messages to thousands of customers with rate limiting
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, Date, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base

# ==================================================================================
# ENUMS
# ==================================================================================

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class RecipientStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    SKIPPED = "skipped"

class ScheduleStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# ==================================================================================
# PYDANTIC MODELS (API Request/Response)
# ==================================================================================

class CampaignCreate(BaseModel):
    """Request model for creating a new marketing campaign"""
    name: str = Field(..., description="Campaign name")
    description: Optional[str] = Field(None, description="Campaign description")
    template_name: str = Field(..., description="WhatsApp template to use")
    language_code: str = Field("en_US", description="Template language")
    target_audience: Optional[Dict[str, Any]] = Field(None, description="Audience filter criteria")
    daily_send_limit: int = Field(250, description="Messages per day (WhatsApp limit)")
    priority: int = Field(5, ge=1, le=10, description="Campaign priority (1=highest, 10=lowest)")
    scheduled_start_date: Optional[datetime] = Field(None, description="When to start sending")
    scheduled_end_date: Optional[datetime] = Field(None, description="When to stop sending")
    template_components: Optional[List[Dict[str, Any]]] = Field(None, description="Template structure")

class CampaignUpdate(BaseModel):
    """Request model for updating a campaign"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    daily_send_limit: Optional[int] = Field(None, ge=1, le=1000)
    priority: Optional[int] = Field(None, ge=1, le=10)
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None

class CampaignResponse(BaseModel):
    """Response model for campaign details"""
    id: str
    name: str
    description: Optional[str]
    template_name: str
    language_code: str
    status: str
    priority: int
    total_target_customers: int
    messages_sent: int
    messages_delivered: int
    messages_read: int
    messages_failed: int
    messages_pending: int
    daily_send_limit: int
    scheduled_start_date: Optional[datetime]
    scheduled_end_date: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class RecipientCreate(BaseModel):
    """Request model for adding recipients to a campaign"""
    campaign_id: str
    phone_numbers: List[str] = Field(..., description="List of phone numbers to add")
    template_parameters: Optional[Dict[str, Any]] = Field(None, description="Custom parameters for recipients")

class RecipientResponse(BaseModel):
    """Response model for recipient details"""
    id: str
    campaign_id: str
    phone_number: str
    status: str
    scheduled_send_date: Optional[date]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    whatsapp_message_id: Optional[str]
    failure_reason: Optional[str]
    retry_count: int
    created_at: datetime

class CampaignStats(BaseModel):
    """Campaign statistics summary"""
    campaign_id: str
    campaign_name: str
    status: str
    total_target: int
    sent: int
    delivered: int
    read: int
    failed: int
    pending: int
    progress_percentage: float
    delivery_rate: Optional[float]
    read_rate: Optional[float]
    estimated_completion_date: Optional[date]

class DailySendSummary(BaseModel):
    """Daily sending summary"""
    date: date
    campaigns_count: int
    total_planned: int
    total_sent: int
    total_remaining: int
    by_campaign: List[Dict[str, Any]]

# ==================================================================================
# SQLALCHEMY DATABASE MODELS
# ==================================================================================

class MarketingCampaignDB(Base):
    """Marketing campaign database table"""
    __tablename__ = "marketing_campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Campaign details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    template_name = Column(String(100), nullable=False)
    language_code = Column(String(10), default="en_US")
    
    # Configuration
    target_audience = Column(JSON)
    total_target_customers = Column(Integer, default=0)
    daily_send_limit = Column(Integer, default=250)
    
    # Status
    status = Column(String(20), default="draft")
    priority = Column(Integer, default=5)
    
    # Scheduling
    scheduled_start_date = Column(DateTime)
    scheduled_end_date = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Template
    template_components = Column(JSON)
    
    # Statistics
    messages_sent = Column(Integer, default=0)
    messages_delivered = Column(Integer, default=0)
    messages_read = Column(Integer, default=0)
    messages_failed = Column(Integer, default=0)
    messages_pending = Column(Integer, default=0)
    
    # Metadata
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CampaignRecipientDB(Base):
    """Campaign recipient database table"""
    __tablename__ = "campaign_recipients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('marketing_campaigns.id', ondelete='CASCADE'), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    
    # Status
    status = Column(String(20), default="pending")
    whatsapp_message_id = Column(String(100))
    
    # Scheduling
    scheduled_send_date = Column(Date)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    failed_at = Column(DateTime)
    
    # Error handling
    failure_reason = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Personalization
    template_parameters = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CampaignSendScheduleDB(Base):
    """Campaign send schedule database table"""
    __tablename__ = "campaign_send_schedule"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('marketing_campaigns.id', ondelete='CASCADE'), nullable=False)
    
    # Schedule
    send_date = Column(Date, nullable=False)
    batch_number = Column(Integer, nullable=False)
    
    # Batch limits
    batch_size = Column(Integer, default=250)
    messages_sent = Column(Integer, default=0)
    messages_remaining = Column(Integer, default=250)
    
    # Status
    status = Column(String(20), default="pending")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
