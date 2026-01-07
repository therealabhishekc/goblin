# How Workflow Templates Work: A Complete Explanation

## The Big Question

**"Once these templates are created, are they stored in the DB and used again and again when a user texts 'hi', or how does it work?"**

## Short Answer

✅ **YES!** Templates are stored in the database **ONCE** and then **reused forever** for all customers.

Think of it like a restaurant menu:
- The **menu** (template) is created once and printed
- Every **customer** (user) gets shown the same menu
- Each customer's **order** (conversation_state) is unique

---

## How It Works: Step by Step

### Phase 1: Setup (Done ONCE by Admin)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ADMIN RUNS THE SCRIPT ONCE                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  $ python -m scripts.create_initial_templates                               │
│                                                                             │
│  Script creates templates and saves to workflow_templates table:            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │ workflow_templates table                                          │     │
│  ├───────────────────────────────────────────────────────────────────┤     │
│  │ id: 1                                                             │     │
│  │ template_name: "main_menu"                                        │     │
│  │ template_type: "button"                                           │     │
│  │ trigger_keywords: ["hi", "hello", "start", "menu"]               │     │
│  │ menu_structure: { ... button menu definition ... }               │     │
│  │ is_active: true                                                   │     │
│  │ created_at: 2025-01-06 10:00:00                                  │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │ id: 2                                                             │     │
│  │ template_name: "new_order"                                        │     │
│  │ template_type: "list"                                             │     │
│  │ trigger_keywords: ["order", "buy"]                               │     │
│  │ menu_structure: { ... list menu definition ... }                 │     │
│  │ is_active: true                                                   │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  And so on for all templates...                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

✅ Templates are now STORED IN DATABASE
✅ Script only needs to run ONCE
✅ Templates are PERMANENT (until you delete them)
```

### Phase 2: Usage (Happens EVERY time a user messages)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  USER 1 SENDS "HI"                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Message arrives: "hi" from phone 1234567890                             │
│     ↓                                                                       │
│  2. System searches workflow_templates for matching keyword:                │
│     SELECT * FROM workflow_templates                                        │
│     WHERE 'hi' = ANY(trigger_keywords) AND is_active = true                │
│     ↓                                                                       │
│  3. Finds "main_menu" template (stored in DB)                              │
│     ↓                                                                       │
│  4. Creates NEW conversation_state for THIS user:                           │
│     ┌───────────────────────────────────────────────────────────────┐     │
│     │ conversation_state table                                      │     │
│     ├───────────────────────────────────────────────────────────────┤     │
│     │ id: 101                                                       │     │
│     │ phone_number: "1234567890"                                    │     │
│     │ conversation_flow: "main_menu"  ← References template name    │     │
│     │ current_step: "initial"                                       │     │
│     │ context: {}                                                   │     │
│     │ created_at: 2025-01-06 14:30:00                              │     │
│     │ expires_at: 2025-01-07 14:30:00  (24 hours later)           │     │
│     └───────────────────────────────────────────────────────────────┘     │
│     ↓                                                                       │
│  5. Reads menu_structure from template (in DB)                             │
│     ↓                                                                       │
│  6. Sends menu to user                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

✅ Template was READ from database (not created)
✅ Conversation_state was CREATED for this specific user
✅ Same template will be used for next user too
```

### Phase 3: Another User (Same Day)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  USER 2 SENDS "HI" (2 hours later)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Message arrives: "hi" from phone 9876543210                             │
│     ↓                                                                       │
│  2. System searches workflow_templates (SAME as before):                    │
│     SELECT * FROM workflow_templates                                        │
│     WHERE 'hi' = ANY(trigger_keywords)                                     │
│     ↓                                                                       │
│  3. Finds SAME "main_menu" template (reused from DB)                       │
│     ↓                                                                       │
│  4. Creates DIFFERENT conversation_state for THIS user:                     │
│     ┌───────────────────────────────────────────────────────────────┐     │
│     │ conversation_state table                                      │     │
│     ├───────────────────────────────────────────────────────────────┤     │
│     │ id: 102                                                       │     │
│     │ phone_number: "9876543210"  ← Different user                  │     │
│     │ conversation_flow: "main_menu"  ← SAME template               │     │
│     │ current_step: "initial"                                       │     │
│     │ context: {}                                                   │     │
│     │ created_at: 2025-01-06 16:30:00  ← Different time            │     │
│     └───────────────────────────────────────────────────────────────┘     │
│     ↓                                                                       │
│  5. Sends SAME menu to this user (from SAME template)                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

✅ SAME template used (from DB)
✅ DIFFERENT conversation_state created
✅ Each user has their own conversation tracking
```

---

## Visual Comparison

### What Gets Created ONCE

```
workflow_templates table (The Menu Cards 📋)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Created: ONE TIME (by admin running script)
Lifetime: PERMANENT (or until manually deleted)
Shared by: ALL USERS

┌──────────────────────────────────────────┐
│ Template: main_menu                      │
│ Type: button                             │
│ Keywords: [hi, hello, start]             │
│ Menu: { ... definition ... }             │
│ Active: true                             │
│ Created: 2025-01-06 10:00:00            │
└──────────────────────────────────────────┘
       ↓ ↓ ↓ ↓ ↓
       Used by ALL customers

┌──────────────────────────────────────────┐
│ Template: new_order                      │
│ Type: list                               │
│ Keywords: [order, buy]                   │
│ Menu: { ... definition ... }             │
│ Active: true                             │
│ Created: 2025-01-06 10:00:00            │
└──────────────────────────────────────────┘
       ↓ ↓ ↓ ↓ ↓
       Used by ALL customers
```

### What Gets Created MANY TIMES

```
conversation_state table (The Order Slips 🧾)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Created: EVERY TIME a user starts conversation
Lifetime: TEMPORARY (expires after 24 hours)
Unique to: EACH USER

┌────────────────────────────────────────────┐
│ User: 1234567890                           │
│ Flow: main_menu  ← References template     │
│ Step: initial                              │
│ Context: {}                                │
│ Created: 2025-01-06 14:30:00              │
│ Expires: 2025-01-07 14:30:00              │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│ User: 9876543210                           │
│ Flow: main_menu  ← SAME template           │
│ Step: product_selection  ← Different step  │
│ Context: {"product": "coffee"}             │
│ Created: 2025-01-06 16:30:00              │
│ Expires: 2025-01-07 16:30:00              │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│ User: 5555555555                           │
│ Flow: new_order  ← Different template      │
│ Step: quantity                             │
│ Context: {"product": "tea", "qty": 2}      │
│ Created: 2025-01-06 18:30:00              │
│ Expires: 2025-01-07 18:30:00              │
└────────────────────────────────────────────┘
```

---

## Database State Over Time

### Day 1 - Morning (After running setup script)

```sql
-- workflow_templates table
SELECT COUNT(*) FROM workflow_templates;
-- Result: 4 templates (main_menu, new_order, support, account)

-- conversation_state table
SELECT COUNT(*) FROM conversation_state;
-- Result: 0 (no users have messaged yet)
```

### Day 1 - Afternoon (10 users messaged)

```sql
-- workflow_templates table
SELECT COUNT(*) FROM workflow_templates;
-- Result: 4 templates (SAME as morning - unchanged)

-- conversation_state table
SELECT COUNT(*) FROM conversation_state;
-- Result: 10 (one per user who messaged)

SELECT phone_number, conversation_flow FROM conversation_state;
-- Results:
-- 1234567890 | main_menu
-- 9876543210 | new_order
-- 5555555555 | main_menu
-- 1111111111 | support
-- ... (6 more rows)
```

### Day 2 - Morning (24 hours later, after cleanup)

```sql
-- workflow_templates table
SELECT COUNT(*) FROM workflow_templates;
-- Result: 4 templates (STILL the same - permanent)

-- conversation_state table (after cleanup of expired)
SELECT COUNT(*) FROM conversation_state;
-- Result: 2 (only active conversations, expired ones deleted)
```

### Day 30 - After 1000 customers

```sql
-- workflow_templates table
SELECT COUNT(*) FROM workflow_templates;
-- Result: 4 templates (STILL the same - permanent)

-- conversation_state table
SELECT COUNT(*) FROM conversation_state;
-- Result: ~50 (only currently active conversations)
```

---

## Code Flow Explanation

### When You Run the Setup Script

```python
# This runs ONCE
def main():
    with get_db_session() as db:
        service = ConversationService(db)
        
        # Creates and SAVES to database
        create_main_menu_template(service)
        create_new_order_template(service)
        create_support_template(service)
        create_account_template(service)

def create_main_menu_template(service):
    service.create_template(
        template_name="main_menu",
        template_type="button",
        menu_structure={...},
        trigger_keywords=["hi", "hello", "start"]
    )
    # This does: INSERT INTO workflow_templates VALUES (...)
    # Template is now STORED IN DATABASE
```

### When User Sends "hi"

```python
# This runs EVERY TIME a user messages
async def handle_text_message(phone_number, text):
    
    # Step 1: Look for template in database
    template = service.find_template_by_keyword(text)
    # SQL: SELECT * FROM workflow_templates 
    #      WHERE 'hi' = ANY(trigger_keywords)
    # Returns: The main_menu template (stored in DB)
    
    # Step 2: Create NEW conversation for THIS user
    conversation = service.start_conversation(
        phone_number=phone_number,
        template_name=template.template_name
    )
    # SQL: INSERT INTO conversation_state VALUES (...)
    # Creates: NEW row in conversation_state
    
    # Step 3: Get menu structure from template
    menu = template.menu_structure  # Read from DB
    
    # Step 4: Send menu to user
    await send_menu(phone_number, menu)
```

### When User Clicks a Button

```python
# Still uses the SAME template from database
async def handle_button_click(phone_number, button_id):
    
    # Get user's active conversation
    conversation = service.get_conversation(phone_number)
    # SQL: SELECT * FROM conversation_state 
    #      WHERE phone_number = '1234567890'
    # Returns: This user's conversation state
    
    # Get the template (from DB)
    template = service.get_template(conversation.conversation_flow)
    # SQL: SELECT * FROM workflow_templates
    #      WHERE template_name = 'main_menu'
    # Returns: The SAME template used earlier
    
    # Update conversation state
    service.update_conversation(
        phone_number=phone_number,
        current_step="next_step"
    )
    # SQL: UPDATE conversation_state 
    #      SET current_step = 'next_step'
    #      WHERE phone_number = '1234567890'
    # Updates: THIS user's conversation only
```

---

## Analogy: Restaurant Menu

Think of it like a restaurant:

### The Menu (workflow_templates)

```
┌────────────────────────────────────┐
│  RESTAURANT MENU                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                    │
│  Appetizers                        │
│    - Soup ............ $5          │
│    - Salad ........... $6          │
│                                    │
│  Main Course                       │
│    - Steak ........... $20         │
│    - Fish ............ $18         │
│                                    │
│  Desserts                          │
│    - Ice Cream ....... $4          │
│    - Cake ............ $5          │
│                                    │
└────────────────────────────────────┘

Created: ONCE (printed and laminated)
Used by: ALL customers
Lifetime: Until menu changes (permanent)
```

### The Order Slip (conversation_state)

```
┌────────────────────────────────────┐
│  ORDER SLIP - Table 5              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                    │
│  Customer: John                    │
│  Time: 7:30 PM                     │
│                                    │
│  ☑ Soup                            │
│  ☑ Steak                           │
│  ☐ Dessert (not decided yet)       │
│                                    │
│  Total so far: $25                 │
│                                    │
└────────────────────────────────────┘

Created: NEW for each customer
Used by: ONE customer only
Lifetime: Until meal is finished (temporary)
Discarded: After customer leaves
```

**The Process:**

1. **Restaurant prints menu** (admin runs setup script)
   - Menu stored in kitchen (templates in database)
   - Menu never changes unless owner updates it

2. **Customer arrives** (user sends "hi")
   - Waiter gives them the menu (system finds template in DB)
   - Waiter creates new order slip (system creates conversation_state)

3. **Customer orders soup** (user clicks button)
   - Waiter marks on order slip (system updates conversation_state)
   - Waiter refers to menu for prices (system reads template from DB)

4. **Customer orders steak** (user makes another selection)
   - Waiter adds to SAME order slip (system updates conversation_state)
   - Waiter still uses SAME menu (system reads SAME template from DB)

5. **Customer finishes meal** (conversation completes)
   - Order slip discarded (conversation_state deleted)
   - Menu stays for next customer (template remains in DB)

6. **Next customer arrives** (another user sends "hi")
   - Gets SAME menu (SAME template from DB)
   - Gets NEW order slip (NEW conversation_state)

---

## Key Takeaways

### Templates (workflow_templates)

✅ **Created:** ONCE by admin running script
✅ **Stored:** In database permanently
✅ **Used:** By ALL users
✅ **Modified:** Only when admin updates them
✅ **Deleted:** Only manually by admin
✅ **Purpose:** Define what menus exist

**Analogy:** Restaurant menu card

### Conversations (conversation_state)

✅ **Created:** EVERY TIME a user starts interaction
✅ **Stored:** In database temporarily (24 hours)
✅ **Used:** By ONE user only
✅ **Modified:** Every time user takes action
✅ **Deleted:** Automatically when expired or completed
✅ **Purpose:** Track individual user's progress

**Analogy:** Individual order slip

---

## Common Scenarios

### Scenario 1: 100 Users Send "hi" on Same Day

```
Templates Created: 0 (already exist)
Conversations Created: 100 (one per user)

Database State:
  workflow_templates: 4 rows (unchanged)
  conversation_state: 100 rows (one per user)

All 100 users see SAME menu (from SAME template)
Each has their OWN conversation tracking
```

### Scenario 2: User Sends "hi" Again Next Day

```
Templates Created: 0 (still exist)
Conversations Created: 1 (new one)

Old conversation: DELETED (expired)
New conversation: CREATED (fresh start)

User sees SAME menu (SAME template)
But conversation_state is NEW (fresh context)
```

### Scenario 3: Admin Updates Template

```
Admin runs:
  service.update_template(
      "main_menu",
      menu_structure={...new menu...}
  )

Result:
  - Template in DB is updated
  - ALL future users see new menu
  - Existing active conversations unaffected
  
Next user who sends "hi":
  - Sees NEW updated menu
  - Gets NEW conversation_state
```

---

## Verification Queries

### Check Templates (Should Stay Constant)

```sql
-- See all templates
SELECT template_name, is_active, created_at 
FROM workflow_templates 
ORDER BY created_at;

-- Count templates
SELECT COUNT(*) FROM workflow_templates;
-- Should be 4 (or however many you created)

-- Check a specific template
SELECT * FROM workflow_templates 
WHERE template_name = 'main_menu';
```

### Check Active Conversations (Changes Frequently)

```sql
-- See all active conversations
SELECT phone_number, conversation_flow, current_step, created_at
FROM conversation_state
WHERE expires_at > NOW()
ORDER BY created_at DESC;

-- Count active conversations
SELECT COUNT(*) FROM conversation_state
WHERE expires_at > NOW();
-- Will vary based on active users

-- See which templates are being used
SELECT conversation_flow, COUNT(*) as user_count
FROM conversation_state
WHERE expires_at > NOW()
GROUP BY conversation_flow;
```

---

## Summary

**The Setup Script:**
- ✅ Runs ONCE
- ✅ Creates templates in database
- ✅ Templates stay there FOREVER (until you delete them)

**When Users Message:**
- ✅ System READS template from database
- ✅ System CREATES new conversation_state for that user
- ✅ SAME template used for ALL users
- ✅ DIFFERENT conversation_state for EACH user

**The Flow:**
```
Run setup script (ONCE)
    ↓
Templates stored in DB
    ↓
User 1 sends "hi"
    ↓
System finds template in DB (reads)
System creates conversation_state (writes)
    ↓
User 2 sends "hi" 
    ↓
System finds SAME template in DB (reads)
System creates NEW conversation_state (writes)
    ↓
... repeat for all users ...
    ↓
Templates NEVER change (unless admin updates)
Conversation_states come and go
```

---

**Last Updated:** 2025-01-06  
**File:** TEMPLATE_REUSE_EXPLANATION.md
