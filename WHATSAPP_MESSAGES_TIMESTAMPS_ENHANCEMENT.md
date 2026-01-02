# WhatsApp Messages Table - Status Timestamps Enhancement

## Summary

Added status timestamp columns to the `whatsapp_messages` table to track message lifecycle events, similar to the `campaign_recipients` table structure.

## Changes Made

### 1. Database Schema Changes

Added the following columns to `whatsapp_messages` table:

| Column Name | Type | Description |
|------------|------|-------------|
| `sent_at` | TIMESTAMP | When the message was sent (status: sent) |
| `delivered_at` | TIMESTAMP | When the message was delivered to recipient |
| `read_at` | TIMESTAMP | When the message was read by recipient |
| `failed_at` | TIMESTAMP | When the message failed to send |
| `failed_reason` | TEXT | Reason for message failure |

**Indexes created:**
- `idx_whatsapp_messages_sent_at`
- `idx_whatsapp_messages_delivered_at`
- `idx_whatsapp_messages_read_at`
- `idx_whatsapp_messages_failed_at`

### 2. Model Updates

**File:** `backend/app/models/whatsapp.py`

Updated `WhatsAppMessageDB` class to include the new columns:
```python
# Status timestamps (similar to campaign_recipients)
sent_at = Column(DateTime)
delivered_at = Column(DateTime)
read_at = Column(DateTime)
failed_at = Column(DateTime)

# Failure tracking
failed_reason = Column(Text)
```

### 3. Webhook Handler Updates

**File:** `backend/app/api/webhook.py`

Enhanced `process_status_update()` function to populate timestamp columns when status updates are received:

- **sent**: Sets `sent_at` timestamp
- **delivered**: Sets `delivered_at` timestamp  
- **read**: Sets `read_at` timestamp
- **failed**: Sets `failed_at` timestamp and `failed_reason`

**Status Hierarchy:** Prevents status downgrades (e.g., if status is already "read", won't downgrade to "delivered" even if webhook arrives late)

```python
status_hierarchy = {
    "sent": 1,
    "delivered": 2,
    "read": 3,
    "failed": 99  # Failed is always updated
}
```

### 4. Outgoing Message Processor Updates

**File:** `backend/app/workers/outgoing_processor.py`

Updated message storage to set `sent_at` timestamp when creating outgoing messages:

```python
now = datetime.utcnow()
message_data = {
    ...
    "status": "sent",
    "sent_at": now  # Set sent_at timestamp
}
```

## How It Works

### Message Flow

1. **Message Created (Outgoing)**
   - Status: `sent`
   - `sent_at` timestamp set
   - Stored in database

2. **WhatsApp Webhook: Delivered Status**
   - Status updated: `delivered`
   - `delivered_at` timestamp set
   - Both `campaign_recipients` and `whatsapp_messages` updated

3. **WhatsApp Webhook: Read Status**
   - Status updated: `read`
   - `read_at` timestamp set
   - Won't downgrade even if "delivered" webhook arrives later

4. **WhatsApp Webhook: Failed Status**
   - Status updated: `failed`
   - `failed_at` timestamp set
   - `failed_reason` populated with error details

### Failure Reason Format

When a message fails, WhatsApp provides error details that are stored in `failed_reason`:

```
Error {code}: {title} - {message} ({details})
```

Example:
```
Error 131026: Message Undeliverable - This message was not delivered to maintain healthy ecosystem engagement
```

## Migration

### Local Database

Migration already applied to local database.

### AWS RDS

To apply migration to production RDS:

```bash
cd /Users/abskchsk/Documents/govindjis/wa-app
export DATABASE_URL="postgresql://username:password@your-rds-endpoint:5432/dbname"
./backend/migrations/run_migration_on_rds.sh
```

Or manually:
```bash
psql "$DATABASE_URL" -f backend/migrations/add_whatsapp_messages_timestamps.sql
```

## Benefits

1. **Consistent Schema**: Both `whatsapp_messages` and `campaign_recipients` now have similar timestamp tracking
2. **Message Analytics**: Can now calculate delivery rates, read rates, and timing analytics
3. **Failure Tracking**: Better understanding of why messages fail
4. **Status History**: Preserves timestamp for each status transition
5. **Performance**: Indexed timestamp columns for efficient querying

## Query Examples

### Get messages with delivery metrics
```sql
SELECT 
    message_id,
    status,
    sent_at,
    delivered_at,
    read_at,
    EXTRACT(EPOCH FROM (delivered_at - sent_at)) as delivery_time_seconds,
    EXTRACT(EPOCH FROM (read_at - delivered_at)) as read_time_seconds
FROM whatsapp_messages
WHERE direction = 'outgoing'
  AND sent_at IS NOT NULL;
```

### Get failed messages with reasons
```sql
SELECT 
    message_id,
    to_phone,
    failed_at,
    failed_reason
FROM whatsapp_messages
WHERE status = 'failed'
ORDER BY failed_at DESC;
```

### Calculate delivery rate
```sql
SELECT 
    COUNT(*) as total_sent,
    COUNT(delivered_at) as delivered,
    COUNT(read_at) as read,
    COUNT(failed_at) as failed,
    ROUND(100.0 * COUNT(delivered_at) / COUNT(*), 2) as delivery_rate,
    ROUND(100.0 * COUNT(read_at) / COUNT(*), 2) as read_rate
FROM whatsapp_messages
WHERE direction = 'outgoing'
  AND sent_at IS NOT NULL;
```

## Testing

To verify the changes are working:

1. Send a message through the campaign system
2. Check that `sent_at` is populated in `whatsapp_messages`
3. Wait for WhatsApp webhooks for delivery/read status
4. Verify timestamps are updated correctly
5. Check App Runner logs for status update confirmations

## Files Changed

1. `backend/app/models/whatsapp.py` - Added columns to model
2. `backend/app/api/webhook.py` - Enhanced status update handler
3. `backend/app/workers/outgoing_processor.py` - Set sent_at on message creation
4. `backend/migrations/add_whatsapp_messages_timestamps.sql` - Database migration
5. `backend/migrations/run_migration_on_rds.sh` - RDS migration script

## Next Steps

1. Run migration on AWS RDS production database
2. Monitor logs to ensure timestamps are being populated correctly
3. Consider creating analytics queries using the new timestamp data
4. Update any existing reports/dashboards to use the new columns
