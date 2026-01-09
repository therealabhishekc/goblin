# Live Agent Feature - "Talk to an Expert" Implementation Guide

## Overview

This guide explains how to implement a live chat feature where customers can transition from automated bot conversations to chat with a human agent in real-time.

## Architecture

```
Customer (WhatsApp) 
    ↕
WhatsApp Business API
    ↕
Backend FastAPI Server
    ↕
PostgreSQL Database (conversation_state + agent_sessions tables)
    ↕
Agent Dashboard (React Frontend)
```

## Database Schema Changes

### 1. Create Agent Sessions Table

```sql
-- Store active agent conversations
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversation_state(id) ON DELETE CASCADE,
    agent_id VARCHAR(50),  -- Agent username/ID (NULL if waiting for agent)
    agent_name VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'waiting',  -- 'waiting', 'active', 'ended'
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '22 hours'),
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_status CHECK (status IN ('waiting', 'active', 'ended'))
);

CREATE INDEX idx_agent_sessions_status ON agent_sessions(status);
CREATE INDEX idx_agent_sessions_agent ON agent_sessions(agent_id);
CREATE INDEX idx_agent_sessions_conversation ON agent_sessions(conversation_id);
CREATE INDEX idx_agent_sessions_expires ON agent_sessions(expires_at) WHERE status IN ('waiting', 'active');

-- Store agent chat messages
CREATE TABLE agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL,  -- 'customer', 'agent', 'system'
    sender_id VARCHAR(50),  -- Agent ID if sender is agent
    message_text TEXT NOT NULL,
    media_url TEXT,
    media_type VARCHAR(20),  -- 'image', 'video', 'document', 'audio'
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_sender CHECK (sender_type IN ('customer', 'agent', 'system'))
);

CREATE INDEX idx_agent_messages_session ON agent_messages(session_id, timestamp);
CREATE INDEX idx_agent_messages_timestamp ON agent_messages(timestamp);
```

### 2. Migration Script

Create `/backend/migrations/add_live_agent_tables.sql`:

```sql
-- Run this migration on your RDS database
-- Usage: psql "postgresql://postgres@your-rds.amazonaws.com:5432/whatsapp_business_development" -f add_live_agent_tables.sql

BEGIN;

-- Create agent sessions table
CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversation_state(id) ON DELETE CASCADE,
    agent_id VARCHAR(50),
    agent_name VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'waiting',
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '22 hours'),
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_status CHECK (status IN ('waiting', 'active', 'ended'))
);

CREATE INDEX IF NOT EXISTS idx_agent_sessions_status ON agent_sessions(status);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_agent ON agent_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_conversation ON agent_sessions(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_expires ON agent_sessions(expires_at) WHERE status IN ('waiting', 'active');

-- Create agent messages table
CREATE TABLE IF NOT EXISTS agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL,
    sender_id VARCHAR(50),
    message_text TEXT NOT NULL,
    media_url TEXT,
    media_type VARCHAR(20),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_sender CHECK (sender_type IN ('customer', 'agent', 'system'))
);

CREATE INDEX IF NOT EXISTS idx_agent_messages_session ON agent_messages(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_messages_timestamp ON agent_messages(timestamp);

COMMIT;
```

## Backend Implementation

### 1. Create Models (`backend/app/models/agent.py`)

```python
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
```

### 2. Create Agent Service (`backend/app/services/agent_service.py`)

```python
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import logging

from app.models.agent import AgentSessionDB, AgentMessageDB, AgentSessionResponse
from app.models.conversation import ConversationStateDB

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, db: Session):
        self.db = db
    
    def start_agent_session(self, conversation_id: str) -> AgentSessionDB:
        """Start a new agent session for a customer"""
        # Check if active session already exists
        existing = self.db.query(AgentSessionDB).filter(
            AgentSessionDB.conversation_id == conversation_id,
            AgentSessionDB.status.in_(["waiting", "active"])
        ).first()
        
        if existing:
            logger.info(f"Agent session already exists: {existing.id}")
            return existing
        
        # Create new session
        session = AgentSessionDB(
            conversation_id=conversation_id,
            status="waiting"
        )
        self.db.add(session)
        
        # Add system message
        system_msg = AgentMessageDB(
            session_id=session.id,
            sender_type="system",
            message_text="Customer requested to speak with an agent. Waiting for agent to join..."
        )
        self.db.add(system_msg)
        
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"✅ Created agent session: {session.id}")
        return session
    
    def assign_agent(self, session_id: str, agent_id: str, agent_name: str) -> AgentSessionDB:
        """Assign an agent to a waiting session"""
        session = self.db.query(AgentSessionDB).filter(
            AgentSessionDB.id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.agent_id = agent_id
        session.agent_name = agent_name
        session.status = "active"
        session.updated_at = datetime.utcnow()
        
        # Add system message
        system_msg = AgentMessageDB(
            session_id=session.id,
            sender_type="system",
            message_text=f"{agent_name} has joined the chat"
        )
        self.db.add(system_msg)
        
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"✅ Agent {agent_name} assigned to session {session_id}")
        return session
    
    def end_agent_session(self, session_id: str) -> AgentSessionDB:
        """End an active agent session"""
        session = self.db.query(AgentSessionDB).filter(
            AgentSessionDB.id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.status = "ended"
        session.ended_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        
        # Add system message
        system_msg = AgentMessageDB(
            session_id=session.id,
            sender_type="system",
            message_text="Chat session ended. Type 'menu' to return to main menu."
        )
        self.db.add(system_msg)
        
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"✅ Ended agent session: {session_id}")
        return session
    
    def save_message(
        self,
        session_id: str,
        sender_type: str,
        message_text: str,
        sender_id: Optional[str] = None,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> AgentMessageDB:
        """Save a message in the agent chat"""
        message = AgentMessageDB(
            session_id=session_id,
            sender_type=sender_type,
            sender_id=sender_id,
            message_text=message_text,
            media_url=media_url,
            media_type=media_type
        )
        self.db.add(message)
        
        # Update session's last_message_at
        session = self.db.query(AgentSessionDB).filter(
            AgentSessionDB.id == session_id
        ).first()
        if session:
            session.last_message_at = datetime.utcnow()
            session.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def get_active_session_by_phone(self, phone_number: str) -> Optional[AgentSessionDB]:
        """Get active agent session for a phone number"""
        conversation = self.db.query(ConversationStateDB).filter(
            ConversationStateDB.phone_number == phone_number
        ).first()
        
        if not conversation:
            return None
        
        session = self.db.query(AgentSessionDB).filter(
            AgentSessionDB.conversation_id == conversation.id,
            AgentSessionDB.status.in_(["waiting", "active"])
        ).first()
        
        return session
    
    def get_waiting_sessions(self) -> List[AgentSessionResponse]:
        """Get all sessions waiting for an agent"""
        sessions = self.db.query(AgentSessionDB).filter(
            AgentSessionDB.status == "waiting"
        ).order_by(AgentSessionDB.created_at).all()
        
        result = []
        for session in sessions:
            conversation = self.db.query(ConversationStateDB).filter(
                ConversationStateDB.id == session.conversation_id
            ).first()
            
            if conversation:
                result.append(AgentSessionResponse(
                    id=str(session.id),
                    conversation_id=str(session.conversation_id),
                    phone_number=conversation.phone_number,
                    customer_name=conversation.context.get("name"),
                    agent_id=session.agent_id,
                    agent_name=session.agent_name,
                    status=session.status,
                    started_at=session.started_at,
                    ended_at=session.ended_at,
                    last_message_at=session.last_message_at
                ))
        
        return result
    
    def get_agent_sessions(self, agent_id: str) -> List[AgentSessionResponse]:
        """Get all active sessions for a specific agent"""
        sessions = self.db.query(AgentSessionDB).filter(
            AgentSessionDB.agent_id == agent_id,
            AgentSessionDB.status == "active"
        ).order_by(AgentSessionDB.last_message_at.desc()).all()
        
        result = []
        for session in sessions:
            conversation = self.db.query(ConversationStateDB).filter(
                ConversationStateDB.id == session.conversation_id
            ).first()
            
            if conversation:
                result.append(AgentSessionResponse(
                    id=str(session.id),
                    conversation_id=str(session.conversation_id),
                    phone_number=conversation.phone_number,
                    customer_name=conversation.context.get("name"),
                    agent_id=session.agent_id,
                    agent_name=session.agent_name,
                    status=session.status,
                    started_at=session.started_at,
                    ended_at=session.ended_at,
                    last_message_at=session.last_message_at
                ))
        
        return result
    
    def get_session_messages(self, session_id: str, limit: int = 100) -> List[AgentMessageDB]:
        """Get all messages in a session"""
        messages = self.db.query(AgentMessageDB).filter(
            AgentMessageDB.session_id == session_id
        ).order_by(AgentMessageDB.timestamp.asc()).limit(limit).all()
        
        return messages
    
    def expire_old_sessions(self) -> int:
        """Auto-expire sessions that have exceeded 22 hours"""
        expired_sessions = self.db.query(AgentSessionDB).filter(
            AgentSessionDB.status.in_(["waiting", "active"]),
            AgentSessionDB.expires_at <= datetime.utcnow()
        ).all()
        
        count = 0
        for session in expired_sessions:
            session.status = "ended"
            session.ended_at = datetime.utcnow()
            session.updated_at = datetime.utcnow()
            
            # Add system message
            system_msg = AgentMessageDB(
                session_id=session.id,
                sender_type="system",
                message_text="Chat session automatically ended after 22 hours."
            )
            self.db.add(system_msg)
            count += 1
        
        if count > 0:
            self.db.commit()
            logger.info(f"⏰ Auto-expired {count} agent sessions")
        
        return count
```

### 3. Update Message Handler (`backend/app/services/message_handler.py`)

Add this method to handle agent mode:

```python
async def _handle_agent_mode(
    self,
    phone_number: str,
    message_text: str,
    conversation: Any
) -> Dict[str, Any]:
    """Handle messages when customer is in agent chat mode"""
    from app.services.agent_service import AgentService
    from app.whatsapp_api import send_whatsapp_message
    
    agent_service = AgentService(self.db)
    
    # Get active agent session
    session = agent_service.get_active_session_by_phone(phone_number)
    
    if not session:
        logger.error(f"No active agent session found for {phone_number}")
        return {"status": "error"}
    
    # Check if customer wants to end chat
    if message_text.lower().strip() in ["end chat", "end", "quit", "exit"]:
        agent_service.end_agent_session(str(session.id))
        
        await send_whatsapp_message(
            phone_number,
            {"type": "text", "content": "Chat ended. Type 'menu' to return to the main menu."}
        )
        
        # End conversation
        self.conv_service.end_conversation(phone_number)
        return {"status": "agent_session_ended"}
    
    # Save customer message
    agent_service.save_message(
        session_id=str(session.id),
        sender_type="customer",
        message_text=message_text
    )
    
    logger.info(f"💬 Customer message saved to agent session: {session.id}")
    
    # If session is still waiting for agent
    if session.status == "waiting":
        await send_whatsapp_message(
            phone_number,
            {"type": "text", "content": "Please wait, an agent will be with you shortly..."}
        )
    
    # Notify agent via WebSocket (handled separately)
    # This would trigger a real-time notification to the agent dashboard
    
    return {"status": "message_forwarded_to_agent", "session_id": str(session.id)}
```

Update the main `handle_message` method to check for agent mode:

```python
async def handle_message(self, phone_number: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for handling incoming messages"""
    
    # Get or create conversation
    conversation = self.conv_service.get_conversation(phone_number)
    
    # Check if in agent mode
    if conversation:
        from app.services.agent_service import AgentService
        agent_service = AgentService(self.db)
        agent_session = agent_service.get_active_session_by_phone(phone_number)
        
        if agent_session and agent_session.status in ["waiting", "active"]:
            # Route to agent handler
            return await self._handle_agent_mode(
                phone_number,
                message_data.get("text", ""),
                conversation
            )
    
    # ... rest of existing logic
```

### 4. Create API Endpoints (`backend/app/api/agent_routes.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.services.agent_service import AgentService
from app.services.conversation_service import ConversationService
from app.models.agent import AgentSessionResponse, AgentMessageResponse, AgentMessageCreate
from app.whatsapp_api import send_whatsapp_message
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["agent"])

@router.post("/sessions/start/{phone_number}")
async def start_agent_session(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """Customer requests to talk to an agent"""
    conv_service = ConversationService(db)
    agent_service = AgentService(db)
    
    # Get or create conversation
    conversation = conv_service.get_conversation(phone_number)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Start agent session
    session = agent_service.start_agent_session(str(conversation.id))
    
    # Send confirmation to customer
    await send_whatsapp_message(
        phone_number,
        {
            "type": "text",
            "content": "🙋 Connecting you to an agent...\nPlease wait while we find someone to help you.\n\nType 'end chat' to return to the menu."
        }
    )
    
    return {
        "status": "success",
        "session_id": str(session.id),
        "message": "Agent session started"
    }

@router.get("/sessions/waiting", response_model=List[AgentSessionResponse])
def get_waiting_sessions(db: Session = Depends(get_db)):
    """Get all customers waiting for an agent"""
    agent_service = AgentService(db)
    return agent_service.get_waiting_sessions()

@router.get("/sessions/my-chats/{agent_id}", response_model=List[AgentSessionResponse])
def get_my_chats(agent_id: str, db: Session = Depends(get_db)):
    """Get all active chats for an agent"""
    agent_service = AgentService(db)
    return agent_service.get_agent_sessions(agent_id)

@router.post("/sessions/{session_id}/assign")
async def assign_agent_to_session(
    session_id: str,
    agent_id: str,
    agent_name: str,
    db: Session = Depends(get_db)
):
    """Agent accepts a waiting session"""
    agent_service = AgentService(db)
    conv_service = ConversationService(db)
    
    try:
        session = agent_service.assign_agent(session_id, agent_id, agent_name)
        
        # Get conversation to send WhatsApp message
        conversation = conv_service.get_conversation_by_id(str(session.conversation_id))
        if conversation:
            await send_whatsapp_message(
                conversation.phone_number,
                {
                    "type": "text",
                    "content": f"✅ {agent_name} is now chatting with you.\n\nFeel free to ask your questions!"
                }
            )
        
        return {
            "status": "success",
            "session_id": str(session.id),
            "message": f"Agent {agent_name} assigned"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/sessions/{session_id}/end")
async def end_agent_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """End an agent session"""
    agent_service = AgentService(db)
    conv_service = ConversationService(db)
    
    try:
        session = agent_service.end_agent_session(session_id)
        
        # Notify customer
        conversation = conv_service.get_conversation_by_id(str(session.conversation_id))
        if conversation:
            await send_whatsapp_message(
                conversation.phone_number,
                {
                    "type": "text",
                    "content": "✅ Chat ended.\n\nType 'menu' to return to the main menu."
                }
            )
            
            # End conversation
            conv_service.end_conversation(conversation.phone_number)
        
        return {
            "status": "success",
            "message": "Session ended"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/sessions/{session_id}/messages", response_model=List[AgentMessageResponse])
def get_session_messages(
    session_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all messages in a session"""
    agent_service = AgentService(db)
    messages = agent_service.get_session_messages(session_id, limit)
    
    return [
        AgentMessageResponse(
            id=str(msg.id),
            session_id=str(msg.session_id),
            sender_type=msg.sender_type,
            sender_id=msg.sender_id,
            message_text=msg.message_text,
            media_url=msg.media_url,
            media_type=msg.media_type,
            timestamp=msg.timestamp
        )
        for msg in messages
    ]

@router.post("/sessions/{session_id}/messages")
async def send_agent_message(
    session_id: str,
    message: AgentMessageCreate,
    db: Session = Depends(get_db)
):
    """Agent sends a message to customer"""
    agent_service = AgentService(db)
    conv_service = ConversationService(db)
    
    # Save message to database
    saved_msg = agent_service.save_message(
        session_id=session_id,
        sender_type=message.sender_type,
        sender_id=message.sender_id,
        message_text=message.message_text,
        media_url=message.media_url,
        media_type=message.media_type
    )
    
    # Send to customer via WhatsApp
    if message.sender_type == "agent":
        # Get session to find phone number
        session = db.query(AgentSessionDB).filter(
            AgentSessionDB.id == session_id
        ).first()
        
        if session:
            conversation = conv_service.get_conversation_by_id(str(session.conversation_id))
            if conversation:
                await send_whatsapp_message(
                    conversation.phone_number,
                    {
                        "type": "text",
                        "content": message.message_text
                    }
                )
    
    return {
        "status": "success",
        "message_id": str(saved_msg.id)
    }

@router.get("/sessions/history", response_model=List[AgentSessionResponse])
def get_chat_history(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get chat history with filters
    
    Query params:
    - agent_id: Filter by specific agent (optional, shows all if not provided)
    - status: Filter by status ('waiting', 'active', 'ended')
    - search: Search in phone number or customer name
    - start_date: Filter from date (YYYY-MM-DD)
    - end_date: Filter to date (YYYY-MM-DD)
    - limit: Number of results (default 50)
    - offset: Pagination offset (default 0)
    """
    from sqlalchemy import or_, and_
    from datetime import datetime
    
    query = db.query(AgentSessionDB)
    
    # Filter by agent (if provided)
    if agent_id:
        query = query.filter(AgentSessionDB.agent_id == agent_id)
    
    # Filter by status (default to 'ended' for history)
    if status:
        query = query.filter(AgentSessionDB.status == status)
    else:
        query = query.filter(AgentSessionDB.status == 'ended')
    
    # Date range filter
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(AgentSessionDB.created_at >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(AgentSessionDB.created_at <= end_dt)
    
    # Get sessions with conversation data for search
    sessions = query.order_by(AgentSessionDB.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for session in sessions:
        conversation = db.query(ConversationStateDB).filter(
            ConversationStateDB.id == session.conversation_id
        ).first()
        
        if conversation:
            # Search filter (applied after query for simplicity)
            if search:
                search_lower = search.lower()
                customer_name = conversation.context.get("name", "").lower()
                phone = conversation.phone_number.lower()
                
                if search_lower not in phone and search_lower not in customer_name:
                    continue
            
            # Count messages in this session
            message_count = db.query(AgentMessageDB).filter(
                AgentMessageDB.session_id == session.id
            ).count()
            
            result.append(AgentSessionResponse(
                id=str(session.id),
                conversation_id=str(session.conversation_id),
                phone_number=conversation.phone_number,
                customer_name=conversation.context.get("name"),
                agent_id=session.agent_id,
                agent_name=session.agent_name,
                status=session.status,
                started_at=session.started_at,
                ended_at=session.ended_at,
                expires_at=session.expires_at,
                last_message_at=session.last_message_at,
                unread_count=message_count  # Reusing this field for message count
            ))
    
    return result

@router.get("/sessions/all", response_model=List[AgentSessionResponse])
def get_all_sessions(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all sessions regardless of agent (for admin/supervisor view)"""
    query = db.query(AgentSessionDB)
    
    if status:
        query = query.filter(AgentSessionDB.status == status)
    else:
        # Default: show waiting and active
        query = query.filter(AgentSessionDB.status.in_(['waiting', 'active']))
    
    sessions = query.order_by(AgentSessionDB.last_message_at.desc()).all()
    
    result = []
    for session in sessions:
        conversation = db.query(ConversationStateDB).filter(
            ConversationStateDB.id == session.conversation_id
        ).first()
        
        if conversation:
            result.append(AgentSessionResponse(
                id=str(session.id),
                conversation_id=str(session.conversation_id),
                phone_number=conversation.phone_number,
                customer_name=conversation.context.get("name"),
                agent_id=session.agent_id,
                agent_name=session.agent_name,
                status=session.status,
                started_at=session.started_at,
                ended_at=session.ended_at,
                expires_at=session.expires_at,
                last_message_at=session.last_message_at
            ))
    
    return result
```

Register routes in `backend/app/main.py`:

```python
from app.api import agent_routes

app.include_router(agent_routes.router)
```

### 5. Add "Talk to Expert" Button in Template

In your template creation UI, add a button with `next_steps` pointing to `AGENT_MODE`:

```json
{
  "header": {
    "type": "text",
    "text": "✨ Welcome to Our Store"
  },
  "body": {
    "text": "How can we help you today? Choose an option below:"
  },
  "footer": {
    "text": "We're here to assist you"
  },
  "action": {
    "buttons": [
      {
        "type": "reply",
        "reply": {
          "id": "btn_products",
          "title": "View Products"
        }
      },
      {
        "type": "reply",
        "reply": {
          "id": "btn_agent",
          "title": "Talk to Expert"
        }
      }
    ]
  },
  "steps": {
    "initial": {
      "prompt": "How can we help you today?",
      "next_steps": {
        "btn_products": "products_template",
        "btn_agent": "AGENT_MODE"
      }
    }
  }
}
```

**Key Points:**
- The template structure has `header`, `body`, `footer`, `action`, and `steps` at the root level
- `action.buttons` contains the interactive buttons shown to the user
- `steps.initial.next_steps` maps button IDs to their destinations
- Use `"AGENT_MODE"` as the special value to trigger live agent session

Update message handler to detect `AGENT_MODE`:

```python
async def _process_selection(self, phone_number: str, selection_id: str, conversation: Any):
    """Process button selection"""
    
    # ... existing code ...
    
    next_value = next_steps[selection_id]
    
    # Check for special AGENT_MODE value
    if next_value == "AGENT_MODE":
        from app.services.agent_service import AgentService
        agent_service = AgentService(self.db)
        
        # Start agent session
        session = agent_service.start_agent_session(str(conversation.id))
        
        # Send confirmation
        await send_whatsapp_message(
            phone_number,
            {
                "type": "text",
                "content": "🙋 Connecting you to an agent...\n\nPlease wait while we find someone to help you.\n\nType 'end chat' to return to the menu."
            }
        )
        
        return {
            "status": "agent_mode_started",
            "session_id": str(session.id)
        }
    
    # ... rest of existing logic ...
```

## Frontend - Agent Dashboard

### 1. Create Agent Dashboard App

Create a new React app in `frontend/agent-dashboard/`:

```bash
cd frontend
npx create-react-app agent-dashboard
cd agent-dashboard
npm install axios socket.io-client react-router-dom
```

### 2. API Configuration (`src/config.js`)

```javascript
export const API_URL = 'https://byqpifhtjq.us-east-1.awsapprunner.com';
export const WS_URL = 'wss://byqpifhtjq.us-east-1.awsapprunner.com/ws';
```

### 3. Main Dashboard Component (`src/components/AgentDashboard.js`)

```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';
import ChatWindow from './ChatWindow';
import './AgentDashboard.css';

function AgentDashboard() {
  const [agentId] = useState('agent_' + Math.random().toString(36).substr(2, 9));
  const [agentName, setAgentName] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activeTab, setActiveTab] = useState('active'); // 'active', 'all', 'history'
  const [waitingSessions, setWaitingSessions] = useState([]);
  const [mySessions, setMySessions] = useState([]);
  const [allSessions, setAllSessions] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(null);
  
  // Search and filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ended');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showMyHistory, setShowMyHistory] = useState(true);

  useEffect(() => {
    if (isLoggedIn) {
      fetchData();
      
      // Auto-refresh every 5 seconds
      const interval = setInterval(() => {
        fetchData();
      }, 5000);
      
      setRefreshInterval(interval);
      
      return () => clearInterval(interval);
    }
  }, [isLoggedIn, activeTab, searchQuery, statusFilter, startDate, endDate, showMyHistory]);

  const fetchData = () => {
    if (activeTab === 'active') {
      fetchWaitingSessions();
      fetchMySessions();
    } else if (activeTab === 'all') {
      fetchAllSessions();
    } else if (activeTab === 'history') {
      fetchChatHistory();
    }
  };

  const fetchWaitingSessions = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/agent/sessions/waiting`);
      setWaitingSessions(response.data);
    } catch (error) {
      console.error('Failed to fetch waiting sessions:', error);
    }
  };

  const fetchMySessions = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/agent/sessions/my-chats/${agentId}`);
      setMySessions(response.data);
    } catch (error) {
      console.error('Failed to fetch my sessions:', error);
    }
  };

  const fetchAllSessions = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/agent/sessions/all`);
      setAllSessions(response.data);
    } catch (error) {
      console.error('Failed to fetch all sessions:', error);
    }
  };

  const fetchChatHistory = async () => {
    try {
      const params = {
        search: searchQuery || undefined,
        status: statusFilter || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        agent_id: showMyHistory ? agentId : undefined,
        limit: 100
      };
      
      const response = await axios.get(`${API_URL}/api/agent/sessions/history`, { params });
      setChatHistory(response.data);
    } catch (error) {
      console.error('Failed to fetch chat history:', error);
    }
  };

  const handleLogin = (e) => {
    e.preventDefault();
    if (agentName.trim()) {
      setIsLoggedIn(true);
    }
  };

  const acceptSession = async (sessionId) => {
    try {
      await axios.post(`${API_URL}/api/agent/sessions/${sessionId}/assign`, null, {
        params: {
          agent_id: agentId,
          agent_name: agentName
        }
      });
      
      fetchWaitingSessions();
      fetchMySessions();
      
      // Open the chat window
      const session = waitingSessions.find(s => s.id === sessionId);
      if (session) {
        setActiveSession(session);
      }
    } catch (error) {
      console.error('Failed to accept session:', error);
      alert('Failed to accept session');
    }
  };

  const endSession = async (sessionId) => {
    try {
      await axios.post(`${API_URL}/api/agent/sessions/${sessionId}/end`);
      fetchMySessions();
      if (activeSession && activeSession.id === sessionId) {
        setActiveSession(null);
      }
    } catch (error) {
      console.error('Failed to end session:', error);
    }
  };

  if (!isLoggedIn) {
    return (
      <div className="login-container">
        <div className="login-box">
          <h2>Agent Login</h2>
          <form onSubmit={handleLogin}>
            <input
              type="text"
              placeholder="Enter your name"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              required
            />
            <button type="submit">Login</button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="sidebar">
        <div className="agent-info">
          <h3>👤 {agentName}</h3>
          <p>Agent ID: {agentId}</p>
        </div>

        <div className="waiting-queue">
          <h4>⏰ Waiting Customers ({waitingSessions.length})</h4>
          {waitingSessions.length === 0 ? (
            <p className="empty-message">No customers waiting</p>
          ) : (
            <ul>
              {waitingSessions.map(session => (
                <li key={session.id} className="session-card waiting">
                  <div className="session-info">
                    <strong>{session.customer_name || session.phone_number}</strong>
                    <span className="waiting-time">
                      Waiting {Math.floor((Date.now() - new Date(session.started_at)) / 60000)} min
                    </span>
                  </div>
                  <button 
                    onClick={() => acceptSession(session.id)}
                    className="btn-accept"
                  >
                    Accept
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="active-chats">
          <h4>💬 My Active Chats ({mySessions.length})</h4>
          {mySessions.length === 0 ? (
            <p className="empty-message">No active chats</p>
          ) : (
            <ul>
              {mySessions.map(session => (
                <li 
                  key={session.id} 
                  className={`session-card active ${activeSession?.id === session.id ? 'selected' : ''}`}
                  onClick={() => setActiveSession(session)}
                >
                  <div className="session-info">
                    <strong>{session.customer_name || session.phone_number}</strong>
                    <span className="last-message">
                      {new Date(session.last_message_at).toLocaleTimeString()}
                    </span>
                  </div>
                  {session.unread_count > 0 && (
                    <span className="unread-badge">{session.unread_count}</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="chat-area">
        {activeSession ? (
          <ChatWindow 
            session={activeSession}
            agentId={agentId}
            agentName={agentName}
            onEndSession={() => endSession(activeSession.id)}
            isHistorical={activeTab === 'history'}
          />
        ) : (
          <div className="no-chat-selected">
            <h3>Select a chat to start messaging</h3>
            {activeTab === 'history' && (
              <p>Use the filters to search chat history</p>
            )}
            {activeTab === 'all' && (
              <p>Showing all active sessions from all agents</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default AgentDashboard;
```

### 4. Chat Window Component (`src/components/ChatWindow.js`)

```javascript
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { API_URL } from '../config';
import './ChatWindow.css';

function ChatWindow({ session, agentId, agentName, onEndSession, isHistorical = false }) {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchMessages();
    
    // Only poll if not historical (ended sessions don't need polling)
    if (!isHistorical) {
      const interval = setInterval(fetchMessages, 2000);
      return () => clearInterval(interval);
    }
  }, [session.id, isHistorical]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/agent/sessions/${session.id}/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputText.trim() || isHistorical) return;

    try {
      await axios.post(`${API_URL}/api/agent/sessions/${session.id}/messages`, {
        session_id: session.id,
        sender_type: 'agent',
        sender_id: agentId,
        message_text: inputText
      });

      setInputText('');
      fetchMessages();
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Failed to send message');
    }
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <div>
          <h3>{session.customer_name || session.phone_number}</h3>
          <div className="header-meta">
            <span className={`status-badge ${session.status}`}>{session.status}</span>
            {isHistorical && (
              <span className="historical-badge">📚 History</span>
            )}
            {session.started_at && (
              <span className="session-date">
                {new Date(session.started_at).toLocaleString()}
              </span>
            )}
          </div>
        </div>
        {!isHistorical && session.status !== 'ended' && (
          <button onClick={onEndSession} className="btn-end-chat">
            End Chat
          </button>
        )}
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-messages">
            <p>No messages in this conversation</p>
          </div>
        ) : (
          messages.map(msg => (
            <div 
              key={msg.id} 
              className={`message ${msg.sender_type}`}
            >
              <div className="message-content">
                {msg.sender_type === 'system' && (
                  <span className="system-label">🔔 System</span>
                )}
                {msg.sender_type === 'agent' && (
                  <span className="agent-label">
                    {msg.sender_id === agentId ? '👤 You' : `👤 ${session.agent_name || 'Agent'}`}
                  </span>
                )}
                {msg.sender_type === 'customer' && (
                  <span className="customer-label">💬 Customer</span>
                )}
                <p>{msg.message_text}</p>
                <span className="timestamp">
                  {new Date(msg.timestamp).toLocaleString()}
                </span>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {isHistorical ? (
        <div className="historical-notice">
          <p>📚 This is a historical conversation (read-only)</p>
        </div>
      ) : (
        <form className="message-input-form" onSubmit={sendMessage}>
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type your message..."
            className="message-input"
            disabled={session.status === 'ended'}
          />
          <button 
            type="submit" 
            className="btn-send"
            disabled={session.status === 'ended'}
          >
            Send
          </button>
        </form>
      )}
    </div>
  );
}

export default ChatWindow;
```

### 5. Styling (`src/components/AgentDashboard.css`)

```css
.dashboard-container {
  display: flex;
  height: 100vh;
  background: #f5f5f5;
}

.sidebar {
  width: 300px;
  background: white;
  border-right: 1px solid #ddd;
  display: flex;
  flex-direction: column;
}

.agent-info {
  padding: 20px;
  border-bottom: 1px solid #ddd;
  background: #4CAF50;
  color: white;
}

.agent-info h3 {
  margin: 0 0 5px 0;
}

.agent-info p {
  margin: 0;
  font-size: 12px;
  opacity: 0.9;
}

.waiting-queue, .active-chats {
  padding: 15px;
  overflow-y: auto;
}

.waiting-queue h4, .active-chats h4 {
  margin: 0 0 10px 0;
}

.session-card {
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.session-card.waiting {
  background: #fff3cd;
  border-color: #ffc107;
}

.session-card.active {
  background: white;
}

.session-card.active.selected {
  background: #e3f2fd;
  border-color: #2196F3;
}

.session-card:hover {
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.session-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.waiting-time, .last-message {
  font-size: 12px;
  color: #666;
}

.btn-accept {
  width: 100%;
  padding: 8px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-accept:hover {
  background: #45a049;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.no-chat-selected {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}

.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  width: 300px;
}

.login-box h2 {
  margin-top: 0;
  text-align: center;
}

.login-box input {
  width: 100%;
  padding: 12px;
  margin-bottom: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.login-box button {
  width: 100%;
  padding: 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

.login-box button:hover {
  background: #5568d3;
}

/* Tab Navigation */
.tab-navigation {
  display: flex;
  border-bottom: 2px solid #ddd;
  background: white;
}

.tab-btn {
  flex: 1;
  padding: 12px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  border-bottom: 3px solid transparent;
}

.tab-btn.active {
  color: #2196F3;
  border-bottom-color: #2196F3;
  font-weight: bold;
}

.tab-btn:hover {
  background: #f5f5f5;
}

/* History Section */
.history-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.history-filters {
  padding: 15px;
  background: #f8f9fa;
  border-bottom: 1px solid #ddd;
}

.search-input {
  width: 100%;
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.date-filters {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.date-input {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 14px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
}

.status-select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}

.session-card.history {
  background: #f8f9fa;
  border-left: 4px solid #6c757d;
}

.session-card.history.selected {
  background: #e7f3ff;
  border-left-color: #2196F3;
}

.session-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 5px;
  font-size: 12px;
  color: #666;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: bold;
  text-transform: uppercase;
}

.status-badge.waiting {
  background: #fff3cd;
  color: #856404;
}

.status-badge.active {
  background: #d4edda;
  color: #155724;
}

.status-badge.ended {
  background: #f8d7da;
  color: #721c24;
}

.agent-badge, .agent-info-small {
  font-size: 12px;
  color: #666;
}

.duration, .msg-count {
  background: #e9ecef;
  padding: 2px 6px;
  border-radius: 4px;
}

/* Chat Window Updates */
.header-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 5px;
}

.historical-badge {
  padding: 4px 8px;
  background: #6c757d;
  color: white;
  border-radius: 4px;
  font-size: 12px;
}

.session-date {
  font-size: 12px;
  color: #666;
}

.empty-messages {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}

.historical-notice {
  padding: 15px;
  background: #f8f9fa;
  border-top: 1px solid #ddd;
  text-align: center;
  color: #666;
  font-size: 14px;
}

.message-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.btn-send:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* All Sessions List */
.all-sessions-list {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}
```

## Deployment Steps

### 1. Run Migration

```bash
cd backend/migrations
psql "postgresql://postgres@your-rds.amazonaws.com:5432/whatsapp_business_development" -f add_live_agent_tables.sql
```

### 2. Create Background Worker for Auto-Expiration

Create `/backend/app/workers/agent_expiration_worker.py`:

```python
"""
Background worker to auto-expire agent sessions after 22 hours
Run this as a separate process or cron job
"""
import asyncio
import logging
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

async def expire_old_sessions():
    """Check and expire sessions that have exceeded 22 hours"""
    from app.services.agent_service import AgentService
    from app.services.conversation_service import ConversationService
    from app.whatsapp_api import send_whatsapp_message
    
    db = SessionLocal()
    try:
        agent_service = AgentService(db)
        conv_service = ConversationService(db)
        
        # Get expired sessions
        expired_count = agent_service.expire_old_sessions()
        
        if expired_count > 0:
            logger.info(f"⏰ Expired {expired_count} agent sessions")
            
            # Notify customers via WhatsApp
            from app.models.agent import AgentSessionDB
            from app.models.conversation import ConversationStateDB
            
            # Get recently expired sessions (last minute)
            recent_expired = db.query(AgentSessionDB).filter(
                AgentSessionDB.status == "ended",
                AgentSessionDB.ended_at >= datetime.utcnow() - timedelta(minutes=1)
            ).all()
            
            for session in recent_expired:
                conversation = db.query(ConversationStateDB).filter(
                    ConversationStateDB.id == session.conversation_id
                ).first()
                
                if conversation:
                    try:
                        await send_whatsapp_message(
                            conversation.phone_number,
                            {
                                "type": "text",
                                "content": "⏰ Your chat session has automatically ended after 22 hours.\\n\\nType 'menu' to return to the main menu."
                            }
                        )
                        
                        # End the conversation
                        conv_service.end_conversation(conversation.phone_number)
                        
                        logger.info(f"✅ Notified customer {conversation.phone_number} about expiration")
                    except Exception as e:
                        logger.error(f"Failed to notify {conversation.phone_number}: {e}")
        
    except Exception as e:
        logger.error(f"Error in expiration worker: {e}")
    finally:
        db.close()

async def run_worker():
    """Main worker loop - runs every 5 minutes"""
    logger.info("🚀 Agent expiration worker started")
    
    while True:
        try:
            await expire_old_sessions()
            
            # Sleep for 5 minutes
            await asyncio.sleep(300)
            
        except KeyboardInterrupt:
            logger.info("⏹️  Worker stopped by user")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retry

if __name__ == "__main__":
    # Run the worker
    asyncio.run(run_worker())
```

### 3. Add Worker Startup Script

Create `/backend/start_agent_worker.sh`:

```bash
#!/bin/bash
# Start the agent expiration worker

cd /Users/abskchsk/Documents/govindjis/wa-app/backend

# Activate virtual environment if using one
# source venv/bin/activate

# Set environment variables
export $(cat .env | xargs)

# Run worker
python -m app.workers.agent_expiration_worker
```

Make it executable:
```bash
chmod +x backend/start_agent_worker.sh
```

### 4. Run Worker Locally (for testing)

```bash
cd backend
python -m app.workers.agent_expiration_worker
```

### 5. Deploy Worker to AWS (Production)

**Option A: Run as systemd service on EC2**

Create `/etc/systemd/system/agent-expiration-worker.service`:

```ini
[Unit]
Description=WhatsApp Agent Session Expiration Worker
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/wa-app/backend
Environment="DATABASE_URL=postgresql://postgres:password@rds-endpoint:5432/whatsapp_business"
ExecStart=/usr/bin/python3 -m app.workers.agent_expiration_worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable agent-expiration-worker
sudo systemctl start agent-expiration-worker
sudo systemctl status agent-expiration-worker
```

**Option B: Run as AWS Lambda (scheduled with EventBridge)**

Create `/backend/lambda_expiration_handler.py`:

```python
import asyncio
from app.workers.agent_expiration_worker import expire_old_sessions

def lambda_handler(event, context):
    """Lambda handler triggered by EventBridge every 5 minutes"""
    asyncio.run(expire_old_sessions())
    
    return {
        'statusCode': 200,
        'body': 'Agent expiration check completed'
    }
```

Deploy to Lambda and create EventBridge rule:
```bash
# Create Lambda deployment package
cd backend
zip -r agent_expiration.zip app/ lambda_expiration_handler.py

# Upload to Lambda (or use AWS SAM/Terraform)
aws lambda create-function --function-name agent-expiration-worker \
    --runtime python3.12 \
    --handler lambda_expiration_handler.lambda_handler \
    --zip-file fileb://agent_expiration.zip

# Create EventBridge rule to run every 5 minutes
aws events put-rule --name agent-expiration-schedule \
    --schedule-expression "rate(5 minutes)"

aws events put-targets --rule agent-expiration-schedule \
    --targets "Id"="1","Arn"="arn:aws:lambda:region:account:function:agent-expiration-worker"
```

**Option C: Use existing cron on server**

Add to crontab:
```bash
# Run every 5 minutes
*/5 * * * * cd /path/to/wa-app/backend && python -m app.workers.agent_expiration_worker --once
```

Update worker to support `--once` flag:

```python
if __name__ == "__main__":
    import sys
    
    if "--once" in sys.argv:
        # Run once and exit (for cron)
        asyncio.run(expire_old_sessions())
    else:
        # Run continuously
        asyncio.run(run_worker())
```

### 6. Deploy Backend

```bash
git add .
git commit -m "Add live agent feature with 22-hour auto-expiration"
git push origin main
```

### 7. Deploy Agent Dashboard

```bash
cd frontend/agent-dashboard
npm run build

# Deploy to S3 + CloudFront or Vercel
aws s3 sync build/ s3://your-agent-dashboard-bucket/
```

## Testing Flow

1. **Customer Side (WhatsApp)**:
   - Customer sends "hi" to bot
   - Bot shows menu with "Talk to Expert" button
   - Customer clicks "Talk to Expert"
   - Bot says "Connecting to agent..."

2. **Agent Side (Dashboard)**:
   - Agent opens dashboard and logs in
   - Sees customer in "Waiting" queue
   - Clicks "Accept" button
   - Chat window opens

3. **Live Chat**:
   - Customer sees "Agent has joined"
   - Both parties can exchange messages
   - Messages appear in real-time
   - Either party can end chat

4. **End Chat**:
   - Agent clicks "End Chat" or customer types "end chat"
   - Customer returns to bot menu
   - Conversation history saved in database

5. **Auto-Expiration (22 Hours)**:
   - Background worker checks every 5 minutes
   - Sessions older than 22 hours are automatically ended
   - Customer receives notification: "Chat session ended after 22 hours"
   - Customer can type 'menu' to return to main menu

## Session Expiration Details

### How It Works

1. **Session Creation**: When agent session starts, `expires_at` is automatically set to `CURRENT_TIMESTAMP + 22 hours`

2. **Background Worker**: Runs every 5 minutes checking for expired sessions
   ```sql
   SELECT * FROM agent_sessions 
   WHERE status IN ('waiting', 'active') 
   AND expires_at <= CURRENT_TIMESTAMP
   ```

3. **Auto-End Process**:
   - Updates session status to 'ended'
   - Sets ended_at timestamp
   - Adds system message to chat history
   - Sends WhatsApp notification to customer
   - Ends the conversation state

4. **Customer Notification**: 
   ```
   ⏰ Your chat session has automatically ended after 22 hours.
   
   Type 'menu' to return to the main menu.
   ```

### Manual vs Auto-End

| Method | Triggered By | Notification | Conversation Ended |
|--------|-------------|-------------|-------------------|
| Manual | Agent clicks "End Chat" | ✅ Yes | ✅ Yes |
| Manual | Customer types "end chat" | ✅ Yes | ✅ Yes |
| Auto | Background worker (22hrs) | ✅ Yes | ✅ Yes |

### Monitoring Expiration

Check sessions nearing expiration:
```sql
SELECT 
    id,
    conversation_id,
    agent_name,
    status,
    started_at,
    expires_at,
    EXTRACT(EPOCH FROM (expires_at - CURRENT_TIMESTAMP))/3600 as hours_remaining
FROM agent_sessions
WHERE status IN ('waiting', 'active')
ORDER BY expires_at ASC;
```

View expiration worker logs:
```bash
# If running as systemd service
sudo journalctl -u agent-expiration-worker -f

# If running manually
tail -f /var/log/agent-expiration-worker.log
```

## Enhancements

1. **WebSocket for Real-Time**: Replace polling with WebSocket connections
2. **Push Notifications**: Notify agents when new customers arrive
3. **Typing Indicators**: Show when agent/customer is typing
4. **File Uploads**: Allow sharing images/documents
5. **Canned Responses**: Quick reply templates for agents
6. **Chat History**: View past conversations
7. **Analytics**: Track response times, customer satisfaction
8. **Multi-Agent Support**: Load balancing across multiple agents

This implementation provides a complete foundation for live agent support in your WhatsApp automation system!
