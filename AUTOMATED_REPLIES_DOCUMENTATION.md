# Automated Replies System - Complete Documentation

## Overview

The automated replies system is an intelligent message processing engine that automatically responds to incoming WhatsApp messages based on predefined rules and patterns. It operates 24/7, handling common queries, managing subscriptions, and providing instant responses to customers.

---

## System Architecture

### Key Components

1. **ReplyAutomation Engine** (`backend/app/services/reply_automation.py`)
   - Core automation logic
   - Rule matching and prioritization
   - Business hours management

2. **WhatsApp Service** (`backend/app/services/whatsapp_service.py`)
   - Message processing orchestration
   - Triggers automated replies

3. **Messaging Service** (`backend/app/services/messaging_service.py`)
   - High-level messaging functions
   - SQS queue integration

---

## How It Works

### Message Flow

```
Incoming WhatsApp Message
         ↓
   Webhook Handler
         ↓
  Message Processor (SQS Worker)
         ↓
  WhatsAppService.process_text_message()
         ↓
  _process_automated_reply_direct()
         ↓
  ReplyAutomation.process_incoming_message()
         ↓
  Rule Matching & Priority Selection
         ↓
  Send Automated Reply (via SQS)
         ↓
  Outgoing Message Queue
         ↓
  WhatsApp API (Message Sent)
```

### Triggering Points

Automated replies are triggered from two locations:

1. **Message Processor Worker** (`backend/start.py`)
   - Primary trigger point
   - Called during message processing
   - Location: `WhatsAppService._process_automated_reply_direct()`

2. **Direct Processing** (legacy, less used)
   - Webhook direct processing
   - Location: `WhatsAppService._process_automated_reply()`

---

## Reply Rules System

### Rule Structure

Each reply rule consists of:

```python
ReplyRule(
    name="rule_name",              # Unique identifier
    condition=r"regex_pattern",    # Pattern to match
    reply_type="text",             # Type: text, template, document, etc.
    reply_data={...},              # Response data
    priority=10,                   # Priority (higher = first)
    active=True                    # Enable/disable rule
)
```

### Rule Priority Levels

| Priority | Category | Description |
|----------|----------|-------------|
| 20 | Critical | STOP/START commands (always processed first) |
| 10 | High | Greetings and immediate responses |
| 6-8 | Medium | FAQs, information requests |
| 1-5 | Low | Business hours, general info |
| 0 | Fallback | Catch-all responses |

---

## Available Rules

### 1. Subscription Management (Priority: 20)

**Unsubscribe Rule**
- **Keywords**: `stop`, `unsubscribe`, `opt out`, `optout`, `cancel`
- **Action**: Marks user as unsubscribed in database
- **Response**: Confirmation message with resubscribe instructions
- **Effect**: User will NOT receive template messages but can still receive automated replies
- **Database Update**: Sets `is_subscribed=False` in `user_profiles` table

**Resubscribe Rule**
- **Keywords**: `start`, `subscribe`, `opt in`, `optin`, `resume`
- **Action**: Marks user as subscribed in database
- **Response**: Welcome back confirmation
- **Effect**: User will receive all template messages again
- **Database Update**: Sets `is_subscribed=True` in `user_profiles` table

### 2. Greetings (Priority: 10)

**General Greeting**
- **Keywords**: `hi`, `hello`, `hey`, `greetings`
- **Response**: "Hello! 👋 Welcome to our WhatsApp Business. How can I help you today?"

**Morning Greeting**
- **Keywords**: `good morning`, `morning`
- **Response**: "Good morning! ☀️ Hope you're having a great day. How can I assist you?"

### 3. FAQs (Priority: 6-8)

**Business Hours**
- **Keywords**: `hours`, `open`, `close`, `timing`, `schedule`
- **Response**: Business hours information (9 AM - 5 PM, Mon-Fri)

**Pricing Information**
- **Keywords**: `price`, `cost`, `rate`, `pricing`, `how much`, `fee`
- **Response**: Pricing inquiry acknowledgment

**Support**
- **Keywords**: `support`, `help`, `issue`, `problem`, `bug`, `error`
- **Response**: Support assistance offer

**Contact Information**
- **Keywords**: `contact`, `phone`, `email`, `address`, `location`
- **Response**: Full contact details

### 4. Business Hours Response (Priority: 1)

**After-Hours Message**
- **Condition**: Outside business hours (Mon-Fri 9 AM - 5 PM)
- **Response**: "Thank you for contacting us! 🕒 Our business hours are 9 AM - 5 PM (Mon-Fri)..."
- **Note**: Only sent OUTSIDE business hours

### 5. Fallback (Priority: 0)

**Unknown Message**
- **Condition**: Matches any message that didn't match other rules
- **Response**: Generic acknowledgment and follow-up promise

---

## Business Hours System

### Configuration

```python
class BusinessHours:
    start_time: time = time(9, 0)    # 9:00 AM
    end_time: time = time(17, 0)     # 5:00 PM
    weekdays_only: bool = True       # Monday-Friday only
```

### How Business Hours Work

1. **Checking Business Hours**
   - Current time is compared against configured hours
   - Weekend check (Saturday=5, Sunday=6)
   - Returns `True` if within business hours, `False` otherwise

2. **Effect on Automated Replies**
   - **During Business Hours**: All rules work normally EXCEPT "business_hours_closed" rule
   - **Outside Business Hours**: "business_hours_closed" rule activates for generic messages
   - **STOP/START commands**: Always processed regardless of business hours
   - **FAQ responses**: Always sent regardless of business hours

3. **Important Note**: 
   - Business hours checking **ONLY prevents the after-hours message** from being sent during business hours
   - It does **NOT block** other automated replies
   - All greetings, FAQs, and subscription commands work 24/7

### Example Scenarios

**Scenario 1: User says "Hi" at 10 AM (Business Hours)**
- ✅ Greeting rule matches (priority 10)
- ✅ Response sent: "Hello! 👋 Welcome..."
- ❌ Business hours closed message NOT sent (because it's business hours)

**Scenario 2: User says "Hi" at 8 PM (After Hours)**
- ✅ Greeting rule matches (priority 10)
- ✅ Response sent: "Hello! 👋 Welcome..."
- ❌ After-hours message NOT sent (because greeting rule has higher priority)

**Scenario 3: User asks unclear question at 8 PM (After Hours)**
- ❌ No high-priority rules match
- ✅ After-hours message sent (priority 1, business hours check passes)

**Scenario 4: User says "STOP" at any time**
- ✅ Always processed (priority 20)
- ✅ User unsubscribed immediately
- ✅ Confirmation sent

---

## Subscription System

### How Subscriptions Work

The system has two types of messages:

1. **Template Messages** (Marketing)
   - Respect subscription status
   - Only sent to subscribed users
   - Examples: Campaign messages, promotional templates

2. **Automated Replies** (Customer Service)
   - Always sent regardless of subscription status
   - Examples: Greetings, FAQs, support responses

### Subscription Status Management

**Database Table**: `user_profiles`
- **Column**: `is_subscribed` (Boolean)
- **Default**: `true` (users are subscribed by default)

**How to Unsubscribe**:
1. User sends: `STOP`, `unsubscribe`, `opt out`, `optout`, or `cancel`
2. System updates database: `is_subscribed = False`
3. User receives confirmation message
4. Effect: No more marketing templates, but automated replies still work

**How to Resubscribe**:
1. User sends: `START`, `subscribe`, `opt in`, `optin`, or `resume`
2. System updates database: `is_subscribed = True`
3. User receives welcome back message
4. Effect: Marketing templates resume

### Code Flow for Subscription

```python
# When sending template messages
async def send_template_message(..., check_subscription=True):
    if check_subscription:
        user_repo = UserRepository(db)
        is_subscribed = user_repo.is_user_subscribed(phone_number)
        
        if not is_subscribed:
            logger.warning(f"User {phone_number} is unsubscribed - template not sent")
            return None
    
    # Send template only if subscribed
```

### Repository Methods

Located in `backend/app/repositories/user_repository.py`:

```python
def is_user_subscribed(self, phone_number: str) -> bool:
    """Check if user is subscribed to receive templates"""
    user = self.get_by_phone_number(phone_number)
    return user.is_subscribed if user else True

def unsubscribe_user(self, phone_number: str):
    """Unsubscribe user from template messages"""
    user = self.get_by_phone_number(phone_number)
    if user:
        user.is_subscribed = False
        self.db.commit()

def resubscribe_user(self, phone_number: str):
    """Resubscribe user to template messages"""
    user = self.get_by_phone_number(phone_number)
    if user:
        user.is_subscribed = True
        self.db.commit()

def get_subscribed_users(self) -> List[UserProfile]:
    """Get all subscribed users"""
    return self.db.query(UserProfile).filter(
        UserProfile.is_subscribed == True
    ).all()
```

---

## Rule Matching Algorithm

### Step-by-Step Process

1. **Normalize Input**
   - Convert message to lowercase
   - Remove extra whitespace

2. **Check Each Rule**
   - Test rule's condition against message
   - Use regex matching for patterns
   - Skip inactive rules

3. **Collect Matching Rules**
   - Multiple rules may match the same message

4. **Select Highest Priority**
   - Sort by priority (descending)
   - Return the highest priority matching rule

5. **Special Conditions**
   - Business hours check for after-hours rule
   - Subscription status for STOP/START commands

### Pattern Matching Examples

```python
# Exact match (case-insensitive)
condition = r"^\s*(stop|unsubscribe)\s*$"
# Matches: "stop", "STOP", " stop ", "unsubscribe"
# Doesn't match: "please stop", "stopping"

# Keyword anywhere in message
condition = r"\b(hello|hi|hey)\b"
# Matches: "Hi there", "Hello!", "hey how are you"
# Doesn't match: "high", "hotel" (word boundary \b)

# Wildcard (matches everything)
condition = "*"
# Always matches (used for fallback)
```

---

## Message Processing Details

### What Messages Get Auto-Replies?

✅ **Processed**:
- Text messages from users
- Messages during business hours
- Messages after business hours
- STOP/START commands
- FAQ keywords

❌ **NOT Processed**:
- Media messages (images, videos, documents)
- Interactive messages (buttons, lists)
- Location messages
- Status updates
- Read receipts

### Processing Steps

```python
async def process_incoming_message(
    phone_number: str,
    message_text: str,
    message_type: str = "text",
    user_context: Dict = None
) -> Optional[str]:
    
    # 1. Check message type
    if message_type != "text":
        return None  # Skip non-text messages
    
    # 2. Normalize text
    normalized_text = message_text.lower().strip()
    
    # 3. Find matching rule
    matching_rule = self._find_matching_rule(normalized_text)
    
    # 4. Handle STOP/START (highest priority)
    if matching_rule.name == "unsubscribe_stop":
        await self._handle_unsubscribe(phone_number)
        return await self._send_automated_reply(...)
    
    if matching_rule.name == "resubscribe_start":
        await self._handle_resubscribe(phone_number)
        return await self._send_automated_reply(...)
    
    # 5. Check business hours for specific rules
    if matching_rule.name == "business_hours_closed":
        if self.business_hours.is_business_hours():
            return None  # Skip during business hours
    
    # 6. Send automated reply
    reply_message_id = await self._send_automated_reply(...)
    
    return reply_message_id
```

---

## Sending Automated Replies

### Reply Data Structure

```python
reply_data = {
    "type": "text",              # Message type
    "content": "Hello! 👋..."    # Message content
}

# For templates
reply_data = {
    "type": "template",
    "template_name": "greeting",
    "parameters": [...]
}

# For media
reply_data = {
    "type": "image",
    "media_url": "https://...",
    "content": "Caption text"
}
```

### Metadata Added

```python
metadata = {
    "rule_name": "greeting_hi",
    "reply_type": "text",
    "automated": True,
    "timestamp": "2024-01-01T10:00:00",
    "priority": "high",  # or "normal"
    "context": {
        "original_message": "Hi",
        "user_context": {...}
    }
}
```

### Queue Integration

Automated replies are sent through SQS:

```python
message_id = await send_outgoing_message(
    phone_number=phone_number,
    message_data=reply_data,
    metadata=metadata
)
```

Flow:
1. Reply data queued to `outgoing-messages` SQS queue
2. Outgoing message worker picks up message
3. WhatsApp API sends message
4. Status updates tracked via webhook

---

## Database Updates

### Tables Updated by Automated Replies

1. **user_profiles**
   - `is_subscribed`: Updated by STOP/START commands
   - `last_interaction_at`: Updated on every message
   - `last_message`: Stores last message content

2. **whatsapp_messages**
   - Outgoing automated reply messages stored
   - `direction`: "outgoing"
   - `status`: "sent" → "delivered" → "read"
   - `content`: Reply message text

3. **business_metrics**
   - `total_messages_received`: Incremented
   - `total_responses_sent`: Incremented for automated replies
   - `unique_users`: Updated daily count
   - `response_time_avg_seconds`: Updated with reply time

---

## Customization Guide

### Adding a New Reply Rule

```python
# In reply_automation.py, add to _setup_default_rules()

self.rules.append(
    ReplyRule(
        name="custom_rule_name",
        condition=r"\b(keyword1|keyword2)\b",
        reply_type="text",
        reply_data={
            "type": "text",
            "content": "Your custom response here"
        },
        priority=7,  # Choose appropriate priority
        active=True
    )
)
```

### Modifying Business Hours

```python
# Update in ReplyAutomation initialization
reply_automation.update_business_hours(
    start_time=time(8, 0),   # 8:00 AM
    end_time=time(18, 0),    # 6:00 PM
    weekdays_only=True
)
```

### Adding Custom Rule Programmatically

```python
from app.services.reply_automation import reply_automation, ReplyRule

# Create custom rule
custom_rule = ReplyRule(
    name="holiday_greeting",
    condition=r"\b(happy new year|merry christmas)\b",
    reply_type="text",
    reply_data={
        "type": "text",
        "content": "Happy Holidays! 🎉"
    },
    priority=9
)

# Add to automation engine
reply_automation.add_custom_rule(custom_rule)
```

### Removing a Rule

```python
from app.services.reply_automation import reply_automation

# Remove by name
reply_automation.remove_rule("greeting_good_morning")
```

---

## Testing Automated Replies

### Manual Testing

1. Send test message via WhatsApp to your business number
2. Check App Runner logs for processing:
   ```
   🤖 Automated reply queued for [phone]: [message_id]
   ✅ Auto-reply sent to [phone] using rule '[rule_name]': [message_id]
   ```

3. Verify response received on WhatsApp

### Test Cases

| Test Case | Input | Expected Rule | Expected Response |
|-----------|-------|---------------|-------------------|
| Greeting | "Hi" | greeting_hi | "Hello! 👋 Welcome..." |
| Unsubscribe | "STOP" | unsubscribe_stop | "✅ You have been unsubscribed..." |
| Resubscribe | "START" | resubscribe_start | "✅ Welcome back!..." |
| Business Hours | "hours" | faq_hours | "🕒 Our business hours are..." |
| After Hours | "test" at 8 PM | business_hours_closed | "Thank you... Our hours are..." |
| Unknown | "xyz123" | fallback_unknown | "Thank you for your message!..." |

### Checking Logs

```bash
# In AWS App Runner logs, search for:
- "🤖 Automated reply queued"
- "✅ Auto-reply sent"
- "📵 User .* sent STOP"
- "✅ User .* sent START"
- "❌ Error processing auto-reply"
```

---

## Troubleshooting

### Common Issues

**Issue**: Automated replies not being sent

**Possible Causes**:
1. Message type is not "text" → Check logs for "Skipping auto-reply for non-text message"
2. No matching rule found → Check logs for "No matching rule found for message"
3. SQS queue issue → Check outgoing-messages queue in AWS
4. Business hours blocking → Check if after-hours rule is matching during business hours

**Solution**:
- Check App Runner logs for specific error messages
- Verify rule patterns match expected keywords
- Test with simple messages like "Hi" or "STOP"

---

**Issue**: STOP command not unsubscribing user

**Possible Causes**:
1. Database connection issue
2. User not found in database
3. Regex pattern not matching

**Solution**:
- Check logs for "✅ User [phone] unsubscribed"
- Verify database connection
- Test with exact keywords: "stop", "STOP", " stop "

---

**Issue**: User receiving messages after unsubscribing

**Possible Causes**:
1. Marketing campaigns not checking subscription
2. Automated replies are always sent (expected behavior)

**Solution**:
- Verify `check_subscription=True` in template sending code
- Remember: Automated replies work regardless of subscription status

---

## Performance Considerations

### Processing Time

- Typical automated reply processing: 50-200ms
- Rule matching: O(n) where n = number of active rules
- Database updates: ~50ms for subscription changes

### Optimization Tips

1. **Reduce Active Rules**: Disable unused rules
2. **Optimize Regex**: Use simpler patterns when possible
3. **Cache User Context**: Minimize database queries
4. **Priority Ordering**: Place most common matches at higher priority

### Scalability

- Current system handles: ~100 messages/second
- SQS queue ensures no message loss
- Multiple workers can process in parallel
- Database connection pooling prevents bottlenecks

---

## Important Notes

1. **Automated replies ALWAYS work**, regardless of subscription status
2. **Template messages RESPECT subscription status** (STOP/START)
3. **Business hours checking** only affects the after-hours message, not other rules
4. **STOP and START** commands have HIGHEST priority (20)
5. **All automated replies** go through SQS queue for reliability
6. **Status tracking** works for automated replies (sent → delivered → read)

---

## Related Files

### Core Files
- `backend/app/services/reply_automation.py` - Main automation engine
- `backend/app/services/whatsapp_service.py` - Message processing orchestration
- `backend/app/services/messaging_service.py` - High-level messaging functions
- `backend/app/services/sqs_service.py` - SQS queue operations

### Repository Files
- `backend/app/repositories/user_repository.py` - User subscription management
- `backend/app/repositories/message_repository.py` - Message storage

### Model Files
- `backend/app/models/user.py` - UserProfile model
- `backend/app/models/whatsapp.py` - WhatsAppMessage model
- `backend/app/models/business.py` - BusinessMetrics model

---

## Summary

The automated replies system is a powerful, rule-based message processing engine that:

✅ Provides instant responses to common queries
✅ Manages user subscriptions (STOP/START)
✅ Respects business hours for after-hours messages
✅ Always responds to customer service queries
✅ Integrates seamlessly with marketing campaigns
✅ Scales reliably using SQS queues
✅ Tracks all message statuses

It operates 24/7, ensuring customers always receive timely responses while respecting their subscription preferences for marketing content.
