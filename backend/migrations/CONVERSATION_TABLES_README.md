# Conversation Tables Implementation Summary

## Overview
Added two new tables to the database schema for WhatsApp interactive menu automation:
1. `conversation_state` - Tracks active conversations (the "order slip")
2. `workflow_templates` - Stores reusable menu templates (the "menu card")

## Key Points

### conversation_state Table
- **conversation_flow column**: Stores the **TEMPLATE NAME** (e.g., 'main_menu', 'new_order', 'support')
- **current_step column**: Stores the **CURRENT STEP** within that template (e.g., 'initial', 'product_selection', 'quantity_input')
- Only ONE active conversation per customer at any time
- Auto-expires old conversations via `expires_at` timestamp

### workflow_templates Table
- Stores reusable interactive menu templates
- Multiple template types: 'button', 'list', 'text'
- Trigger keywords to activate templates
- Complete menu structure stored as JSONB

## Files Modified

### 1. New Model File
**File**: `/backend/app/models/conversation.py`
- Created new SQLAlchemy models: `ConversationStateDB` and `WorkflowTemplateDB`
- Created Pydantic models for API requests/responses
- Includes enums, create/update/response models

### 2. Updated Model Exports
**File**: `/backend/app/models/__init__.py`
- Added import for conversation models
- Makes models available throughout the application

### 3. Backwards Compatibility
**File**: `/backend/app/database/models.py`
- Added imports for new conversation models
- Maintains backwards compatibility with existing code

### 4. New SQL Migration
**File**: `/backend/migrations/add_conversation_tables.sql`
- Standalone migration for adding conversation tables
- Includes indexes, comments, and permissions
- Can be run independently

### 5. Updated Complete Schema
**File**: `/backend/migrations/complete_schema.sql`
- Added Section 11: Conversation State and Workflow Templates
- Added Section 12: Permissions for conversation tables
- Updated final migration summary (now 9 total tables)
- Updated verification queries

## Database Schema Structure

```sql
-- conversation_state: Tracks active conversations
CREATE TABLE conversation_state (
    id UUID PRIMARY KEY,
    phone_number VARCHAR(20),
    conversation_flow VARCHAR(50),  -- TEMPLATE NAME
    current_step VARCHAR(50),       -- CURRENT STEP in template
    context JSONB,                  -- User data/selections
    last_interaction TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- workflow_templates: Stores menu templates
CREATE TABLE workflow_templates (
    id UUID PRIMARY KEY,
    template_name VARCHAR(100) UNIQUE,
    template_type VARCHAR(20),
    trigger_keywords TEXT[],
    menu_structure JSONB,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Indexes Created
- `idx_conversation_phone` - Fast lookup by phone number
- `idx_conversation_flow` - Fast lookup by flow/template name
- `idx_conversation_expires` - Cleanup expired conversations
- `idx_workflow_templates_name` - Fast lookup by template name
- `idx_workflow_templates_active` - Filter active templates

## Usage Example

```python
from app.models.conversation import ConversationStateDB, WorkflowTemplateDB

# Create a conversation state
conversation = ConversationStateDB(
    phone_number="1234567890",
    conversation_flow="main_menu",  # Template name
    current_step="initial",          # Current step
    context={"user_selection": "new_order"}
)

# Create a workflow template
template = WorkflowTemplateDB(
    template_name="main_menu",
    template_type="button",
    trigger_keywords=["hi", "hello", "start"],
    menu_structure={
        "type": "button",
        "body": {"text": "Welcome! How can we help?"},
        "action": {
            "buttons": [
                {"id": "btn_1", "title": "New Order"},
                {"id": "btn_2", "title": "Support"}
            ]
        }
    },
    is_active=True
)
```

## Testing

All imports tested successfully:
```bash
✅ Successfully imported ConversationStateDB
✅ Successfully imported WorkflowTemplateDB
```

## Next Steps

To use these tables:
1. Run the migration: `psql -f backend/migrations/add_conversation_tables.sql`
2. Or run the complete schema: `psql -f backend/migrations/complete_schema.sql`
3. Import models in your code: `from app.models.conversation import ConversationStateDB, WorkflowTemplateDB`
4. Use the conversation manager as described in the WhatsApp Interactive Menu Automation Guide

## Total Database Tables

After this update, the database has **9 tables**:
1. user_profiles
2. whatsapp_messages
3. business_metrics
4. marketing_campaigns
5. campaign_recipients
6. campaign_send_schedule
7. **conversation_state** (NEW)
8. **workflow_templates** (NEW)

## Documentation References

See the full guide at: `/docs/WhatsApp_Interactive_Menu_Automation_Guide.md`
