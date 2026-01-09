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
        self.db.flush()  # Flush to get the session.id
        
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
                    expires_at=session.expires_at,
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
                    expires_at=session.expires_at,
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
