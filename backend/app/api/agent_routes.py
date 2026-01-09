from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.connection import get_db
from app.services.agent_service import AgentService
from app.services.conversation_service import ConversationService
from app.models.agent import AgentSessionDB, AgentMessageDB, AgentSessionResponse, AgentMessageResponse, AgentMessageCreate
from app.models.conversation import ConversationStateDB
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
        conversation = db.query(ConversationStateDB).filter(
            ConversationStateDB.id == session.conversation_id
        ).first()
        
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
        conversation = db.query(ConversationStateDB).filter(
            ConversationStateDB.id == session.conversation_id
        ).first()
        
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
            conversation = db.query(ConversationStateDB).filter(
                ConversationStateDB.id == session.conversation_id
            ).first()
            
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
