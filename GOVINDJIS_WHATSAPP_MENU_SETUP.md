# Govindji's Jewelry - WhatsApp Interactive Menu Setup

## Overview

This document explains the WhatsApp interactive menu system configured for Govindji's Jewelry store.

---

## Main Menu

**Trigger Keywords (case-insensitive):**
- hi
- hello
- hey
- start
- menu
- help

**Welcome Message:**
```
✨ Welcome to Govindji's, where you'll experience exquisite craftsmanship 
and unparalleled quality in Gold and Diamond jewelry that has been trusted 
for over six decades.
```

**Button Options:**

1. **💎 Explore Collection**
   - Button ID: `explore_collection`
   - Action: Shows collection categories and information

2. **👨‍💼 Talk to Expert**
   - Button ID: `talk_to_expert`
   - Action: Connects customer with jewelry consultant

3. **📍 Visit Us**
   - Button ID: `visit_us`
   - Action: Shows showroom address and hours

---

## User Flow

### Flow 1: Customer Sends "Hi"

```
Customer: "hi"
    ↓
System: Detects keyword (case-insensitive)
    ↓
System: Finds "main_menu" template
    ↓
System: Creates conversation_state for customer
    ↓
System: Sends welcome message with 3 buttons
    ↓
Customer: Clicks button
    ↓
System: Processes selection and shows relevant info
```

### Flow 2: Customer Clicks "Explore Collection"

```
Customer: Clicks "💎 Explore Collection"
    ↓
System: Shows collection information:
  • Gold Jewelry - Traditional & Contemporary
  • Diamond Jewelry - For every occasion
  • Bridal Collection - Special day pieces
  • Custom Designs - Your vision
    ↓
System: Asks if they want to speak with consultant
```

### Flow 3: Customer Clicks "Talk to Expert"

```
Customer: Clicks "👨‍💼 Talk to Expert"
    ↓
System: Explains expert services:
  • Find perfect piece
  • Understand quality/craftsmanship
  • Custom design consultation
  • Repair/maintenance
    ↓
System: Asks for name and requirement
    ↓
Customer: Provides details
    ↓
System: Confirms expert will contact within 24 hours
```

### Flow 4: Customer Clicks "Visit Us"

```
Customer: Clicks "📍 Visit Us"
    ↓
System: Shows:
  • Showroom address
  • Business hours
  • Contact information
  • Parking details
    ↓
System: Offers directions
```

---

## Template Details

### 1. Main Menu Template

**Name:** `main_menu`
**Type:** `button`
**Status:** Active

**Structure:**
```json
{
  "type": "button",
  "body": {
    "text": "Welcome message..."
  },
  "action": {
    "buttons": [
      {
        "type": "reply",
        "reply": {
          "id": "explore_collection",
          "title": "💎 Explore Collection"
        }
      },
      {
        "type": "reply",
        "reply": {
          "id": "talk_to_expert",
          "title": "👨‍💼 Talk to Expert"
        }
      },
      {
        "type": "reply",
        "reply": {
          "id": "visit_us",
          "title": "📍 Visit Us"
        }
      }
    ]
  }
}
```

**Trigger Keywords:** `["hi", "hello", "hey", "start", "menu", "help"]`

### 2. Explore Collection Template

**Name:** `explore_collection`
**Type:** `text`
**Status:** Active

**Message:**
```
💎 Explore Our Exquisite Collection

At Govindji's, we offer:

🔸 Gold Jewelry - Traditional & Contemporary designs
🔸 Diamond Jewelry - Stunning pieces for every occasion
🔸 Bridal Collection - Make your special day unforgettable
🔸 Custom Designs - Bring your vision to life

Visit our showroom or website to view our complete collection.

Would you like to speak with our jewelry consultant?
```

**Trigger Keywords:** `["collection", "jewelry", "explore", "catalog"]`

### 3. Talk to Expert Template

**Name:** `talk_to_expert`
**Type:** `text`
**Status:** Active

**Message:**
```
👨‍💼 Connect with Our Jewelry Experts

Our experienced consultants are here to help you:

✓ Find the perfect piece
✓ Understand jewelry quality and craftsmanship
✓ Custom design consultation
✓ Repair and maintenance services

Please share your:
1. Name
2. What you're looking for

Our expert will contact you shortly!
```

**Trigger Keywords:** `["expert", "consultant", "help", "advice"]`

### 4. Visit Us Template

**Name:** `visit_us`
**Type:** `text`
**Status:** Active

**Message:**
```
📍 Visit Govindji's Showroom

🏪 Address:
[Your Showroom Address]
[City, State, ZIP]

⏰ Business Hours:
Monday - Saturday: 10:00 AM - 8:00 PM
Sunday: 11:00 AM - 6:00 PM

📞 Contact:
Phone: [Your Phone Number]
Email: [Your Email]

🚗 We're conveniently located with ample parking.

Would you like directions?
```

**Trigger Keywords:** `["visit", "location", "address", "showroom", "store"]`

⚠️ **Action Required:** Update this template with your actual address and contact details.

---

## Installation & Setup

### Step 1: Verify Database Tables

```bash
psql -h YOUR_DB_HOST -U postgres -d postgres -c "
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN ('conversation_state', 'workflow_templates');"
```

Expected: 2 rows

### Step 2: Update Contact Information

Edit `backend/scripts/create_initial_templates.py`:

Find the `visit_structure` section and update:
- `[Your Showroom Address]` → Actual address
- `[City, State, ZIP]` → Actual location
- `[Your Phone Number]` → Actual phone
- `[Your Email]` → Actual email

Update business hours if different.

### Step 3: Run Template Creation

```bash
cd backend
python -m scripts.create_initial_templates
```

### Step 4: Verify Templates Created

```bash
psql $DATABASE_URL -c "SELECT template_name, is_active FROM workflow_templates;"
```

Expected output:
```
  template_name    | is_active 
-------------------+-----------
 main_menu         | t
 explore_collection| t
 talk_to_expert    | t
 visit_us          | t
```

### Step 5: Test

Send "hi" to your WhatsApp Business number.

Expected: Receive welcome message with 3 buttons.

---

## Testing Scenarios

### Test 1: Main Menu Trigger

**Input:** Send "hi" (or "HELLO", "Hey", etc.)

**Expected Output:**
```
✨ Welcome to Govindji's, where you'll experience exquisite...

[Button: 💎 Explore Collection]
[Button: 👨‍💼 Talk to Expert]
[Button: 📍 Visit Us]
```

### Test 2: Explore Collection Button

**Input:** Click "💎 Explore Collection"

**Expected Output:**
```
💎 Explore Our Exquisite Collection

At Govindji's, we offer:
...
```

### Test 3: Talk to Expert Button

**Input:** Click "👨‍💼 Talk to Expert"

**Expected Output:**
```
👨‍💼 Connect with Our Jewelry Experts

Our experienced consultants are here to help you:
...
```

### Test 4: Visit Us Button

**Input:** Click "📍 Visit Us"

**Expected Output:**
```
📍 Visit Govindji's Showroom

🏪 Address:
[Your address]
...
```

### Test 5: Keyword Triggers

**Input:** Send "collection" directly

**Expected:** Shows collection information (bypasses main menu)

**Input:** Send "expert"

**Expected:** Shows expert connection info (bypasses main menu)

### Test 6: Case Insensitivity

**Input:** "HI", "Hi", "hi", "HELLO", "hello"

**Expected:** All trigger the main menu (case doesn't matter)

---

## Database Structure

### Templates Created

```sql
-- Main menu
INSERT INTO workflow_templates VALUES (
  id: UUID,
  template_name: 'main_menu',
  template_type: 'button',
  trigger_keywords: ['hi', 'hello', 'hey', 'start', 'menu', 'help'],
  menu_structure: {...},
  is_active: true
);

-- Explore collection
INSERT INTO workflow_templates VALUES (
  template_name: 'explore_collection',
  template_type: 'text',
  trigger_keywords: ['collection', 'jewelry', 'explore', 'catalog'],
  ...
);

-- Talk to expert
INSERT INTO workflow_templates VALUES (
  template_name: 'talk_to_expert',
  template_type: 'text',
  trigger_keywords: ['expert', 'consultant', 'help', 'advice'],
  ...
);

-- Visit us
INSERT INTO workflow_templates VALUES (
  template_name: 'visit_us',
  template_type: 'text',
  trigger_keywords: ['visit', 'location', 'address', 'showroom', 'store'],
  ...
);
```

### When Customer Sends "Hi"

```sql
-- Conversation state created
INSERT INTO conversation_state VALUES (
  id: UUID,
  phone_number: '1234567890',
  conversation_flow: 'main_menu',
  current_step: 'initial',
  context: {},
  last_interaction: NOW(),
  expires_at: NOW() + INTERVAL '24 hours'
);
```

---

## Customization

### Change Welcome Message

Edit `backend/scripts/create_initial_templates.py`:

```python
"body": {
    "text": "Your new welcome message here"
}
```

### Change Button Titles

```python
{
    "type": "reply",
    "reply": {
        "id": "explore_collection",
        "title": "Your Button Text"  # Max 20 characters
    }
}
```

### Add More Buttons

WhatsApp allows maximum 3 buttons. To add more options, use a list menu instead:

```python
"type": "list"  # Instead of "button"
```

### Change Trigger Keywords

```python
trigger_keywords=["your", "keywords", "here"]
```

Keywords are automatically case-insensitive.

### Update Collection Info

Edit the `explore_structure` in `create_additional_templates()`:

```python
"text": "Your updated collection information"
```

---

## Maintenance

### Update Templates

1. Edit the template script
2. Delete old template:
   ```sql
   DELETE FROM workflow_templates WHERE template_name = 'template_name';
   ```
3. Run script again:
   ```bash
   python -m scripts.create_initial_templates
   ```

### Check Active Conversations

```sql
SELECT phone_number, conversation_flow, current_step, created_at
FROM conversation_state
WHERE expires_at > NOW()
ORDER BY created_at DESC;
```

### Clean Up Expired Conversations

```bash
cd backend
python -c "
from app.core.database import init_database, get_db_session
from app.services.conversation_service import ConversationService
init_database()
with get_db_session() as db:
    count = ConversationService(db).cleanup_expired_conversations()
    print(f'Cleaned up {count} conversations')
"
```

### View Template Details

```sql
SELECT template_name, template_type, trigger_keywords, is_active
FROM workflow_templates
ORDER BY template_name;
```

---

## Troubleshooting

### Issue: Menu Not Appearing

**Check:**
1. Templates exist: `SELECT COUNT(*) FROM workflow_templates;`
2. Keywords match: `SELECT trigger_keywords FROM workflow_templates WHERE template_name='main_menu';`
3. Template active: `SELECT is_active FROM workflow_templates WHERE template_name='main_menu';`

**Solution:**
```bash
python -m scripts.create_initial_templates
```

### Issue: Buttons Not Working

**Check:**
1. Button IDs match template steps
2. Conversation state exists for user
3. Logs show button processing

**Solution:**
Check logs for errors, verify button IDs in menu_structure.

### Issue: "Hi" Not Triggering

**Verify:**
1. Keyword in trigger_keywords array
2. Case insensitive matching enabled (it is by default)
3. Template is active

**Test:**
```sql
SELECT * FROM workflow_templates 
WHERE 'hi' = ANY(trigger_keywords);
```

---

## Logs to Monitor

### Successful Flow

```
🎯 Template 'main_menu' matched keyword 'hi'
🆕 Started conversation: 1234567890 -> main_menu
🔘 Interactive selection processed: selection_processed
```

### Errors to Watch

```
❌ Template not found: main_menu
⚠️ No active conversation for interactive message
📭 No template matched for: random text
```

---

## Contact for Support

If you need help customizing the templates or encounter issues:

1. Check the logs for error messages
2. Verify database tables exist
3. Ensure templates are created and active
4. Test with simple keywords first

---

## Summary

✅ **Main Menu:** Welcome message with 3 buttons
✅ **Explore Collection:** Shows jewelry categories
✅ **Talk to Expert:** Connects with consultant
✅ **Visit Us:** Shows location and hours

🔑 **Trigger:** "hi", "hello" (case-insensitive)
📱 **Platform:** WhatsApp Business API
💾 **Storage:** PostgreSQL database
⏱️ **Expiry:** Conversations expire after 24 hours

---

**Last Updated:** 2025-01-06
**Store:** Govindji's Jewelry
**Status:** Ready to deploy (update address first!)
