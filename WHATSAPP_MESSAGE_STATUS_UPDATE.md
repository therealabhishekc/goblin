# WhatsApp Message Status Tracking

## Overview
The `whatsapp_messages` table now tracks message delivery status in real-time through WhatsApp webhook status updates.

## Status Flow

### Outgoing Messages (sent by business)
1. **sent** - Initial status when message is sent via WhatsApp API
2. **delivered** - Updated when WhatsApp delivers to recipient's device
3. **read** - Updated when recipient reads the message
4. **failed** - Updated if message delivery fails

### Incoming Messages (received from users)
1. **processing** - Initial status when message is received
2. **received** - Can be set for completed processing

## Implementation

### Database Schema
- **Table**: `whatsapp_messages`
- **Column**: `status` (String(20))
- **Valid Values**: sent, delivered, read, failed, processing, received

### Webhook Processing
When WhatsApp sends status updates via webhook, the `process_status_update()` function in `backend/app/api/webhook.py` handles:

1. **Campaign Messages**: Updates `campaign_recipients` table with delivery/read timestamps
2. **All Messages**: Updates `whatsapp_messages` table with current status

### Code Changes
**File**: `backend/app/api/webhook.py`
**Function**: `process_status_update()`

The function now:
- Queries both `campaign_recipients` and `whatsapp_messages` tables
- Updates campaign recipient status if message is part of a marketing campaign
- Updates message status in whatsapp_messages table for all messages
- Logs both updates for monitoring

## Testing

### Check Status Updates
```sql
-- View recent message status changes
SELECT 
    message_id,
    to_phone,
    message_type,
    status,
    timestamp,
    content
FROM whatsapp_messages
WHERE direction = 'outgoing'
ORDER BY timestamp DESC
LIMIT 10;
```

### Monitor Status Distribution
```sql
-- Count messages by status
SELECT 
    status,
    COUNT(*) as count,
    message_type
FROM whatsapp_messages
WHERE direction = 'outgoing'
GROUP BY status, message_type
ORDER BY count DESC;
```

## Benefits

1. **Accurate Tracking**: Know exactly which messages were delivered and read
2. **Campaign Analytics**: Better insights into campaign message engagement
3. **Debugging**: Quickly identify failed message deliveries
4. **Unified Updates**: Both campaign and non-campaign messages tracked consistently

## Related Tables

- **whatsapp_messages**: Stores all WhatsApp messages with status
- **campaign_recipients**: Stores campaign-specific recipient data with detailed timestamps
  - `sent_at`: When message was sent
  - `delivered_at`: When message was delivered
  - `read_at`: When message was read
  - `status`: Current recipient status (PENDING, SENT, DELIVERED, READ, FAILED)

## Notes

- Status updates arrive via WhatsApp webhooks asynchronously
- Messages may receive multiple status updates (sent → delivered → read)
- Failed messages will have status = "failed"
- Campaign messages get dual tracking (whatsapp_messages + campaign_recipients)
