# WhatsApp Interactive Menu Automation Guide

## Table of Contents
1. [Overview](#overview)
2. [WhatsApp Interactive Components](#whatsapp-interactive-components)
3. [Current System Architecture](#current-system-architecture)
4. [Implementation Guide](#implementation-guide)
5. [Database Schema](#database-schema)
6. [Code Examples](#code-examples)
7. [Testing & Deployment](#testing--deployment)
8. [Best Practices](#best-practices)

---

## Overview

This guide explains how to implement automated reply workflows using WhatsApp Business API interactive menus. Interactive messages allow you to create rich, button-based or list-based interfaces that users can interact with, providing a more engaging and user-friendly experience.

### Quick Understanding: The Two Tables

**Think of it like a restaurant:**

1. **`workflow_templates`** = The Menu Card 📋
   - Stores all the menus/options you show to customers
   - "Main Menu", "Product Catalog", "Support Options" etc.
   - Reusable templates that anyone can view
   - **Example**: When customer says "Hi", you show them the main menu (stored in this table)

2. **`conversation_state`** = The Order Slip 🧾
   - Tracks what THIS customer is doing RIGHT NOW
   - Only ONE active conversation per customer
   - Changes as customer progresses: selecting product → entering quantity → confirming
   - Gets deleted when conversation is complete
   - **Example**: Customer selected coffee, entered quantity 2, now at confirmation step

**Simple Analogy:**
- **Menu Card (workflow_templates)**: Same menu shown to everyone
- **Order Slip (conversation_state)**: Each customer's personal order, changes as they order

When a customer says "Hi", there is ONE conversation_flow created called "main_menu". As they interact, this flow might change to "new_order" or "support", but only ONE flow exists per customer at any time.

### What are Interactive Messages?

Interactive messages are special WhatsApp message types that include:
- **Buttons**: Up to 3 reply buttons per message
- **Lists**: Up to 10 sections with up to 10 rows each (100 total options)
- **Quick Replies**: Predefined responses users can tap

These components enable you to build:
- Customer service menus
- Order tracking systems
- Product catalogs
- Support ticket workflows
- Multi-step conversations

---

## WhatsApp Interactive Components

### 1. Reply Buttons

Reply buttons are simple, quick-action buttons (up to 3 per message).

**Structure:**
```json
{
  "type": "button",
  "body": {
    "text": "Welcome! How can we help you today?"
  },
  "action": {
    "buttons": [
      {
        "type": "reply",
        "reply": {
          "id": "button_1",
          "title": "Track Order"
        }
      },
      {
        "type": "reply",
        "reply": {
          "id": "button_2",
          "title": "New Order"
        }
      },
      {
        "type": "reply",
        "reply": {
          "id": "button_3",
          "title": "Support"
        }
      }
    ]
  }
}
```

**Limitations:**
- Maximum 3 buttons
- Button title: max 20 characters
- Button ID: max 256 characters

### 2. List Messages

List messages provide a more scalable menu with multiple sections and rows.

**Structure:**
```json
{
  "type": "list",
  "header": {
    "type": "text",
    "text": "Our Services"
  },
  "body": {
    "text": "Please select a service you're interested in"
  },
  "footer": {
    "text": "Powered by WhatsApp Business"
  },
  "action": {
    "button": "View Services",
    "sections": [
      {
        "title": "Products",
        "rows": [
          {
            "id": "row_1",
            "title": "Product A",
            "description": "Description of Product A"
          },
          {
            "id": "row_2",
            "title": "Product B",
            "description": "Description of Product B"
          }
        ]
      },
      {
        "title": "Services",
        "rows": [
          {
            "id": "row_3",
            "title": "Service A",
            "description": "Description of Service A"
          }
        ]
      }
    ]
  }
}
```

**Limitations:**
- Maximum 10 sections
- Maximum 10 rows per section (100 total rows)
- Row title: max 24 characters
- Row description: max 72 characters
- Section title: max 24 characters

---

## Current System Architecture

### Message Flow

```
User Sends Message
    ↓
WhatsApp Webhook → API Endpoint (/webhook)
    ↓
DynamoDB (Deduplication)
    ↓
SQS Queue (Incoming Messages)
    ↓
Message Processor Worker
    ↓
Reply Automation Service
    ↓
SQS Queue (Outgoing Messages)
    ↓
WhatsApp API
    ↓
User Receives Reply
```

### Key Components

1. **Webhook Handler** (`backend/app/api/webhook.py`)
   - Receives incoming messages
   - Performs deduplication
   - Queues messages to SQS

2. **Message Processor** (`backend/app/workers/message_processor.py`)
   - Processes queued messages
   - Handles different message types (text, image, interactive, etc.)
   - Routes to appropriate handlers

3. **Reply Automation** (`backend/app/services/reply_automation.py`)
   - Contains rule-based reply logic
   - Processes message content
   - Generates automated responses

4. **Messaging Service** (`backend/app/services/messaging_service.py`)
   - High-level message sending functions
   - Handles message formatting
   - Queues outgoing messages

---

## Database Schema

### Tables Involved in Interactive Workflows

#### 1. **whatsapp_messages**
Stores all incoming and outgoing messages.

```sql
CREATE TABLE whatsapp_messages (
    id UUID PRIMARY KEY,
    message_id VARCHAR(100) UNIQUE NOT NULL,
    from_phone VARCHAR(20) NOT NULL,
    to_phone VARCHAR(20),
    message_type VARCHAR(20) NOT NULL, -- 'text', 'interactive', 'button', etc.
    content TEXT,                       -- For interactive: stores selection info
    media_url VARCHAR(500),
    media_type VARCHAR(50),
    media_size INTEGER,
    status VARCHAR(20) DEFAULT 'processing',
    direction VARCHAR(20) DEFAULT 'incoming',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    failed_at TIMESTAMP,
    failure_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. **user_profiles**
Stores user information and preferences.

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    whatsapp_phone VARCHAR(20) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    customer_tier VARCHAR(20) DEFAULT 'regular',
    subscription VARCHAR(20) DEFAULT 'subscribed',
    tags TEXT[],
    notes TEXT,
    last_interaction TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### 3. **conversation_state** (NEW - To be created)
Tracks multi-step conversation flows and maintains user context throughout interactions.

**Purpose**: 
- Remembers where a user is in a multi-step conversation
- Stores temporary data needed across multiple messages
- Ensures conversations expire after inactivity
- Enables complex workflows like order placement, support tickets, etc.

**Key Concepts**:
- **conversation_flow**: The type of conversation (e.g., 'order_tracking', 'support_ticket', 'main_menu')
- **current_step**: Where the user is in that flow (e.g., 'awaiting_order_id', 'selecting_product', 'confirming_order')
- **context**: JSON object storing conversation data (e.g., selected items, quantities, user inputs)
- **expires_at**: Conversations automatically expire after 30 minutes of inactivity to prevent stale data

**Example Flow**:
When a user says "Hi", you create ONE conversation_flow called "main_menu". As they navigate through your system:
1. User says "Hi" → Flow: "main_menu", Step: "menu_shown"
2. User clicks "Place Order" button → Flow: "new_order", Step: "category_selection" 
3. User selects "Coffee" → Same Flow: "new_order", Step: "quantity_input", Context: {"product": "coffee"}
4. User says "2" → Same Flow: "new_order", Step: "confirmation", Context: {"product": "coffee", "quantity": 2}
5. User confirms → Flow ends, order is placed

```sql
CREATE TABLE IF NOT EXISTS conversation_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL,
    conversation_flow VARCHAR(50) NOT NULL,  -- e.g., 'order_tracking', 'support_ticket', 'new_order'
    current_step VARCHAR(50) NOT NULL,       -- e.g., 'awaiting_order_id', 'menu_selection', 'confirming'
    context JSONB DEFAULT '{}',              -- e.g., {"product": "coffee", "quantity": 2, "price": 150}
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,                    -- Auto-expire after 30 mins of inactivity
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversation_phone ON conversation_state(phone_number);
CREATE INDEX idx_conversation_flow ON conversation_state(conversation_flow);
CREATE INDEX idx_conversation_expires ON conversation_state(expires_at);
```

**Real World Example - Order Tracking Flow**:

| User Action | conversation_flow | current_step | context | What Happens |
|------------|------------------|--------------|---------|--------------|
| User: "Track my order" | "order_tracking" | "awaiting_order_id" | {} | Bot asks: "Please provide your order ID" |
| User: "ORD-12345" | "order_tracking" | "showing_status" | {"order_id": "ORD-12345"} | Bot fetches order, shows status |
| User clicks "Track Again" | "order_tracking" | "awaiting_order_id" | {} | Loop back to step 1 |
| User clicks "Main Menu" | "main_menu" | "menu_shown" | {} | New flow starts |

#### 4. **workflow_templates** (NEW - To be created)
Stores reusable interactive menu templates that can be triggered by keywords or used programmatically.

**Purpose**: 
- Store pre-built menu structures that can be reused
- Map keywords to specific menus (e.g., "hi" → main_menu, "order" → product_catalog)
- Enable non-technical users to create/modify menus via admin panel
- Version control for menu changes

**Key Concepts**:
- **template_name**: Unique identifier for the template (e.g., 'main_menu', 'product_catalog')
- **template_type**: Type of interactive message ('button', 'list', 'flow')
- **trigger_keywords**: Array of words that trigger this template (e.g., ['hi', 'hello', 'menu'] → main_menu)
- **menu_structure**: Complete JSON structure of the WhatsApp interactive message

```sql
CREATE TABLE IF NOT EXISTS workflow_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(100) UNIQUE NOT NULL,
    template_type VARCHAR(20) NOT NULL,     -- 'button', 'list', 'flow'
    trigger_keywords TEXT[],                 -- e.g., ['hi', 'hello', 'menu'] triggers main menu
    menu_structure JSONB NOT NULL,          -- Complete WhatsApp interactive message JSON
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workflow_templates_name ON workflow_templates(template_name);
CREATE INDEX idx_workflow_templates_active ON workflow_templates(is_active);
```

**Real World Example - Stored Templates**:

**Template 1: Main Menu (Button Type)**
```json
{
  "template_name": "main_menu",
  "template_type": "button",
  "trigger_keywords": ["hi", "hello", "menu", "start", "help"],
  "menu_structure": {
    "type": "button",
    "body": {"text": "Welcome! How can we help you today?"},
    "action": {
      "buttons": [
        {"type": "reply", "reply": {"id": "track_order", "title": "Track Order"}},
        {"type": "reply", "reply": {"id": "new_order", "title": "Place Order"}},
        {"type": "reply", "reply": {"id": "support", "title": "Get Support"}}
      ]
    }
  }
}
```

**Template 2: Product Catalog (List Type)**
```json
{
  "template_name": "product_catalog",
  "template_type": "list",
  "trigger_keywords": ["order", "buy", "purchase", "products"],
  "menu_structure": {
    "type": "list",
    "body": {"text": "Browse our products and select items to order"},
    "action": {
      "button": "View Products",
      "sections": [
        {
          "title": "Beverages",
          "rows": [
            {"id": "coffee", "title": "Coffee", "description": "₹120 - Hot & Cold"},
            {"id": "tea", "title": "Tea", "description": "₹80 - Masala Chai"}
          ]
        },
        {
          "title": "Snacks",
          "rows": [
            {"id": "samosa", "title": "Samosa", "description": "₹40 - 2 pieces"},
            {"id": "pakora", "title": "Pakora", "description": "₹60 - Mixed"}
          ]
        }
      ]
    }
  }
}
```

**How It Works**:
1. User sends "hi" → System checks workflow_templates for matching trigger_keywords
2. Finds "main_menu" template with keywords ['hi', 'hello', 'menu']
3. Retrieves menu_structure JSON and sends it as interactive message
4. User clicks button → Creates conversation_state entry to track their journey

---

## Complete Conversation Flow Example

Let's walk through a **complete customer journey** to understand how conversation_flow and workflow_templates work together:

### Scenario: Customer Orders Coffee

#### Step-by-Step Flow:

**1. Customer Initiates Contact**
```
User Message: "Hi"
```
**System Actions:**
- Checks `workflow_templates` for keyword "hi"
- Finds template_name: "main_menu"
- Creates `conversation_state` entry:
  ```
  phone_number: "917829844548"
  conversation_flow: "main_menu"
  current_step: "menu_shown"
  context: {}
  expires_at: now() + 30 minutes
  ```
- Sends main menu with 3 buttons

**WhatsApp Message Sent:**
```
Welcome! How can we help you today?
[Track Order] [Place Order] [Get Support]
```

---

**2. Customer Clicks "Place Order"**
```
Interactive Reply: button_id = "new_order"
```
**System Actions:**
- Retrieves `conversation_state` for phone "917829844548"
- Current flow: "main_menu", step: "menu_shown"
- Detects button_id = "new_order"
- Updates `conversation_state`:
  ```
  conversation_flow: "new_order"
  current_step: "category_selection"
  context: {}
  ```
- Fetches `workflow_templates` template_name: "product_catalog"
- Sends product list

**WhatsApp Message Sent:**
```
🛍️ What would you like to order?

[View Products]
When tapped, shows:
  Beverages:
    - Coffee (₹120 - Hot & Cold)
    - Tea (₹80 - Masala Chai)
  Snacks:
    - Samosa (₹40 - 2 pieces)
    - Pakora (₹60 - Mixed)
```

---

**3. Customer Selects "Coffee"**
```
Interactive Reply: list_reply_id = "coffee"
```
**System Actions:**
- Retrieves `conversation_state` for phone "917829844548"
- Current flow: "new_order", step: "category_selection"
- Detects selection: "coffee"
- Updates `conversation_state`:
  ```
  conversation_flow: "new_order"
  current_step: "quantity_input"
  context: {"product": "coffee", "product_name": "Coffee", "price": 120}
  ```
- Sends text message asking for quantity

**WhatsApp Message Sent:**
```
Great choice! ☕ Coffee - ₹120

How many would you like to order?
(Reply with a number, e.g., 1, 2, 3)
```

---

**4. Customer Replies with Quantity**
```
User Message: "2"
```
**System Actions:**
- Retrieves `conversation_state` for phone "917829844548"
- Current flow: "new_order", step: "quantity_input"
- Context has: {"product": "coffee", "price": 120}
- Validates input "2" is a number
- Calculates total: 120 × 2 = 240
- Updates `conversation_state`:
  ```
  conversation_flow: "new_order"
  current_step: "confirmation"
  context: {
    "product": "coffee",
    "product_name": "Coffee",
    "price": 120,
    "quantity": 2,
    "total": 240
  }
  ```
- Sends confirmation message with buttons

**WhatsApp Message Sent:**
```
📋 Order Summary:
Coffee × 2 = ₹240

Is this correct?
[✅ Confirm Order] [❌ Cancel] [🔄 Edit]
```

---

**5. Customer Confirms Order**
```
Interactive Reply: button_id = "confirm_order"
```
**System Actions:**
- Retrieves `conversation_state` for phone "917829844548"
- Current flow: "new_order", step: "confirmation"
- Context has complete order data
- Creates order in database:
  ```sql
  INSERT INTO orders (customer_phone, items, total, status)
  VALUES ('917829844548', '[{"product": "coffee", "quantity": 2}]', 240, 'pending')
  ```
- Deletes/expires `conversation_state` entry (conversation complete)
- Sends success message

**WhatsApp Message Sent:**
```
✅ Order Confirmed!

Order ID: ORD-12345
Coffee × 2 = ₹240

Your order will be ready in 15 minutes.
Track status anytime by replying "track ORD-12345"

Need anything else? Reply "menu"
```

---

### Key Insights from This Example:

1. **One Active Conversation at a Time**: 
   - The user has ONE conversation_state row at any time
   - It transitions through steps: "menu_shown" → "category_selection" → "quantity_input" → "confirmation"

2. **Context Builds Over Time**:
   - Step 1: `context = {}`
   - Step 2: `context = {"product": "coffee", "price": 120}`
   - Step 3: `context = {"product": "coffee", "price": 120, "quantity": 2, "total": 240}`
   - This context moves through the conversation

3. **Different conversation_flow Values**:
   - "main_menu": Initial greeting/menu
   - "new_order": Order placement flow
   - "order_tracking": Check order status flow
   - "support": Customer support flow

4. **Workflow Templates are Reusable**:
   - "main_menu" template can be triggered by: "hi", "hello", "menu", "start"
   - Same template sent to all users who say "hi"
   - Stored once in `workflow_templates`, used many times

5. **Automatic Cleanup**:
   - If user doesn't respond for 30 minutes, `expires_at` is reached
   - Conversation is cleaned up automatically
   - Next message from user starts fresh conversation

---

## Implementation Guide

### Step 1: Extend Message Processor for Interactive Messages

Update `backend/app/workers/message_processor.py` to handle interactive message responses:

```python
# In process_message_safe method, add handling for interactive type

elif message_type == "interactive":
    interactive_data = message.get("interactive", {})
    interactive_type = interactive_data.get("type")  # 'button_reply' or 'list_reply'
    
    if interactive_type == "button_reply":
        button_reply = interactive_data.get("button_reply", {})
        button_id = button_reply.get("id")
        button_title = button_reply.get("title")
        
        result = await messaging_service.process_button_reply(
            phone_number=phone_number,
            button_id=button_id,
            button_title=button_title,
            message_id=message_id
        )
    
    elif interactive_type == "list_reply":
        list_reply = interactive_data.get("list_reply", {})
        row_id = list_reply.get("id")
        row_title = list_reply.get("title")
        row_description = list_reply.get("description", "")
        
        result = await messaging_service.process_list_reply(
            phone_number=phone_number,
            row_id=row_id,
            row_title=row_title,
            row_description=row_description,
            message_id=message_id
        )
```

### Step 2: Create Conversation State Manager

Create `backend/app/services/conversation_manager.py`:

```python
"""
Conversation State Manager
Handles multi-step conversation flows and context tracking
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

from app.core.logging import logger

class ConversationManager:
    """Manages conversation state and flows"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_conversation(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get active conversation for user"""
        query = text("""
            SELECT * FROM conversation_state 
            WHERE phone_number = :phone 
            AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY last_interaction DESC 
            LIMIT 1
        """)
        result = self.db.execute(query, {"phone": phone_number}).fetchone()
        
        if result:
            return {
                "id": str(result.id),
                "conversation_flow": result.conversation_flow,
                "current_step": result.current_step,
                "context": result.context,
                "last_interaction": result.last_interaction
            }
        return None
    
    def start_conversation(
        self, 
        phone_number: str, 
        flow_name: str, 
        initial_step: str,
        context: Dict[str, Any] = None,
        ttl_minutes: int = 30
    ) -> str:
        """Start a new conversation flow"""
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        
        query = text("""
            INSERT INTO conversation_state 
            (phone_number, conversation_flow, current_step, context, expires_at)
            VALUES (:phone, :flow, :step, :context, :expires)
            RETURNING id
        """)
        
        result = self.db.execute(query, {
            "phone": phone_number,
            "flow": flow_name,
            "step": initial_step,
            "context": json.dumps(context or {}),
            "expires": expires_at
        })
        self.db.commit()
        
        conversation_id = str(result.fetchone()[0])
        logger.info(f"🔄 Started conversation {flow_name} for {phone_number}: {conversation_id}")
        return conversation_id
    
    def update_conversation(
        self, 
        phone_number: str, 
        new_step: str,
        context_updates: Dict[str, Any] = None
    ) -> bool:
        """Update conversation state"""
        # Get current conversation
        current = self.get_conversation(phone_number)
        if not current:
            return False
        
        # Merge context
        new_context = current["context"]
        if context_updates:
            new_context.update(context_updates)
        
        query = text("""
            UPDATE conversation_state 
            SET current_step = :step,
                context = :context,
                last_interaction = NOW(),
                updated_at = NOW()
            WHERE phone_number = :phone
            AND (expires_at IS NULL OR expires_at > NOW())
        """)
        
        self.db.execute(query, {
            "phone": phone_number,
            "step": new_step,
            "context": json.dumps(new_context)
        })
        self.db.commit()
        
        logger.info(f"🔄 Updated conversation for {phone_number} to step: {new_step}")
        return True
    
    def end_conversation(self, phone_number: str) -> bool:
        """End active conversation"""
        query = text("""
            UPDATE conversation_state 
            SET expires_at = NOW()
            WHERE phone_number = :phone
            AND (expires_at IS NULL OR expires_at > NOW())
        """)
        
        self.db.execute(query, {"phone": phone_number})
        self.db.commit()
        
        logger.info(f"✅ Ended conversation for {phone_number}")
        return True
    
    def cleanup_expired(self) -> int:
        """Clean up expired conversations"""
        query = text("""
            DELETE FROM conversation_state 
            WHERE expires_at < NOW()
            RETURNING id
        """)
        
        result = self.db.execute(query)
        self.db.commit()
        count = len(result.fetchall())
        
        if count > 0:
            logger.info(f"🧹 Cleaned up {count} expired conversations")
        return count
```

### Step 3: Create Interactive Menu Builder

Create `backend/app/services/interactive_menu_builder.py`:

```python
"""
Interactive Menu Builder
Builds WhatsApp interactive messages (buttons and lists)
"""
from typing import List, Dict, Any, Optional

class InteractiveMenuBuilder:
    """Builds interactive message structures"""
    
    @staticmethod
    def build_button_menu(
        body_text: str,
        buttons: List[Dict[str, str]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a button-based interactive message
        
        Args:
            body_text: Main message text
            buttons: List of buttons [{"id": "btn_1", "title": "Button 1"}, ...]
            header_text: Optional header
            footer_text: Optional footer
        
        Returns:
            WhatsApp interactive message payload
        """
        if len(buttons) > 3:
            raise ValueError("Maximum 3 buttons allowed")
        
        message = {
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": body_text
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": btn["id"],
                                "title": btn["title"][:20]  # Max 20 chars
                            }
                        }
                        for btn in buttons
                    ]
                }
            }
        }
        
        if header_text:
            message["interactive"]["header"] = {
                "type": "text",
                "text": header_text
            }
        
        if footer_text:
            message["interactive"]["footer"] = {
                "text": footer_text
            }
        
        return message
    
    @staticmethod
    def build_list_menu(
        body_text: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a list-based interactive message
        
        Args:
            body_text: Main message text
            button_text: Text for the list button (e.g., "View Menu")
            sections: List of sections with rows
            header_text: Optional header
            footer_text: Optional footer
        
        Example sections:
        [
            {
                "title": "Section 1",
                "rows": [
                    {"id": "row_1", "title": "Option 1", "description": "Description"}
                ]
            }
        ]
        
        Returns:
            WhatsApp interactive message payload
        """
        if len(sections) > 10:
            raise ValueError("Maximum 10 sections allowed")
        
        total_rows = sum(len(section.get("rows", [])) for section in sections)
        if total_rows > 100:
            raise ValueError("Maximum 100 total rows allowed")
        
        message = {
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {
                    "text": body_text
                },
                "action": {
                    "button": button_text[:20],  # Max 20 chars
                    "sections": [
                        {
                            "title": section["title"][:24],  # Max 24 chars
                            "rows": [
                                {
                                    "id": row["id"],
                                    "title": row["title"][:24],  # Max 24 chars
                                    "description": row.get("description", "")[:72]  # Max 72 chars
                                }
                                for row in section.get("rows", [])
                            ]
                        }
                        for section in sections
                    ]
                }
            }
        }
        
        if header_text:
            message["interactive"]["header"] = {
                "type": "text",
                "text": header_text
            }
        
        if footer_text:
            message["interactive"]["footer"] = {
                "text": footer_text
            }
        
        return message
```

### Step 4: Create Workflow Examples

Create `backend/app/services/workflow_examples.py`:

```python
"""
Example Interactive Workflows
Pre-built conversation flows for common use cases
"""
from typing import Dict, Any
from app.services.interactive_menu_builder import InteractiveMenuBuilder
from app.services.conversation_manager import ConversationManager
from app.services.messaging_service import send_whatsapp_message
from app.core.logging import logger

class WorkflowExamples:
    """Pre-built workflow examples"""
    
    def __init__(self, conversation_manager: ConversationManager):
        self.conv_mgr = conversation_manager
        self.menu_builder = InteractiveMenuBuilder()
    
    async def main_menu_workflow(self, phone_number: str):
        """Main menu - entry point for customer interactions"""
        
        # Start conversation
        self.conv_mgr.start_conversation(
            phone_number=phone_number,
            flow_name="main_menu",
            initial_step="menu_shown"
        )
        
        # Build main menu
        menu = self.menu_builder.build_button_menu(
            body_text="Welcome! 👋 How can we help you today?",
            buttons=[
                {"id": "track_order", "title": "Track Order"},
                {"id": "new_order", "title": "Place Order"},
                {"id": "support", "title": "Get Support"}
            ],
            footer_text="Reply anytime for help"
        )
        
        # Send menu
        await send_whatsapp_message(
            phone_number=phone_number,
            message_type="interactive",
            content=menu
        )
        
        logger.info(f"📋 Sent main menu to {phone_number}")
    
    async def handle_button_reply(self, phone_number: str, button_id: str):
        """Handle button selection from main menu"""
        
        if button_id == "track_order":
            await self.order_tracking_workflow(phone_number)
        
        elif button_id == "new_order":
            await self.new_order_workflow(phone_number)
        
        elif button_id == "support":
            await self.support_workflow(phone_number)
    
    async def order_tracking_workflow(self, phone_number: str):
        """Order tracking flow"""
        
        # Update conversation state
        self.conv_mgr.update_conversation(
            phone_number=phone_number,
            new_step="awaiting_order_id"
        )
        
        # Ask for order ID
        await send_whatsapp_message(
            phone_number=phone_number,
            message_type="text",
            content="📦 Please provide your order ID (e.g., ORD-12345)"
        )
    
    async def new_order_workflow(self, phone_number: str):
        """New order placement flow"""
        
        # Update conversation state
        self.conv_mgr.start_conversation(
            phone_number=phone_number,
            flow_name="new_order",
            initial_step="category_selection"
        )
        
        # Show product categories
        menu = self.menu_builder.build_list_menu(
            body_text="🛍️ What would you like to order?",
            button_text="View Products",
            sections=[
                {
                    "title": "Beverages",
                    "rows": [
                        {"id": "prod_coffee", "title": "Coffee", "description": "Hot & Cold Coffee"},
                        {"id": "prod_tea", "title": "Tea", "description": "Chai & Green Tea"},
                        {"id": "prod_juice", "title": "Juice", "description": "Fresh Fruit Juices"}
                    ]
                },
                {
                    "title": "Snacks",
                    "rows": [
                        {"id": "prod_samosa", "title": "Samosa", "description": "Crispy Samosas"},
                        {"id": "prod_pakora", "title": "Pakora", "description": "Mixed Pakoras"},
                        {"id": "prod_sandwich", "title": "Sandwich", "description": "Veg Sandwiches"}
                    ]
                }
            ],
            footer_text="Browse and select items"
        )
        
        await send_whatsapp_message(
            phone_number=phone_number,
            message_type="interactive",
            content=menu
        )
    
    async def support_workflow(self, phone_number: str):
        """Customer support flow"""
        
        # Start support conversation
        self.conv_mgr.start_conversation(
            phone_number=phone_number,
            flow_name="support",
            initial_step="issue_selection"
        )
        
        # Show support categories
        menu = self.menu_builder.build_button_menu(
            body_text="🆘 How can we support you?",
            buttons=[
                {"id": "supp_delivery", "title": "Delivery Issue"},
                {"id": "supp_payment", "title": "Payment Issue"},
                {"id": "supp_other", "title": "Other"}
            ],
            footer_text="Our team is here to help"
        )
        
        await send_whatsapp_message(
            phone_number=phone_number,
            message_type="interactive",
            content=menu
        )
```

### Step 5: Integrate with Message Processor

Update `backend/app/services/messaging_service.py`:

```python
# Add these methods to handle interactive replies

async def process_button_reply(
    phone_number: str,
    button_id: str,
    button_title: str,
    message_id: str
) -> Dict[str, Any]:
    """Process button reply from interactive message"""
    from app.core.database import SessionLocal
    from app.services.conversation_manager import ConversationManager
    from app.services.workflow_examples import WorkflowExamples
    
    db = SessionLocal()
    try:
        conv_mgr = ConversationManager(db)
        workflows = WorkflowExamples(conv_mgr)
        
        # Get current conversation state
        conversation = conv_mgr.get_conversation(phone_number)
        
        if conversation:
            flow = conversation["conversation_flow"]
            step = conversation["current_step"]
            
            logger.info(f"🔘 Button reply: {button_id} | Flow: {flow} | Step: {step}")
            
            # Route based on current conversation flow
            if flow == "main_menu":
                await workflows.handle_button_reply(phone_number, button_id)
            
            elif flow == "support":
                await workflows.handle_support_button(phone_number, button_id)
        
        else:
            # No active conversation - show main menu
            await workflows.main_menu_workflow(phone_number)
        
        return {"status": "success", "button_id": button_id}
    
    finally:
        db.close()


async def process_list_reply(
    phone_number: str,
    row_id: str,
    row_title: str,
    row_description: str,
    message_id: str
) -> Dict[str, Any]:
    """Process list reply from interactive message"""
    from app.core.database import SessionLocal
    from app.services.conversation_manager import ConversationManager
    from app.services.workflow_examples import WorkflowExamples
    
    db = SessionLocal()
    try:
        conv_mgr = ConversationManager(db)
        workflows = WorkflowExamples(conv_mgr)
        
        # Get current conversation state
        conversation = conv_mgr.get_conversation(phone_number)
        
        if conversation:
            flow = conversation["conversation_flow"]
            step = conversation["current_step"]
            
            logger.info(f"📋 List reply: {row_id} | Flow: {flow} | Step: {step}")
            
            # Route based on current conversation flow
            if flow == "new_order":
                await workflows.handle_product_selection(phone_number, row_id, row_title)
        
        return {"status": "success", "row_id": row_id}
    
    finally:
        db.close()
```

---

## Code Examples

### Example 1: Simple Button Menu

```python
from app.services.interactive_menu_builder import InteractiveMenuBuilder
from app.services.messaging_service import send_whatsapp_message

menu_builder = InteractiveMenuBuilder()

# Create button menu
menu = menu_builder.build_button_menu(
    body_text="Choose an option:",
    buttons=[
        {"id": "opt_yes", "title": "Yes"},
        {"id": "opt_no", "title": "No"},
        {"id": "opt_maybe", "title": "Maybe"}
    ]
)

# Send to user
await send_whatsapp_message(
    phone_number="917829844548",
    message_type="interactive",
    content=menu
)
```

### Example 2: Product Catalog List

```python
# Create product catalog
menu = menu_builder.build_list_menu(
    header_text="Our Menu",
    body_text="Select items to order",
    button_text="Browse Menu",
    sections=[
        {
            "title": "Hot Beverages",
            "rows": [
                {
                    "id": "item_1",
                    "title": "Espresso",
                    "description": "₹120 - Strong Italian coffee"
                },
                {
                    "id": "item_2",
                    "title": "Cappuccino",
                    "description": "₹150 - Coffee with steamed milk"
                }
            ]
        },
        {
            "title": "Cold Beverages",
            "rows": [
                {
                    "id": "item_3",
                    "title": "Iced Latte",
                    "description": "₹180 - Chilled coffee drink"
                }
            ]
        }
    ],
    footer_text="All prices include taxes"
)

await send_whatsapp_message(
    phone_number="917829844548",
    message_type="interactive",
    content=menu
)
```

### Example 3: Multi-Step Order Flow

```python
from app.services.conversation_manager import ConversationManager
from app.core.database import SessionLocal

db = SessionLocal()
conv_mgr = ConversationManager(db)

# Step 1: Start order
conv_mgr.start_conversation(
    phone_number="917829844548",
    flow_name="order",
    initial_step="category",
    context={"cart": []}
)

# Step 2: User selects item
conv_mgr.update_conversation(
    phone_number="917829844548",
    new_step="quantity",
    context_updates={"selected_item": "item_1"}
)

# Step 3: User provides quantity
conv_mgr.update_conversation(
    phone_number="917829844548",
    new_step="confirm",
    context_updates={"quantity": 2}
)

# Step 4: Complete order
conv_mgr.end_conversation("917829844548")
```

---

## Testing & Deployment

### Local Testing

1. **Create Database Tables**:
```bash
cd /Users/abskchsk/Documents/govindjis/wa-app/backend/migrations
psql -h whatsapp-postgres-development.cibi66cyqd2r.us-east-1.rds.amazonaws.com -U postgres -d postgres -f create_conversation_tables.sql
```

2. **Test Interactive Menus**:
```python
# Use WhatsApp test numbers to send interactive messages
# Monitor logs to see incoming button/list replies
```

3. **Check Logs**:
```bash
# App Runner logs
# Look for: "🔘 Button reply" or "📋 List reply"
```

### Deployment Steps

1. **Deploy Code Changes**:
```bash
cd /Users/abskchsk/Documents/govindjis/wa-app
git add .
git commit -m "Add interactive menu support"
git push origin main
```

2. **Create Migration Script**:
Create `backend/migrations/add_conversation_tables.sql`

3. **Run Migration**:
```bash
# Connect to RDS and run migration
psql -h [RDS_ENDPOINT] -U postgres -d postgres -f add_conversation_tables.sql
```

4. **Monitor Deployment**:
- Check AWS App Runner deployment status
- Verify health checks pass
- Test interactive menus with real WhatsApp numbers

---

## Best Practices

### 1. **Keep Menus Simple**
- Max 3 buttons for simple choices
- Use lists when you have more than 3 options
- Group related items in list sections

### 2. **Clear Button/Row Text**
- Use action-oriented text ("Track Order" not "Order")
- Keep under character limits
- Make options mutually exclusive

### 3. **Manage Conversation State**
- Always track where users are in flows
- Set expiration times for conversations
- Clean up old conversations regularly

### 4. **Error Handling**
- Handle unexpected user input
- Provide "Go Back" or "Main Menu" options
- Timeout inactive conversations

### 5. **Testing**
- Test all menu combinations
- Verify button/list IDs are unique
- Check character limits don't truncate text

### 6. **Performance**
- Keep conversation context small
- Use efficient database queries
- Cache frequently used menus

### 7. **User Experience**
- Provide clear instructions
- Show progress in multi-step flows
- Confirm important actions
- Allow easy exit from flows

---

## Migration SQL Script

Save this as `backend/migrations/add_conversation_tables.sql`:

```sql
-- Conversation State Table
CREATE TABLE IF NOT EXISTS conversation_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL,
    conversation_flow VARCHAR(50) NOT NULL,
    current_step VARCHAR(50) NOT NULL,
    context JSONB DEFAULT '{}',
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversation_phone ON conversation_state(phone_number);
CREATE INDEX IF NOT EXISTS idx_conversation_flow ON conversation_state(conversation_flow);
CREATE INDEX IF NOT EXISTS idx_conversation_expires ON conversation_state(expires_at);

-- Workflow Templates Table
CREATE TABLE IF NOT EXISTS workflow_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(100) UNIQUE NOT NULL,
    template_type VARCHAR(20) NOT NULL,
    trigger_keywords TEXT[],
    menu_structure JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_workflow_templates_name ON workflow_templates(template_name);
CREATE INDEX IF NOT EXISTS idx_workflow_templates_active ON workflow_templates(is_active);

-- Add comment for documentation
COMMENT ON TABLE conversation_state IS 'Tracks active conversation flows and user context';
COMMENT ON TABLE workflow_templates IS 'Stores reusable interactive menu templates';
```

---

## Summary

This guide provides a complete framework for implementing automated reply workflows using WhatsApp interactive menus. The system includes:

✅ **Database schema** for conversation tracking
✅ **Conversation manager** for state management
✅ **Menu builder** for creating interactive messages
✅ **Workflow examples** for common use cases
✅ **Integration** with existing message processor
✅ **Best practices** for production deployment

You can now build sophisticated conversational experiences that guide users through multi-step processes, product catalogs, support tickets, and more - all within WhatsApp!

For questions or issues, check the App Runner logs or refer to the [WhatsApp Business API documentation](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages#interactive-messages).
