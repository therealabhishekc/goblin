# Campaign Recipients Table - Complete Fix

## Problem Analysis

The `campaign_recipients` table was not properly tracking message delivery status. Messages were being sent, but the status tracking was incomplete, causing issues with:
1. Messages showing as "queued" instead of "sent"
2. Delivered/read status not being updated
3. Timestamps not being properly filled

## Table Structure

The `campaign_recipients` table has these key columns:

```sql
CREATE TABLE campaign_recipients (
    id UUID PRIMARY KEY,
    campaign_id UUID REFERENCES marketing_campaigns(id),
    phone_number VARCHAR(20) NOT NULL,
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending',  -- pending → sent → delivered → read
    whatsapp_message_id VARCHAR(100),
    
    -- Timestamps for message lifecycle
    scheduled_send_date DATE,
    sent_at TIMESTAMP,          -- When we sent the message
    delivered_at TIMESTAMP,     -- When WhatsApp delivered it
    read_at TIMESTAMP,          -- When recipient read it
    failed_at TIMESTAMP,        -- If failed
    
    -- Error handling
    failure_reason TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Personalization
    template_parameters JSONB,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## What Was Fixed

### 1. **Status Flow** (marketing_service.py)
Changed from `QUEUED` to `SENT` when message is successfully sent:

```python
# BEFORE:
repo.update_recipient_status(
    recipient.id,
    RecipientStatus.QUEUED,  # ❌ Wrong - message is actually sent
    whatsapp_message_id=message_id
)

# AFTER:
repo.update_recipient_status(
    recipient.id,
    RecipientStatus.SENT,  # ✅ Correct - message was sent
    whatsapp_message_id=message_id
)
```

### 2. **Webhook Status Updates** (webhook.py)
Added handling for WhatsApp status updates (delivered, read):

```python
# Extract status updates from webhook
statuses = value.get("statuses", [])

# Process each status update
for status_update in statuses:
    result = await process_status_update(
        status_update=status_update,
        webhook_id=webhook_id
    )
```

New function `process_status_update()` that:
- Receives status updates from WhatsApp (sent, delivered, read, failed)
- Finds the campaign recipient by `whatsapp_message_id`
- Updates the status and timestamps in `campaign_recipients`

### 3. **Enhanced Repository** (marketing_repository.py)
Improved `update_recipient_status()` to handle all status types:

```python
def update_recipient_status(self, recipient_id, status, whatsapp_message_id, failure_reason):
    if status == RecipientStatus.QUEUED:
        recipient.whatsapp_message_id = whatsapp_message_id
    
    elif status == RecipientStatus.SENT:
        recipient.sent_at = datetime.utcnow()
        recipient.whatsapp_message_id = whatsapp_message_id
    
    elif status == RecipientStatus.DELIVERED:
        recipient.delivered_at = datetime.utcnow()
        # Backfill sent_at if missing
        if not recipient.sent_at:
            recipient.sent_at = datetime.utcnow()
    
    elif status == RecipientStatus.READ:
        recipient.read_at = datetime.utcnow()
        # Backfill delivered_at and sent_at if missing
        if not recipient.delivered_at:
            recipient.delivered_at = datetime.utcnow()
        if not recipient.sent_at:
            recipient.sent_at = datetime.utcnow()
    
    elif status == RecipientStatus.FAILED:
        recipient.failed_at = datetime.utcnow()
        recipient.failure_reason = failure_reason
        recipient.retry_count += 1
    
    elif status == RecipientStatus.SKIPPED:
        recipient.failure_reason = failure_reason
```

## Status Lifecycle

The complete message lifecycle now works as follows:

```
1. PENDING      → Recipient added to campaign, waiting to be scheduled
2. SENT         → Message sent to WhatsApp API successfully
3. DELIVERED    → WhatsApp delivered message to recipient's phone
4. READ         → Recipient opened and read the message
```

Alternative paths:
```
PENDING → FAILED    → Sending failed (e.g., API error)
PENDING → SKIPPED   → User unsubscribed, recipient skipped
```

## How Data Flows

### When Campaign Messages Are Sent (Daily Processor)

1. **GET** pending recipients for today from `campaign_recipients`
2. **CHECK** if user is subscribed
3. **SEND** message via WhatsApp API
4. **UPDATE** status to `SENT` with:
   - `status = 'sent'`
   - `sent_at = current_timestamp`
   - `whatsapp_message_id = <id_from_whatsapp>`

### When WhatsApp Sends Status Updates (Webhook)

1. **RECEIVE** webhook with status update:
   ```json
   {
     "statuses": [{
       "id": "wamid.xxx",
       "status": "delivered",
       "timestamp": "1234567890"
     }]
   }
   ```

2. **FIND** recipient by `whatsapp_message_id`

3. **UPDATE** status:
   - For "delivered": Set `delivered_at`, status = 'delivered'
   - For "read": Set `read_at`, status = 'read'
   - For "failed": Set `failed_at`, status = 'failed', increment retry_count

## All Columns Are Now Properly Filled

✅ **id** - Auto-generated UUID  
✅ **campaign_id** - Set when recipient is added  
✅ **phone_number** - Set when recipient is added  
✅ **status** - Updated through lifecycle (pending → sent → delivered → read)  
✅ **whatsapp_message_id** - Set when message is sent  
✅ **scheduled_send_date** - Set when campaign is activated  
✅ **sent_at** - Set when status becomes SENT  
✅ **delivered_at** - Set when WhatsApp confirms delivery  
✅ **read_at** - Set when recipient reads message  
✅ **failed_at** - Set if sending fails  
✅ **failure_reason** - Set if sending fails or user is skipped  
✅ **retry_count** - Incremented on failures  
✅ **max_retries** - Default value of 3  
✅ **template_parameters** - Set when recipient is added (if provided)  
✅ **created_at** - Auto-set on creation  
✅ **updated_at** - Auto-updated by trigger  

## Testing the Fix

### 1. Create a test campaign
```bash
curl -X POST http://your-api/api/marketing/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Campaign",
    "template_name": "your_template",
    "language_code": "en_US",
    "daily_send_limit": 250
  }'
```

### 2. Add recipients
```bash
curl -X POST http://your-api/api/marketing/campaigns/{campaign_id}/recipients \
  -H "Content-Type: application/json" \
  -d '{
    "phone_numbers": ["14694652751", "19453083188"]
  }'
```

### 3. Activate campaign
```bash
curl -X POST http://your-api/api/marketing/campaigns/{campaign_id}/activate
```

### 4. Process daily (send messages)
```bash
curl -X POST http://your-api/api/marketing/process-daily
```

### 5. Check database
```sql
SELECT 
    phone_number,
    status,
    whatsapp_message_id,
    sent_at,
    delivered_at,
    read_at,
    failure_reason
FROM campaign_recipients
WHERE campaign_id = '{your_campaign_id}'
ORDER BY created_at;
```

Expected results:
- `status` should be 'sent' (not 'queued')
- `whatsapp_message_id` should be filled
- `sent_at` should have a timestamp
- `delivered_at` and `read_at` will be filled when WhatsApp sends status updates

## Monitoring Campaign Progress

Use the campaign stats endpoint:
```bash
curl http://your-api/api/marketing/campaigns/{campaign_id}/stats
```

Response:
```json
{
  "campaign_id": "xxx",
  "campaign_name": "Test Campaign",
  "status": "active",
  "total_target": 100,
  "sent": 50,
  "delivered": 45,
  "read": 30,
  "failed": 5,
  "pending": 50,
  "progress_percentage": 50.0,
  "delivery_rate": 90.0,
  "read_rate": 60.0
}
```

## Summary

All columns in `campaign_recipients` are now properly filled:
- ✅ Status tracking works correctly (pending → sent → delivered → read)
- ✅ All timestamps are recorded (sent_at, delivered_at, read_at)
- ✅ WhatsApp message IDs are stored for tracking
- ✅ Webhook status updates properly update the table
- ✅ Failed messages are tracked with reasons
- ✅ Campaign statistics reflect real-time progress

The fix ensures complete visibility into campaign message delivery and recipient engagement.
