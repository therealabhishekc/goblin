"""
User-related data models.
Includes user profiles, customer information, and user management.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base

# Enums
class CustomerTier(str, Enum):
    REGULAR = "regular"
    PREMIUM = "premium"
    VIP = "vip"

# Pydantic Models
class UserProfile(BaseModel):
    """User profile data model"""
    whatsapp_phone: str = Field(..., description="WhatsApp phone number")
    display_name: Optional[str] = Field(None, description="Display name")
    business_name: Optional[str] = Field(None, description="Business name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    customer_tier: CustomerTier = Field(CustomerTier.REGULAR, description="Customer tier")
    tags: List[str] = Field(default=[], description="Customer tags")
    notes: Optional[str] = Field(None, description="Customer notes")
    is_active: bool = Field(True, description="Is user active")
    subscription: str = Field("subscribed", description="Subscription status for template messages")

class UserCreate(BaseModel):
    """User creation model"""
    whatsapp_phone: str
    display_name: Optional[str] = None
    business_name: Optional[str] = None
    email: Optional[EmailStr] = None
    customer_tier: CustomerTier = CustomerTier.REGULAR
    tags: List[str] = []
    notes: Optional[str] = None

class UserUpdate(BaseModel):
    """User update model"""
    display_name: Optional[str] = None
    business_name: Optional[str] = None
    email: Optional[EmailStr] = None
    customer_tier: Optional[CustomerTier] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    subscription: Optional[str] = Field(None, description="Update subscription status")

class UserResponse(BaseModel):
    """User response model"""
    id: str
    whatsapp_phone: str
    display_name: Optional[str]
    business_name: Optional[str]
    email: Optional[str]
    customer_tier: str
    tags: List[str]
    total_messages: int
    last_interaction: Optional[datetime]
    is_active: bool
    subscription: str
    subscription_updated_at: Optional[datetime]
    created_at: datetime

# SQLAlchemy Database Model
class UserProfileDB(Base):
    """User profile database table"""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    whatsapp_phone = Column(String(20), unique=True, nullable=False, index=True)
    display_name = Column(String(100))
    business_name = Column(String(200))
    email = Column(String(255))
    
    # Customer management
    customer_tier = Column(String(20), default="regular")
    tags = Column(ARRAY(String), default=[])
    notes = Column(Text)
    
    # Interaction tracking
    first_contact = Column(DateTime, default=datetime.utcnow)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    total_messages = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Message subscription (for templates only, does NOT affect automated replies)
    subscription = Column(String(20), default="subscribed")  # 'subscribed' or 'unsubscribed'
    subscription_updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
