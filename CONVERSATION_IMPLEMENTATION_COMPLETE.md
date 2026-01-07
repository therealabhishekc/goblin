# Conversation System Implementation - Complete

## ✅ Implementation Status

All conversation system logic has been implemented and integrated with your existing code.

---

## 📁 Files Created

### 1. Core Service Layer
**Location:** `backend/app/services/conversation_service.py`

**What it does:**
- Manages workflow templates (CRUD operations)
- Manages conversation states (start, update, end)
- Finds templates by keywords
- Cleans up expired conversations
- Provides helper methods

**Key Methods:**
```python
# Template Methods
create_template()       # Create new template
get_template()         # Get template by name
find_template_by_keyword()  # Match user text to template
update_template()      # Modify existing template
delete_template()      # Remove template

# Conversation Methods
start_conversation()   # Begin new conversation
get_conversation()     # Get active conversation
update_conversation()  # Update step/context
end_conversation()     # Delete conversation
cleanup_expired_conversations()  # Remove old ones
```

### 2. Message Handler
**Location:** `backend/app/services/message_handler.py`

**What it does:**
- Handles incoming text messages
- Handles interactive button/list selections
- Starts new conversations based on keywords
- Continues existing conversations
- Processes user selections and moves through steps
- Sends interactive menus

**Key Methods:**
```python
handle_text_message()         # Process text from user
handle_interactive_message()  # Process button/list clicks
```

### 3. Template Creation Script
**Location:** `backend/scripts/create_initial_templates.py`

**What it does:**
- Scaffolding for creating initial templates
- Template structures left empty for you to fill
- Easy to customize and extend

**How to use:**
1. Edit the file to add your menu structures
2. Run: `python -m scripts.create_initial_templates`

### 4. Integration with Existing Code
**Location:** `backend/app/services/whatsapp_service.py`

**What was updated:**
- `process_text_message()` - Now checks for interactive conversations first, falls back to auto-reply
- `process_interactive_message()` - Now handles button/list selections

---

## 🔄 How It Works

### Flow Diagram

```
User sends "hi"
    ↓
WhatsApp Webhook receives message
    ↓
Message Processor Worker picks it up
    ↓
WhatsAppService.process_text_message()
    ↓
Checks InteractiveMessageHandler first
    ↓
    ├─ Has trigger keyword? 
    │   ├─ YES → Start conversation → Send menu ✅
    │   └─ NO → Check for active conversation
    │       ├─ YES → Continue conversation → Process input
    │       └─ NO → Fall back to auto-reply
    ↓
Response sent to user
```

### User clicks button

```
User clicks button
    ↓
WhatsApp Webhook receives interactive event
    ↓
Message Processor Worker picks it up
    ↓
WhatsAppService.process_interactive_message()
    ↓
InteractiveMessageHandler.handle_interactive_message()
    ↓
Extract button/list selection
    ↓
Get current conversation state
    ↓
Process selection → Update conversation → Move to next step
    ↓
Send next menu/prompt to user
```

---

## 🚀 Getting Started

### Step 1: Verify Tables Exist

Check if conversation tables are in your database:

```bash
psql -h YOUR_DB_HOST -U postgres -d postgres -c "
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN ('conversation_state', 'workflow_templates');"
```

**Expected output:** 2 rows

If tables don't exist, run the migration:
```bash
cd backend/migrations
./apply_conversation_migration.sh development
```

### Step 2: Customize Template Script

Edit `backend/scripts/create_initial_templates.py`:

```python
def create_main_menu_template(service: ConversationService):
    menu_structure = {
        "type": "button",
        "body": {
            "text": "👋 Welcome to our WhatsApp Business!\n\nHow can we help?"
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
                        "title": "👤 Account"
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
```

### Step 3: Run Template Creation

```bash
cd backend
python -m scripts.create_initial_templates
```

### Step 4: Test It

1. Send "hi" to your WhatsApp Business number
2. Should receive the menu you defined
3. Click a button
4. System processes the selection

---

## 🧪 Testing

### Test Commands

```bash
# Check if tables exist
psql $DATABASE_URL -c "SELECT COUNT(*) FROM workflow_templates;"

# Check templates
psql $DATABASE_URL -c "SELECT template_name, is_active FROM workflow_templates;"

# Check active conversations
psql $DATABASE_URL -c "SELECT phone_number, conversation_flow, current_step FROM conversation_state;"

# Clean up expired conversations
python -c "
from app.core.database import init_database, get_db_session
from app.services.conversation_service import ConversationService
init_database()
with get_db_session() as db:
    service = ConversationService(db)
    count = service.cleanup_expired_conversations()
    print(f'Cleaned up {count} conversations')
"
```

### Test Scenarios

1. **Start Conversation:**
   - Send trigger keyword (e.g., "hi")
   - Should receive interactive menu

2. **Continue Conversation:**
   - Click a button in the menu
   - Should move to next step

3. **Expired Conversation:**
   - Wait 24 hours
   - Send message again
   - Should start fresh conversation

4. **No Match:**
   - Send random text with no active conversation
   - Should fall back to auto-reply

---

## 📊 Database Structure

### workflow_templates (The Menu Card 📋)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| template_name | VARCHAR(100) | Unique template identifier |
| template_type | VARCHAR(20) | 'button', 'list', or 'text' |
| trigger_keywords | TEXT[] | Keywords that activate template |
| menu_structure | JSONB | Complete menu definition |
| is_active | BOOLEAN | Whether template is active |
| created_at | TIMESTAMP | When created |
| updated_at | TIMESTAMP | When last updated |

### conversation_state (The Order Slip 🧾)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| phone_number | VARCHAR(20) | Customer's phone |
| conversation_flow | VARCHAR(50) | Template name (which menu) |
| current_step | VARCHAR(50) | Current step in template |
| context | JSONB | User's selections/inputs |
| last_interaction | TIMESTAMP | Last message time |
| expires_at | TIMESTAMP | When conversation expires |
| created_at | TIMESTAMP | When started |
| updated_at | TIMESTAMP | When last updated |

---

## 🎯 Usage Examples

### Create a Template Programmatically

```python
from app.core.database import get_db_session
from app.services.conversation_service import ConversationService

with get_db_session() as db:
    service = ConversationService(db)
    
    template = service.create_template(
        template_name="welcome_menu",
        template_type="button",
        menu_structure={...},
        trigger_keywords=["start", "begin"],
        is_active=True
    )
```

### Start a Conversation

```python
conversation = service.start_conversation(
    phone_number="1234567890",
    template_name="welcome_menu",
    initial_step="initial",
    context={"source": "website"}
)
```

### Update Conversation State

```python
service.update_conversation(
    phone_number="1234567890",
    current_step="product_selection",
    context_update={"selected_category": "electronics"}
)
```

### End Conversation

```python
service.end_conversation("1234567890")
```

---

## 🔧 Configuration

### Expiry Time

Default: 24 hours

To change:
```python
service.start_conversation(
    phone_number="...",
    template_name="...",
    expiry_hours=48  # 2 days
)
```

### Cleanup Expired Conversations

Set up a cron job or scheduled task:

```bash
# Add to crontab
0 2 * * * cd /path/to/backend && python -c "from app.services.conversation_service import ConversationService; from app.core.database import get_db_session, init_database; init_database(); with get_db_session() as db: ConversationService(db).cleanup_expired_conversations()"
```

Or create a script:

```python
# backend/scripts/cleanup_conversations.py
from app.core.database import init_database, get_db_session
from app.services.conversation_service import ConversationService

def main():
    init_database()
    with get_db_session() as db:
        service = ConversationService(db)
        count = service.cleanup_expired_conversations()
        print(f"Cleaned up {count} expired conversations")

if __name__ == "__main__":
    main()
```

---

## 📚 Documentation References

- **Full Implementation Guide:** `COMPLETE_CONVERSATION_IMPLEMENTATION_GUIDE.md`
- **Template Reuse Explanation:** `TEMPLATE_REUSE_EXPLANATION.md`
- **Table Structure:** `backend/migrations/CONVERSATION_TABLES_README.md`
- **Auto Reply Status:** `AUTO_REPLY_STATUS_REPORT.md`

---

## ✅ Checklist

- [x] ConversationService implemented
- [x] InteractiveMessageHandler implemented
- [x] Template creation script created
- [x] Integration with WhatsAppService complete
- [x] Database tables ready (run migration if needed)
- [ ] Customize template script with your menus
- [ ] Run template creation script
- [ ] Test with trigger keywords
- [ ] Test button selections
- [ ] Set up conversation cleanup

---

## 🐛 Troubleshooting

### "Module not found: conversation_service"

**Solution:** Make sure you're running from the backend directory:
```bash
cd backend
python -m scripts.create_initial_templates
```

### "Table does not exist"

**Solution:** Run the migration:
```bash
cd backend/migrations
./apply_conversation_migration.sh development
```

### "No template matched"

**Solution:** 
1. Check if templates exist: `SELECT * FROM workflow_templates;`
2. Check if keywords match your message
3. Check if template is_active = true

### "Conversation not found"

**Solution:**
1. Check if conversation expired (24 hours)
2. Check if conversation was deleted
3. Start new conversation with trigger keyword

---

## 🎉 Next Steps

1. **Customize Templates**
   - Edit `scripts/create_initial_templates.py`
   - Add your menu structures
   - Define your conversation flows

2. **Run Script**
   ```bash
   python -m scripts.create_initial_templates
   ```

3. **Test**
   - Send trigger keyword to WhatsApp
   - Verify menu appears
   - Click buttons and test flow

4. **Monitor**
   - Check logs for conversation events
   - Monitor database for active conversations
   - Set up cleanup schedule

5. **Expand**
   - Add more templates
   - Create complex flows
   - Add validation and error handling

---

**Last Updated:** 2025-01-06
**Status:** ✅ Ready to Use
**Action Required:** Customize templates and test
