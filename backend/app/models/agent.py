from sqlalchemy import Column, String, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

from app.database.connection import Base

# Database Models
class AgentSessionDB(Base):
    __tablename__ = "agent_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversation_state.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(String(50), nullable=True)
    agent_name = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="waiting")
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(hours=22))
    last_message_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("status IN ('waiting', 'active', 'ended')", name="valid_status"),
    )

class AgentMessageDB(Base):
    __tablename__ = "agent_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False)
    sender_type = Column(String(20), nullable=False)
    sender_id = Column(String(50), nullable=True)
    message_text = Column(Text, nullable=False)
    media_url = Column(Text, nullable=True)
    media_type = Column(String(20), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("sender_type IN ('customer', 'agent', 'system')", name="valid_sender"),
    )

# Pydantic Schemas
class AgentSessionCreate(BaseModel):
    conversation_id: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None

class AgentSessionResponse(BaseModel):
    id: str
    conversation_id: str
    phone_number: str
    customer_name: Optional[str]
    agent_id: Optional[str]
    agent_name: Optional[str]
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    expires_at: datetime
    last_message_at: datetime
    unread_count: int = 0
    
    class Config:
        from_attributes = True

class AgentMessageCreate(BaseModel):
    session_id: str
    sender_type: str = Field(..., pattern="^(customer|agent|system)$")
    sender_id: Optional[str] = None
    message_text: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None

class AgentMessageResponse(BaseModel):
    id: str
    session_id: str
    sender_type: str
    sender_id: Optional[str]
    message_text: str
    media_url: Optional[str]
    media_type: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True
