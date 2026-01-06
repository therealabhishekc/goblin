# Quick Reference: Conversation Tables

## The Simple Answer

**Q: In `conversation_state`, does `conversation_flow` store the template name or the current_step?**

**A: `conversation_flow` stores the TEMPLATE NAME**

```
conversation_flow = "main_menu"          ← Which template (TEMPLATE NAME)
current_step = "product_selection"       ← Where in that template (CURRENT STEP)
```

## Database Tables

### conversation_state
- **Purpose**: Tracks what THIS customer is doing RIGHT NOW
- **Analogy**: The "Order Slip" 🧾
- **Lifespan**: Temporary (deleted when conversation completes)
- **Cardinality**: ONE per customer at any time

### workflow_templates  
- **Purpose**: Reusable menu definitions
- **Analogy**: The "Menu Card" 📋
- **Lifespan**: Permanent (stored forever)
- **Cardinality**: Many templates, used by many conversations

## Column Meanings

```sql
conversation_state:
  conversation_flow  → TEMPLATE NAME (e.g., "main_menu", "new_order")
  current_step       → CURRENT STEP (e.g., "initial", "product_selection")
  context            → User's data (selections, inputs)
```

## Import Models

```python
# Recommended
from app.models.conversation import ConversationStateDB, WorkflowTemplateDB

# Or backwards compatible
from app.database.models import ConversationState, WorkflowTemplate
```

## Apply Migration

```bash
# Add just conversation tables
psql -f backend/migrations/add_conversation_tables.sql

# Or complete schema (all tables)
psql -f backend/migrations/complete_schema.sql
```

## Total Tables: 9
1. user_profiles
2. whatsapp_messages
3. business_metrics
4. marketing_campaigns
5. campaign_recipients
6. campaign_send_schedule
7. **conversation_state** ⭐ NEW
8. **workflow_templates** ⭐ NEW

## Documentation
- Full Guide: `docs/WhatsApp_Interactive_Menu_Automation_Guide.md`
- Implementation: `IMPLEMENTATION_SUMMARY.md`
- Diagrams: `backend/migrations/table_relationship.txt`
