"""
Conversation state and workflow template models.
Handles interactive menu conversations and workflow templates.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.core.database import Base

# ==================================================================================
# ENUMS
# ==================================================================================

class TemplateType(str, Enum):
    """Template types for interactive menus"""
    BUTTON = "button"
    LIST = "list"
    TEXT = "text"

# ==================================================================================
# PYDANTIC MODELS (API Request/Response)
# ==================================================================================

class ConversationStateCreate(BaseModel):
    """Request model for creating a conversation state"""
    phone_number: str = Field(..., description="Customer phone number")
    conversation_flow: str = Field(..., description="Template name/flow identifier")
    context: Dict[str, Any] = Field(default={}, description="Conversation context data")
    expires_at: Optional[datetime] = Field(None, description="When conversation expires")

class ConversationStateUpdate(BaseModel):
    """Request model for updating conversation state"""
    context: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None

class ConversationStateResponse(BaseModel):
    """Response model for conversation state"""
    id: str
    phone_number: str
    conversation_flow: str
    context: Dict[str, Any]
    last_interaction: datetime
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class WorkflowTemplateCreate(BaseModel):
    """Request model for creating a workflow template"""
    template_name: str = Field(..., description="Unique template name")
    template_type: TemplateType = Field(..., description="Type of template")
    trigger_keywords: List[str] = Field(default=[], description="Keywords that trigger this template")
    menu_structure: Dict[str, Any] = Field(..., description="Menu structure (buttons, lists, etc.)")
    is_active: bool = Field(True, description="Is template active")

class WorkflowTemplateUpdate(BaseModel):
    """Request model for updating workflow template"""
    template_type: Optional[TemplateType] = None
    trigger_keywords: Optional[List[str]] = None
    menu_structure: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class WorkflowTemplateResponse(BaseModel):
    """Response model for workflow template"""
    id: str
    template_name: str
    template_type: str
    trigger_keywords: List[str]
    menu_structure: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

# ==================================================================================
# SQLALCHEMY DATABASE MODELS
# ==================================================================================

class ConversationStateDB(Base):
    """Conversation state database table - tracks active conversation flows"""
    __tablename__ = "conversation_state"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Customer identification
    phone_number = Column(String(20), nullable=False, index=True)
    
    # Flow tracking
    conversation_flow = Column(String(50), nullable=False, index=True)  # Template name
    
    # Context data
    context = Column(JSONB, default={})  # Stores user selections, inputs, etc.
    
    # Timing
    last_interaction = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, index=True)  # Auto-expire old conversations
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WorkflowTemplateDB(Base):
    """Workflow template database table - stores reusable interactive menu templates"""
    __tablename__ = "workflow_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template identification
    template_name = Column(String(100), unique=True, nullable=False, index=True)
    template_type = Column(String(20), nullable=False)  # 'button', 'list', 'text'
    
    # Triggers
    trigger_keywords = Column(ARRAY(String), default=[])  # Keywords that activate this template
    
    # Menu structure
    menu_structure = Column(JSONB, nullable=False)  # Full menu definition
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
