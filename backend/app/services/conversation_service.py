"""
Conversation and Template Management Service
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.conversation import (
    ConversationStateDB, 
    WorkflowTemplateDB,
    TemplateType
)
from app.core.logging import logger

class ConversationService:
    """Service for managing conversations and templates"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================================================
    # WORKFLOW TEMPLATE METHODS
    # ============================================================================
    
    def create_template(
        self,
        template_name: str,
        template_type: str,
        menu_structure: Dict[str, Any],
        trigger_keywords: List[str] = None,
        is_active: bool = True
    ) -> WorkflowTemplateDB:
        """
        Create a new workflow template
        
        Args:
            template_name: Unique name for the template
            template_type: 'button', 'list', or 'text'
            menu_structure: Complete menu definition as dict
            trigger_keywords: Optional keywords that trigger this template
            is_active: Whether template is active
            
        Returns:
            Created template
        """
        template = WorkflowTemplateDB(
            template_name=template_name,
            template_type=template_type,
            trigger_keywords=trigger_keywords or [],
            menu_structure=menu_structure,
            is_active=is_active
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"✅ Created template: {template_name}")
        return template
    
    def get_template(self, template_name: str) -> Optional[WorkflowTemplateDB]:
        """Get a template by name"""
        return self.db.query(WorkflowTemplateDB).filter(
            WorkflowTemplateDB.template_name == template_name
        ).first()
    
    def get_active_templates(self) -> List[WorkflowTemplateDB]:
        """Get all active templates"""
        return self.db.query(WorkflowTemplateDB).filter(
            WorkflowTemplateDB.is_active == True
        ).all()
    
    def find_template_by_keyword(self, text: str) -> Optional[WorkflowTemplateDB]:
        """
        Find a template that matches keywords in the text
        
        Args:
            text: User's message text
            
        Returns:
            Matching template or None
        """
        text_lower = text.lower().strip()
        
        templates = self.get_active_templates()
        
        for template in templates:
            if not template.trigger_keywords:
                continue
                
            for keyword in template.trigger_keywords:
                if keyword.lower() in text_lower:
                    logger.info(f"🎯 Template '{template.template_name}' matched keyword '{keyword}'")
                    return template
        
        return None
    
    def update_template(
        self,
        template_name: str,
        **kwargs
    ) -> Optional[WorkflowTemplateDB]:
        """Update a template"""
        template = self.get_template(template_name)
        if not template:
            return None
        
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"✅ Updated template: {template_name}")
        return template
    
    def delete_template(self, template_name: str) -> bool:
        """Delete a template"""
        template = self.get_template(template_name)
        if not template:
            return False
        
        self.db.delete(template)
        self.db.commit()
        
        logger.info(f"🗑️ Deleted template: {template_name}")
        return True
    
    # ============================================================================
    # CONVERSATION STATE METHODS
    # ============================================================================
    
    def start_conversation(
        self,
        phone_number: str,
        template_name: str,
        initial_step: str = "initial",
        context: Dict[str, Any] = None,
        expiry_hours: int = 24
    ) -> ConversationStateDB:
        """
        Start a new conversation for a customer
        
        Args:
            phone_number: Customer's phone number
            template_name: Which template to use
            initial_step: Starting step
            context: Initial context data
            expiry_hours: Hours until conversation expires
            
        Returns:
            Created conversation state
        """
        # Check if customer already has an active conversation
        existing = self.get_conversation(phone_number)
        if existing:
            logger.info(f"📝 Ending existing conversation for {phone_number}")
            self.end_conversation(phone_number)
        
        # Create new conversation
        conversation = ConversationStateDB(
            phone_number=phone_number,
            conversation_flow=template_name,
            current_step=initial_step,
            context=context or {},
            last_interaction=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=expiry_hours)
        )
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        logger.info(f"🆕 Started conversation: {phone_number} -> {template_name}")
        return conversation
    
    def get_conversation(self, phone_number: str) -> Optional[ConversationStateDB]:
        """Get active conversation for a customer"""
        return self.db.query(ConversationStateDB).filter(
            ConversationStateDB.phone_number == phone_number,
            ConversationStateDB.expires_at > datetime.utcnow()
        ).first()
    
    def update_conversation(
        self,
        phone_number: str,
        current_step: str = None,
        context_update: Dict[str, Any] = None,
        new_template: str = None
    ) -> Optional[ConversationStateDB]:
        """
        Update conversation state
        
        Args:
            phone_number: Customer's phone number
            current_step: New step to move to
            context_update: Data to add/update in context
            new_template: Switch to a different template
            
        Returns:
            Updated conversation or None
        """
        conversation = self.get_conversation(phone_number)
        if not conversation:
            logger.warning(f"⚠️ No active conversation for {phone_number}")
            return None
        
        # Update fields
        if current_step:
            conversation.current_step = current_step
        
        if new_template:
            conversation.conversation_flow = new_template
        
        if context_update:
            # Merge context
            current_context = conversation.context or {}
            current_context.update(context_update)
            conversation.context = current_context
        
        conversation.last_interaction = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(conversation)
        
        logger.info(f"📝 Updated conversation: {phone_number} -> step={current_step}")
        return conversation
    
    def end_conversation(self, phone_number: str) -> bool:
        """End/delete a conversation"""
        conversation = self.get_conversation(phone_number)
        if not conversation:
            return False
        
        self.db.delete(conversation)
        self.db.commit()
        
        logger.info(f"✅ Ended conversation: {phone_number}")
        return True
    
    def cleanup_expired_conversations(self) -> int:
        """Remove expired conversations"""
        count = self.db.query(ConversationStateDB).filter(
            ConversationStateDB.expires_at <= datetime.utcnow()
        ).delete()
        
        self.db.commit()
        
        if count > 0:
            logger.info(f"🧹 Cleaned up {count} expired conversations")
        
        return count
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def get_current_menu(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Get the current menu structure for a customer
        
        Returns:
            Menu structure dict or None
        """
        conversation = self.get_conversation(phone_number)
        if not conversation:
            return None
        
        template = self.get_template(conversation.conversation_flow)
        if not template:
            return None
        
        return template.menu_structure
