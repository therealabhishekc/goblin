"""
Business-related data models.
Includes analytics, metrics, and business intelligence models.
"""
from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base

# Pydantic Models
class BusinessMetrics(BaseModel):
    """Business metrics data model"""
    date: datetime = Field(default_factory=lambda: datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
    total_messages_received: int = Field(default=0, description="Total messages received")
    total_responses_sent: int = Field(default=0, description="Total responses sent")
    unique_users: int = Field(default=0, description="Unique users")
    response_time_avg_seconds: Optional[float] = Field(None, description="Average response time")
    popular_keywords: Dict[str, int] = Field(default={}, description="Popular keywords count")

class MetricsResponse(BaseModel):
    """Metrics response model"""
    date: str
    total_messages_received: int
    total_responses_sent: int
    unique_users: int
    response_time_avg_seconds: Optional[float]
    popular_keywords: Dict[str, int]

class MetricsSummary(BaseModel):
    """Overall metrics summary"""
    total_messages_received: int
    total_responses_sent: int
    average_response_time_seconds: float
    total_days_tracked: int

class MessageTemplate(BaseModel):
    """Message template model"""
    name: str = Field(..., description="Template name")
    category: str = Field(..., description="Template category")
    template_text: str = Field(..., description="Template text content")
    variables: list[str] = Field(default=[], description="Template variables")
    is_active: bool = Field(True, description="Is template active")

# SQLAlchemy Database Models
class BusinessMetricsDB(Base):
    """Business metrics database table"""
    __tablename__ = "business_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    
    # Message metrics
    total_messages_received = Column(Integer, default=0)
    total_responses_sent = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    
    # Performance metrics
    response_time_avg_seconds = Column(Float)
    
    # Content tracking
    popular_keywords = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MessageTemplateDB(Base):
    """Message template database table"""
    __tablename__ = "message_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(50), nullable=False)
    
    # Template content
    template_text = Column(String(1000), nullable=False)
    variables = Column(JSON, default=[])
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
