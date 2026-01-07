# Complete Guide: Using Conversation Tables for Interactive Menus

## Table of Contents
1. [Overview](#overview)
2. [Understanding the Tables](#understanding-the-tables)
3. [Creating Workflow Templates](#creating-workflow-templates)
4. [Managing Conversation State](#managing-conversation-state)
5. [Complete Implementation Example](#complete-implementation-example)
6. [Integration with Message Processing](#integration-with-message-processing)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The conversation system uses two tables that work together:

- **`workflow_templates`** = The reusable menu definitions (like a restaurant menu card)
- **`conversation_state`** = The active conversation tracking (like an order slip)

**Key Concept:**
- You create templates ONCE (they're reusable)
- You create conversation states MANY times (one per active conversation)

---

## Understanding the Tables

### workflow_templates (The Menu Card 📋)

**Purpose:** Store reusable interactive menu templates that can be shown to customers.

**Structure:**
```python
template_name: str        # Unique identifier (e.g., "main_menu")
template_type: str        # "button", "list", or "text"
trigger_keywords: list    # Words that activate this template
menu_structure: dict      # The actual WhatsApp menu structure (JSONB)
is_active: bool          # Can be disabled without deleting
```

**Example Templates:**
1. **Main Menu** - First menu customers see
2. **New Order Flow** - Step-by-step ordering process
3. **Support Menu** - Help and FAQ options
4. **Account Menu** - Profile and settings

### conversation_state (The Order Slip 🧾)

**Purpose:** Track what THIS customer is doing RIGHT NOW.

**Structure:**
```python
phone_number: str         # Customer's phone number
conversation_flow: str    # Which template they're using (TEMPLATE NAME)
current_step: str         # Where they are in that template (STEP)
context: dict            # Their selections/inputs (JSONB)
last_interaction: datetime
expires_at: datetime     # Auto-cleanup old conversations
```

**Important:** Only ONE active conversation per customer at any time!

---

## Creating Workflow Templates

### Step 1: Create a Template Service

Create `backend/app/services/conversation_service.py`:

```python
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
```

### Step 2: Create Initial Templates

Create a script to populate templates: `backend/scripts/create_initial_templates.py`:

```python
"""
Script to create initial workflow templates
Run: python -m scripts.create_initial_templates
"""
from app.core.database import init_database, get_db_session
from app.services.conversation_service import ConversationService

def create_main_menu_template(service: ConversationService):
    """Create the main menu template"""
    
    menu_structure = {
        "type": "button",
        "body": {
            "text": "👋 Welcome to our WhatsApp Business!\n\nHow can we help you today?"
        },
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": {
                        "id": "new_order",
                        "title": "🛒 New Order"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "support",
                        "title": "💬 Support"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "account",
                        "title": "👤 My Account"
                    }
                }
            ]
        },
        "steps": {
            "initial": {
                "next_steps": {
                    "new_order": "order_flow",
                    "support": "support_flow",
                    "account": "account_flow"
                }
            }
        }
    }
    
    service.create_template(
        template_name="main_menu",
        template_type="button",
        menu_structure=menu_structure,
        trigger_keywords=["hi", "hello", "start", "menu", "help"],
        is_active=True
    )
    
    print("✅ Created main_menu template")

def create_new_order_template(service: ConversationService):
    """Create the new order flow template"""
    
    menu_structure = {
        "type": "list",
        "body": {
            "text": "🛒 What would you like to order?"
        },
        "action": {
            "button": "View Products",
            "sections": [
                {
                    "title": "☕ Beverages",
                    "rows": [
                        {"id": "coffee", "title": "Coffee", "description": "$3.50"},
                        {"id": "tea", "title": "Tea", "description": "$2.50"},
                        {"id": "juice", "title": "Fresh Juice", "description": "$4.00"}
                    ]
                },
                {
                    "title": "🍰 Food",
                    "rows": [
                        {"id": "sandwich", "title": "Sandwich", "description": "$6.00"},
                        {"id": "salad", "title": "Salad", "description": "$7.00"},
                        {"id": "pasta", "title": "Pasta", "description": "$9.00"}
                    ]
                }
            ]
        },
        "steps": {
            "initial": {
                "prompt": "Select a product",
                "next_step": "quantity"
            },
            "quantity": {
                "prompt": "How many would you like? (Enter a number)",
                "validation": "number",
                "next_step": "confirmation"
            },
            "confirmation": {
                "prompt": "Confirm your order?",
                "next_step": "complete"
            },
            "complete": {
                "prompt": "Order placed! Your order number is {order_id}",
                "end_conversation": True
            }
        }
    }
    
    service.create_template(
        template_name="new_order",
        template_type="list",
        menu_structure=menu_structure,
        trigger_keywords=["order", "buy", "purchase"],
        is_active=True
    )
    
    print("✅ Created new_order template")

def create_support_template(service: ConversationService):
    """Create the support menu template"""
    
    menu_structure = {
        "type": "button",
        "body": {
            "text": "💬 How can we help you?\n\nChoose a support option:"
        },
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": {
                        "id": "faq",
                        "title": "❓ FAQ"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "track_order",
                        "title": "📦 Track Order"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "contact",
                        "title": "📞 Contact Us"
                    }
                }
            ]
        },
        "steps": {
            "initial": {
                "next_steps": {
                    "faq": "show_faq",
                    "track_order": "track_flow",
                    "contact": "show_contact"
                }
            }
        }
    }
    
    service.create_template(
        template_name="support",
        template_type="button",
        menu_structure=menu_structure,
        trigger_keywords=["support", "help", "question", "problem"],
        is_active=True
    )
    
    print("✅ Created support template")

def create_account_template(service: ConversationService):
    """Create the account menu template"""
    
    menu_structure = {
        "type": "button",
        "body": {
            "text": "👤 Account Menu\n\nManage your account:"
        },
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": {
                        "id": "profile",
                        "title": "📝 My Profile"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "orders",
                        "title": "📦 My Orders"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "settings",
                        "title": "⚙️ Settings"
                    }
                }
            ]
        }
    }
    
    service.create_template(
        template_name="account",
        template_type="button",
        menu_structure=menu_structure,
        trigger_keywords=["account", "profile", "my orders"],
        is_active=True
    )
    
    print("✅ Created account template")

def main():
    """Create all initial templates"""
    print("🚀 Creating initial workflow templates...")
    print("")
    
    init_database()
    
    with get_db_session() as db:
        service = ConversationService(db)
        
        # Create templates
        create_main_menu_template(service)
        create_new_order_template(service)
        create_support_template(service)
        create_account_template(service)
    
    print("")
    print("✅ All templates created successfully!")
    print("")
    print("You can now:")
    print("  1. Send 'hi' to your WhatsApp number to see the main menu")
    print("  2. Send 'order' to trigger the new order flow")
    print("  3. Send 'support' to see the support menu")

if __name__ == "__main__":
    main()
```

---

## Managing Conversation State

### When to Create Conversation States

Conversation states are created automatically when:
1. User sends a trigger keyword (e.g., "hi", "order")
2. User clicks a button that starts a new flow
3. User needs to complete a multi-step process

### Example Flow

**Scenario:** Customer wants to order coffee

```python
# 1. Customer sends "hi"
# System checks: No active conversation exists
# Action: Create conversation state + show main menu

conversation = service.start_conversation(
    phone_number="1234567890",
    template_name="main_menu",
    initial_step="initial"
)
# conversation_flow = "main_menu"
# current_step = "initial"
# context = {}

# 2. Customer clicks "New Order" button
# Action: Switch to order template

service.update_conversation(
    phone_number="1234567890",
    new_template="new_order",
    current_step="initial"
)
# conversation_flow = "new_order"
# current_step = "initial"

# 3. Customer selects "Coffee"
# Action: Save selection, move to quantity step

service.update_conversation(
    phone_number="1234567890",
    current_step="quantity",
    context_update={"product": "coffee", "price": 3.50}
)
# conversation_flow = "new_order"
# current_step = "quantity"
# context = {"product": "coffee", "price": 3.50}

# 4. Customer enters "2"
# Action: Save quantity, move to confirmation

service.update_conversation(
    phone_number="1234567890",
    current_step="confirmation",
    context_update={"quantity": 2, "total": 7.00}
)
# conversation_flow = "new_order"
# current_step = "confirmation"
# context = {"product": "coffee", "price": 3.50, "quantity": 2, "total": 7.00}

# 5. Customer confirms order
# Action: Process order, end conversation

order_id = process_order(conversation.context)
service.end_conversation("1234567890")
# Conversation deleted - customer can start fresh next time
```

---

## Complete Implementation Example

### Create Message Handler

Update `backend/app/services/message_handler.py`:

```python
"""
Interactive Message Handler
Processes user messages and manages conversation flows
"""
from typing import Dict, Any, Optional
from app.services.conversation_service import ConversationService
from app.whatsapp_api import send_whatsapp_message
from app.core.logging import logger

class InteractiveMessageHandler:
    """Handles interactive conversation messages"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.conv_service = ConversationService(db_session)
    
    async def handle_text_message(
        self,
        phone_number: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Handle incoming text message
        
        Returns:
            Processing result
        """
        # Check if user has active conversation
        conversation = self.conv_service.get_conversation(phone_number)
        
        if conversation:
            # Continue existing conversation
            return await self._continue_conversation(phone_number, text, conversation)
        else:
            # Try to match keyword and start new conversation
            return await self._start_new_conversation(phone_number, text)
    
    async def handle_interactive_message(
        self,
        phone_number: str,
        interactive_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle button/list selection
        
        Args:
            phone_number: Customer phone
            interactive_data: Button or list selection data
        """
        # Extract selection
        if interactive_data.get("type") == "button_reply":
            selection_id = interactive_data["button_reply"]["id"]
        elif interactive_data.get("type") == "list_reply":
            selection_id = interactive_data["list_reply"]["id"]
        else:
            return {"status": "unsupported"}
        
        conversation = self.conv_service.get_conversation(phone_number)
        if not conversation:
            logger.warning(f"⚠️ No conversation for interactive message from {phone_number}")
            return {"status": "no_conversation"}
        
        # Process selection based on current step
        return await self._process_selection(phone_number, selection_id, conversation)
    
    async def _start_new_conversation(
        self,
        phone_number: str,
        text: str
    ) -> Dict[str, Any]:
        """Start a new conversation based on keyword"""
        
        # Find matching template
        template = self.conv_service.find_template_by_keyword(text)
        
        if not template:
            logger.info(f"📭 No template matched for: {text}")
            return {"status": "no_match"}
        
        # Start conversation
        conversation = self.conv_service.start_conversation(
            phone_number=phone_number,
            template_name=template.template_name
        )
        
        # Send initial menu
        await self._send_menu(phone_number, template.menu_structure)
        
        return {
            "status": "conversation_started",
            "template": template.template_name
        }
    
    async def _continue_conversation(
        self,
        phone_number: str,
        text: str,
        conversation: Any
    ) -> Dict[str, Any]:
        """Continue existing conversation"""
        
        template = self.conv_service.get_template(conversation.conversation_flow)
        if not template:
            logger.error(f"❌ Template not found: {conversation.conversation_flow}")
            self.conv_service.end_conversation(phone_number)
            return {"status": "error"}
        
        # Get current step definition
        steps = template.menu_structure.get("steps", {})
        current_step_def = steps.get(conversation.current_step, {})
        
        # Validate input if needed
        if current_step_def.get("validation") == "number":
            try:
                quantity = int(text)
                if quantity <= 0:
                    raise ValueError()
            except ValueError:
                await send_whatsapp_message(
                    phone_number,
                    {"type": "text", "text": {"body": "❌ Please enter a valid number"}}
                )
                return {"status": "invalid_input"}
        
        # Store input in context
        context_key = current_step_def.get("context_key", "user_input")
        context_update = {context_key: text}
        
        # Move to next step
        next_step = current_step_def.get("next_step")
        if not next_step:
            logger.error(f"❌ No next step defined for {conversation.current_step}")
            return {"status": "error"}
        
        # Update conversation
        self.conv_service.update_conversation(
            phone_number=phone_number,
            current_step=next_step,
            context_update=context_update
        )
        
        # Send next prompt
        next_step_def = steps.get(next_step, {})
        prompt = next_step_def.get("prompt", "Continue...")
        
        # Replace placeholders with context values
        prompt = self._format_prompt(prompt, conversation.context)
        
        await send_whatsapp_message(
            phone_number,
            {"type": "text", "text": {"body": prompt}}
        )
        
        # Check if conversation should end
        if next_step_def.get("end_conversation"):
            self.conv_service.end_conversation(phone_number)
            return {"status": "conversation_completed"}
        
        return {"status": "step_advanced", "next_step": next_step}
    
    async def _process_selection(
        self,
        phone_number: str,
        selection_id: str,
        conversation: Any
    ) -> Dict[str, Any]:
        """Process button or list selection"""
        
        template = self.conv_service.get_template(conversation.conversation_flow)
        if not template:
            return {"status": "error"}
        
        # Get step definition
        steps = template.menu_structure.get("steps", {})
        current_step_def = steps.get(conversation.current_step, {})
        
        # Determine next step based on selection
        next_steps = current_step_def.get("next_steps", {})
        
        if selection_id in next_steps:
            # Switch template if needed
            next_value = next_steps[selection_id]
            
            if next_value.endswith("_flow"):
                # Start a different flow
                template_name = next_value.replace("_flow", "")
                self.conv_service.update_conversation(
                    phone_number=phone_number,
                    new_template=template_name,
                    current_step="initial",
                    context_update={"previous_selection": selection_id}
                )
                
                # Send new menu
                new_template = self.conv_service.get_template(template_name)
                if new_template:
                    await self._send_menu(phone_number, new_template.menu_structure)
            else:
                # Move to next step in current flow
                self.conv_service.update_conversation(
                    phone_number=phone_number,
                    current_step=next_value,
                    context_update={"selection": selection_id}
                )
        
        return {"status": "selection_processed"}
    
    async def _send_menu(self, phone_number: str, menu_structure: Dict[str, Any]):
        """Send WhatsApp interactive menu"""
        
        menu_type = menu_structure.get("type")
        
        if menu_type == "button":
            # Send button message
            message = {
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": menu_structure.get("body"),
                    "action": menu_structure.get("action")
                }
            }
        elif menu_type == "list":
            # Send list message
            message = {
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "body": menu_structure.get("body"),
                    "action": menu_structure.get("action")
                }
            }
        else:
            # Send text message
            message = {
                "type": "text",
                "text": {"body": menu_structure.get("body", {}).get("text", "Menu")}
            }
        
        await send_whatsapp_message(phone_number, message)
    
    def _format_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Replace placeholders in prompt with context values"""
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))
        return prompt
```

---

## Integration with Message Processing

Update your existing message processor to use the interactive handler:

```python
# In backend/app/services/whatsapp_service.py

async def process_text_message(self, phone_number: str, text_content: str, ...):
    """Process text message with interactive conversation support"""
    
    # ... existing code ...
    
    # Check for interactive conversation
    from app.services.message_handler import InteractiveMessageHandler
    
    handler = InteractiveMessageHandler(self.db)
    result = await handler.handle_text_message(phone_number, text_content)
    
    if result["status"] in ["conversation_started", "step_advanced"]:
        # Interactive conversation handled
        return {"status": "success", "interactive": True}
    
    # Fall back to auto-reply if no conversation
    reply_message_id = await self._process_automated_reply_direct(...)
    
    return {"status": "success", "reply_sent": reply_message_id is not None}

async def process_interactive_message(self, phone_number: str, interactive_data: Dict, ...):
    """Process interactive button/list selection"""
    
    from app.services.message_handler import InteractiveMessageHandler
    
    handler = InteractiveMessageHandler(self.db)
    result = await handler.handle_interactive_message(phone_number, interactive_data)
    
    return {"status": "success", "result": result}
```

---

## Best Practices

### 1. Template Design

✅ **DO:**
- Keep menus simple (3 buttons max, 10 list items max per section)
- Use clear, action-oriented button titles
- Include emojis for visual appeal
- Define all steps in advance
- Plan the complete flow before coding

❌ **DON'T:**
- Create overly complex nested menus
- Use technical jargon in menu text
- Forget to define next steps
- Create dead-end flows with no exit

### 2. Conversation Management

✅ **DO:**
- Always clean up completed conversations
- Set reasonable expiry times (24 hours is good)
- Store only necessary data in context
- Validate user input at each step
- Provide a way to cancel/restart

❌ **DON'T:**
- Leave conversations active indefinitely
- Store sensitive data in context
- Trust user input without validation
- Force users through long flows without breaks

### 3. Context Data

```python
# Good context structure
context = {
    "product": "coffee",
    "quantity": 2,
    "price": 3.50,
    "total": 7.00,
    "step_history": ["initial", "product_selection", "quantity"]
}

# Bad context structure (too much data)
context = {
    "user_profile": {...},  # Don't duplicate DB data
    "full_catalog": [...],  # Don't store large datasets
    "internal_ids": {...}   # Don't expose internal data
}
```

### 4. Error Handling

Always handle these cases:
- Template not found
- Conversation expired
- Invalid user input
- Network errors sending messages
- Database transaction failures

### 5. Testing

Test these scenarios:
- Starting a conversation
- Completing a full flow
- Abandoning mid-flow
- Concurrent conversations (should not happen)
- Template switching
- Expiry cleanup

---

## Troubleshooting

### "No active conversation found"

**Cause:** Conversation expired or was deleted

**Solution:**
```python
# Always check before processing
conversation = service.get_conversation(phone_number)
if not conversation:
    # Start new conversation
    template = service.find_template_by_keyword("menu")
    service.start_conversation(phone_number, template.template_name)
```

### "Template not found"

**Cause:** Template was deleted or name mismatch

**Solution:**
```python
# Always check template exists
template = service.get_template(template_name)
if not template:
    logger.error(f"Template not found: {template_name}")
    # Fallback to main menu
    template = service.get_template("main_menu")
```

### "Context data lost"

**Cause:** Context not properly saved or retrieved

**Solution:**
```python
# Always use update method, don't replace context
service.update_conversation(
    phone_number=phone_number,
    context_update={"new_key": "value"}  # Merges with existing
)

# Not this:
conversation.context = {"new_key": "value"}  # Replaces all!
```

### "User stuck in conversation"

**Cause:** No expiry set or no way to exit

**Solution:**
```python
# Always set expiry
service.start_conversation(..., expiry_hours=24)

# Provide exit command
if text.lower() in ["cancel", "exit", "quit"]:
    service.end_conversation(phone_number)
    # Send confirmation message
```

---

## Quick Start Checklist

1. ☐ Apply conversation tables migration
2. ☐ Create ConversationService
3. ☐ Run create_initial_templates script
4. ☐ Create InteractiveMessageHandler
5. ☐ Update message processor to use handler
6. ☐ Test with "hi" keyword
7. ☐ Test button selections
8. ☐ Test complete order flow
9. ☐ Verify conversation cleanup

---

## Next Steps

1. **Create your first template** using the script
2. **Test it** by sending "hi" to your WhatsApp number
3. **Monitor logs** to see conversation flow
4. **Customize menus** for your business needs
5. **Add more templates** for different flows
6. **Set up scheduled cleanup** of expired conversations

---

## Need Help?

Common issues and solutions:
- Template not triggering → Check trigger_keywords and is_active
- Menu not sending → Check WhatsApp API credentials
- Conversation not saving → Check database connection
- Context not updating → Use update_conversation method

For more details, see:
- `docs/WhatsApp_Interactive_Menu_Automation_Guide.md`
- `backend/app/models/conversation.py`
- `backend/migrations/CONVERSATION_TABLES_README.md`

---

**Last Updated:** 2025-01-06
**Status:** Ready to implement
