# Automated Replies System - Complete Guide

## 📋 Overview

The automated replies system in your WhatsApp application provides intelligent, rule-based automatic responses to incoming messages. It helps handle common customer queries 24/7 without human intervention.

## 🏗️ Architecture

### Key Components

1. **Reply Automation Engine** (`backend/app/services/reply_automation.py`)
   - Core logic for matching messages with rules
   - Priority-based rule selection
   - Business hours checking
   - STOP/START command handling

2. **WhatsApp Service** (`backend/app/services/whatsapp_service.py`)
   - Integrates automated replies into message processing
   - Manages database operations for messages
   - Coordinates with user profiles

3. **Message Processor** (`backend/app/workers/message_processor.py`)
   - Background worker that processes incoming messages from SQS
   - Handles race conditions with DynamoDB
   - Triggers automated reply logic

## 🔄 How It Works

### Message Flow

```
1. User sends message to WhatsApp Business
   ↓
2. WhatsApp webhook → Your API endpoint (/webhook)
   ↓
3. Message stored in database (whatsapp_messages table)
   ↓
4. Message queued in SQS (incoming-messages queue)
   ↓
5. Message Processor picks up message from SQS
   ↓
6. WhatsApp Service processes the text message
   ↓
7. Reply Automation Engine analyzes message
   ↓
8. Matching rule found based on priority
   ↓
9. Automated reply queued in SQS (outgoing-messages queue)
   ↓
10. Outgoing message processor sends reply via WhatsApp API
```

### Detailed Processing Steps

#### Step 1: Message Reception
- **File**: `backend/app/api/webhook.py`
- WhatsApp sends a POST request to your `/webhook` endpoint
- Message is stored in `whatsapp_messages` table
- Message is queued in SQS `incoming-messages` queue

#### Step 2: Message Processing
- **File**: `backend/app/workers/message_processor.py`
- Background worker polls SQS for new messages
- Uses DynamoDB for atomic message claiming (prevents race conditions)
- Creates fresh database session for each message

#### Step 3: Text Message Handling
- **File**: `backend/app/services/whatsapp_service.py` → `process_text_message()`
- Stores message in database
- Updates user profile (last interaction time)
- Updates analytics
- Calls automated reply processing

#### Step 4: Rule Matching
- **File**: `backend/app/services/reply_automation.py` → `process_incoming_message()`
- Message text is normalized (lowercase, trimmed)
- All active rules are checked for matches
- Highest priority matching rule is selected

#### Step 5: Reply Generation
- **File**: `backend/app/services/reply_automation.py` → `_send_automated_reply()`
- Reply data is prepared from the matched rule
- Metadata is added (rule name, automation flag, timestamp)
- Reply is queued in SQS `outgoing-messages` queue

#### Step 6: Reply Sending
- Outgoing message processor picks up the reply
- Sends via WhatsApp Business API
- Updates message status in database
- Updates campaign recipient status if applicable

## 📜 Rule System

### Rule Structure

Each rule has:
- **name**: Unique identifier for the rule
- **condition**: Regex pattern to match against message text
- **reply_type**: Type of reply (text, template, document, location)
- **reply_data**: The actual reply content
- **priority**: Higher numbers = higher priority (0-20)
- **active**: Boolean to enable/disable the rule

### Rule Priority Levels

- **Priority 20**: STOP/START commands (highest - always processed first)
- **Priority 10**: Greetings (hi, hello, good morning)
- **Priority 8**: FAQ about business hours
- **Priority 7**: FAQ about pricing, support
- **Priority 6**: Contact information requests
- **Priority 1**: Business hours closed message
- **Priority 0**: Fallback/unknown messages (lowest)

### Default Rules

#### 1. STOP/START Commands (Priority 20)

**STOP Command:**
- **Trigger**: `stop`, `unsubscribe`, `opt out`, `optout`, `cancel`
- **Action**: Unsubscribes user from template messages (marketing campaigns)
- **Reply**: "✅ You have been unsubscribed from promotional messages..."
- **Database Update**: Sets `subscription = 'unsubscribed'` in `user_profiles` table
- **Note**: User can still receive automated replies to their messages

**START Command:**
- **Trigger**: `start`, `subscribe`, `opt in`, `optin`, `resume`
- **Action**: Resubscribes user to template messages
- **Reply**: "✅ Welcome back! You are now subscribed..."
- **Database Update**: Sets `subscription = 'subscribed'` in `user_profiles` table

#### 2. Greeting Rules (Priority 10)

**Hi/Hello:**
- **Trigger**: Contains `hi`, `hello`, `hey`, `greetings`
- **Reply**: "Hello! 👋 Welcome to our WhatsApp Business. How can I help you today?"

**Good Morning:**
- **Trigger**: Contains `good morning` or `morning`
- **Reply**: "Good morning! ☀️ Hope you're having a great day. How can I assist you?"

#### 3. Business Hours (Priority 8)

**Hours Inquiry:**
- **Trigger**: Contains `hours`, `open`, `close`, `timing`, `schedule`
- **Reply**: Detailed business hours (Monday-Friday: 9:00 AM - 5:00 PM)

#### 4. FAQ Rules (Priority 7)

**Pricing:**
- **Trigger**: Contains `price`, `cost`, `rate`, `pricing`, `how much`, `fee`
- **Reply**: "Great question about our pricing! 💰 Let me send you our detailed pricing information..."

**Support:**
- **Trigger**: Contains `support`, `help`, `issue`, `problem`, `bug`, `error`
- **Reply**: "I'm here to help! 🛠️ Could you please describe the specific issue..."

#### 5. Contact Info (Priority 6)

**Contact Request:**
- **Trigger**: Contains `contact`, `phone`, `email`, `address`, `location`
- **Reply**: Complete contact information with phone, email, and address

#### 6. Business Hours Closed (Priority 1)

**After Hours:**
- **Trigger**: `*` (matches any message)
- **Condition**: Only sent outside business hours (Mon-Fri 9 AM - 5 PM)
- **Reply**: "Thank you for contacting us! 🕒 Our business hours are 9 AM - 5 PM..."

#### 7. Fallback (Priority 0)

**Unknown Message:**
- **Trigger**: `*` (matches any message if no other rule matches)
- **Reply**: "Thank you for your message! 😊 I'll make sure our team reviews this..."

## 🕒 Business Hours Configuration

### Current Settings
- **Start Time**: 9:00 AM
- **End Time**: 5:00 PM
- **Weekdays Only**: Yes (Monday-Friday)
- **Timezone**: UTC (adjust in your deployment)

### Customization

You can update business hours programmatically:

```python
from app.services.reply_automation import reply_automation
from datetime import time

# Update to 8 AM - 6 PM, weekdays only
reply_automation.update_business_hours(
    start_time=time(8, 0),
    end_time=time(18, 0),
    weekdays_only=True
)
```

## 🔒 Subscription Management

### How STOP/START Works

1. **User sends "STOP"**
   - Message matched to `unsubscribe_stop` rule
   - `user_repository.unsubscribe_user()` is called
   - Database updates: `subscription = 'unsubscribed'`
   - Confirmation message sent: "You have been unsubscribed..."
   - User will NOT receive marketing campaign messages
   - User WILL still receive automated replies to their messages

2. **User sends "START"**
   - Message matched to `resubscribe_start` rule
   - `user_repository.resubscribe_user()` is called
   - Database updates: `subscription = 'subscribed'`
   - Confirmation message sent: "Welcome back! You are now subscribed..."
   - User will receive marketing campaign messages again

### Database Schema

**Table**: `user_profiles`

```sql
subscription VARCHAR(20) DEFAULT 'subscribed'
-- Values: 'subscribed' or 'unsubscribed'
```

### Important Distinction

- **Unsubscribed from templates**: User won't receive marketing campaigns
- **Automated replies**: ALWAYS work regardless of subscription status
- This ensures customer service functionality remains available

## 🎯 Adding Custom Rules

### Method 1: In Code

Edit `backend/app/services/reply_automation.py`:

```python
def _setup_default_rules(self):
    # ... existing rules ...
    
    # Add your custom rule
    self.rules.append(
        ReplyRule(
            name="custom_shipping",
            condition=r"\b(shipping|delivery|ship|deliver)\b",
            reply_type="text",
            reply_data={
                "type": "text",
                "content": "🚚 We offer free shipping on orders over $50! Standard delivery takes 3-5 business days."
            },
            priority=7
        )
    )
```

### Method 2: Programmatically at Runtime

```python
from app.services.reply_automation import reply_automation, ReplyRule

# Add a new rule
custom_rule = ReplyRule(
    name="custom_refund",
    condition=r"\b(refund|return|money back)\b",
    reply_type="text",
    reply_data={
        "type": "text",
        "content": "We offer 30-day money-back guarantee! Contact support to initiate a refund."
    },
    priority=8
)

reply_automation.add_custom_rule(custom_rule)
```

### Method 3: Remove a Rule

```python
from app.services.reply_automation import reply_automation

# Remove a rule by name
reply_automation.remove_rule("faq_pricing")
```

## 📊 Database Tables Involved

### 1. whatsapp_messages
- **Purpose**: Stores all WhatsApp messages (incoming and outgoing)
- **Columns Used**:
  - `message_id`: Unique WhatsApp message ID
  - `from_phone`: Sender's phone number
  - `to_phone`: Recipient's phone number
  - `message_type`: Type of message (text, image, etc.)
  - `content`: Message content/text
  - `direction`: 'incoming' or 'outgoing'
  - `status`: Message status (sent, delivered, read, failed)
  - `timestamp`: When message was received/sent
  - `sent_at`, `delivered_at`, `read_at`: Status timestamps
  - `failure_reason`: Error message if failed

### 2. user_profiles
- **Purpose**: Stores user information and preferences
- **Columns Used**:
  - `id`: Unique user ID (UUID)
  - `phone_number`: User's WhatsApp number (unique)
  - `display_name`: User's name from WhatsApp
  - `subscription`: 'subscribed' or 'unsubscribed' (for template messages)
  - `last_interaction_at`: Last message timestamp
  - `customer_tier`: User tier (bronze, silver, gold, platinum)
  - `city`: User's city
  - `tags`: Array of tags for user segmentation

### 3. business_metrics
- **Purpose**: Daily analytics and metrics
- **Columns Updated**:
  - `total_messages_received`: Count of incoming messages
  - `total_responses_sent`: Count of outgoing messages (including automated)
  - `unique_users`: Count of unique users who messaged
  - `response_time_avg_seconds`: Average response time

## 🔍 Logging and Monitoring

### Log Messages

**Message Reception:**
```
📥 Received 1 messages for processing
🔄 Processing message: wamid.xxx (type: text, from: 91782...)
```

**Rule Matching:**
```
🤖 Automated reply queued for 917829844548: wamid.xxx
✅ Auto-reply sent to 917829844548 using rule 'greeting_hi': wamid.xxx
```

**Subscription Changes:**
```
📵 User 917829844548 sent STOP - unsubscribed from templates
✅ User 917829844548 resubscribed from template messages
```

**Errors:**
```
❌ Error processing auto-reply for 917829844548: [error details]
No matching rule found for message: 'random text...'
```

### Monitoring Locations

1. **AWS CloudWatch Logs**
   - App Runner logs show real-time processing
   - Search for "Auto-reply" or "🤖" emoji

2. **Database Queries**
   ```sql
   -- Check automated reply messages
   SELECT * FROM whatsapp_messages 
   WHERE direction = 'outgoing' 
   AND content LIKE '%👋%' 
   ORDER BY timestamp DESC;
   
   -- Check subscription status
   SELECT phone_number, subscription, last_interaction_at 
   FROM user_profiles 
   WHERE subscription = 'unsubscribed';
   ```

## 🐛 Troubleshooting

### Issue 1: Automated Replies Not Sending

**Symptoms**: User sends message but no automated reply

**Checks**:
1. Verify message reached webhook: Check app logs for "📥 Received"
2. Check if rule matched: Look for "No matching rule found"
3. Verify SQS queue: Check `incoming-messages` and `outgoing-messages` queues
4. Check message processor: Ensure worker is running

**Solution**:
```bash
# Check app logs
aws logs tail /aws/apprunner/YOUR_SERVICE_NAME --follow

# Check SQS queues
aws sqs get-queue-attributes --queue-url YOUR_QUEUE_URL --attribute-names All
```

### Issue 2: Delayed Replies

**Symptoms**: Reply sent but after several minutes

**Cause**: Message processor polling interval or SQS visibility timeout

**Solution**:
- Message processor uses 20-second long polling
- Expected delay: 0-20 seconds for first message
- If longer, check worker logs for errors

### Issue 3: Duplicate Replies

**Symptoms**: User receives same reply multiple times

**Cause**: Multiple message processors handling same message

**Solution**:
- System uses DynamoDB for atomic message claiming
- Check DynamoDB table for message status
- Verify only one message processor instance is running

### Issue 4: STOP Command Not Working

**Symptoms**: User sends STOP but still receives campaign messages

**Checks**:
1. Check user_profiles table: `SELECT subscription FROM user_profiles WHERE phone_number = '...'`
2. Check logs for "📵 User ... unsubscribed"
3. Verify campaign filtering logic

**Solution**:
```python
# Manually unsubscribe user
from app.repositories.user_repository import UserRepository
from app.core.database import get_db_session

with get_db_session() as db:
    user_repo = UserRepository(db)
    user_repo.unsubscribe_user("917829844548")
```

### Issue 5: Business Hours Not Working

**Symptoms**: After-hours message sent during business hours

**Checks**:
1. Verify server timezone: `datetime.now()` should match expected timezone
2. Check business hours configuration
3. Verify rule priority (business_hours_closed has priority 1)

**Solution**:
```python
# Check current configuration
from app.services.reply_automation import reply_automation

print(f"Start: {reply_automation.business_hours.start_time}")
print(f"End: {reply_automation.business_hours.end_time}")
print(f"Weekdays only: {reply_automation.business_hours.weekdays_only}")
print(f"Is business hours now: {reply_automation.business_hours.is_business_hours()}")
```

## 🔐 Security Considerations

1. **Rate Limiting**: Consider adding rate limiting to prevent abuse
2. **Message Validation**: Always validate message content before processing
3. **User Privacy**: Don't log sensitive user information
4. **API Security**: Webhook endpoint should verify WhatsApp signature

## 📈 Performance Optimization

### Current Configuration
- **SQS Long Polling**: 20 seconds (reduces API calls)
- **Batch Processing**: Up to 10 messages concurrently
- **Visibility Timeout**: 900 seconds (15 minutes)
- **DynamoDB**: Atomic operations prevent race conditions

### Scaling Considerations
- **Horizontal Scaling**: Run multiple message processor instances
- **Queue Monitoring**: Alert when queue depth exceeds threshold
- **Database Connection Pooling**: Configured in database settings

## 🎓 Best Practices

1. **Rule Design**
   - Keep regex patterns simple and efficient
   - Use higher priority for more specific rules
   - Test rules thoroughly with edge cases

2. **Reply Content**
   - Keep messages concise and helpful
   - Use emojis sparingly for readability
   - Provide clear next steps or call-to-action

3. **Monitoring**
   - Regularly review logs for "No matching rule found"
   - Track automated reply success rate
   - Monitor user feedback on automated responses

4. **Testing**
   - Test all rules in development environment
   - Verify STOP/START commands work correctly
   - Test business hours logic across timezones

5. **Maintenance**
   - Regularly update FAQ responses
   - Keep contact information current
   - Archive or remove outdated rules

## 📚 Related Documentation

- **Campaigns Guide**: `CAMPAIGN_SETUP_GUIDE.md`
- **Database Schema**: Check migration files in `backend/migrations/`
- **API Documentation**: `backend/app/api/README.md` (if exists)
- **WhatsApp Business API**: https://developers.facebook.com/docs/whatsapp/business-platform

## 🆘 Support

For issues or questions:
1. Check application logs in CloudWatch
2. Review database for message and user records
3. Test rules manually using Python REPL
4. Contact development team with specific error messages

---

**Last Updated**: January 2, 2026
**Version**: 1.0
