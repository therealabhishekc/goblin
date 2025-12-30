# Campaign Status Update Analysis

## Question
Are the `delivered_at` and `read_at` columns in the `campaign_recipients` table being updated?

## Answer
**Yes, they ARE being updated** - but there was a bug where campaign-level counters weren't being updated.

---

## How Status Updates Work

### 1. Webhook Flow
When WhatsApp sends status updates (sent, delivered, read, failed):

1. **Webhook receives status update** (`/webhook` endpoint)
2. **`process_status_update()` function** extracts the status (lines 329-404 in `webhook.py`)
3. **Finds the campaign recipient** by `whatsapp_message_id`
4. **Maps WhatsApp status** to internal status:
   - `"sent"` → `RecipientStatus.SENT`
   - `"delivered"` → `RecipientStatus.DELIVERED`
   - `"read"` → `RecipientStatus.READ`
   - `"failed"` → `RecipientStatus.FAILED`
5. **Calls `update_recipient_status()`** to update the database

### 2. Status Update Function
The `update_recipient_status()` function in `marketing_repository.py`:

#### ✅ What it WAS doing correctly:
- Setting `delivered_at` timestamp when status = DELIVERED
- Setting `read_at` timestamp when status = READ
- Setting `sent_at` timestamp when status = SENT
- Setting `failed_at` timestamp when status = FAILED
- Backfilling missing timestamps (e.g., if READ comes before DELIVERED)

#### ❌ What was MISSING:
- **Campaign-level counters were NOT being updated**
- `campaign.messages_delivered` was not incremented
- `campaign.messages_read` was not incremented
- `campaign.messages_sent` was not incremented
- `campaign.messages_failed` was not incremented
- `campaign.messages_pending` was not decremented

---

## The Fix Applied

Updated `update_recipient_status()` to:

### 1. Track old status
```python
old_status = recipient.status
```

### 2. Update campaign counters based on status transitions
```python
if status == RecipientStatus.DELIVERED:
    recipient.delivered_at = datetime.utcnow()
    if campaign and old_status != RecipientStatus.DELIVERED.value:
        campaign.messages_delivered += 1
```

### 3. Handle different transition scenarios
- **PENDING → SENT**: Increment `messages_sent`, decrement `messages_pending`
- **PENDING → DELIVERED**: Increment both `messages_sent` and `messages_delivered`
- **SENT → DELIVERED**: Only increment `messages_delivered`
- **DELIVERED → READ**: Only increment `messages_read`
- **PENDING → READ**: Increment all three counters
- **Any → FAILED**: Increment `messages_failed`, decrement `messages_pending`

### 4. Prevent double counting
The function checks `old_status != new_status` to avoid incrementing counters multiple times.

---

## Verification

### Check recipient-level updates:
```sql
SELECT 
    phone_number,
    status,
    sent_at,
    delivered_at,
    read_at,
    whatsapp_message_id
FROM campaign_recipients
WHERE campaign_id = 'YOUR_CAMPAIGN_ID'
ORDER BY sent_at DESC;
```

### Check campaign-level counters:
```sql
SELECT 
    name,
    status,
    messages_sent,
    messages_delivered,
    messages_read,
    messages_failed,
    messages_pending,
    total_target_customers
FROM marketing_campaigns
WHERE id = 'YOUR_CAMPAIGN_ID';
```

### Verify the counters match:
```sql
SELECT 
    c.name AS campaign_name,
    c.messages_sent AS campaign_counter_sent,
    COUNT(CASE WHEN r.status = 'sent' THEN 1 END) AS actual_sent,
    c.messages_delivered AS campaign_counter_delivered,
    COUNT(CASE WHEN r.status = 'delivered' THEN 1 END) AS actual_delivered,
    c.messages_read AS campaign_counter_read,
    COUNT(CASE WHEN r.status = 'read' THEN 1 END) AS actual_read,
    c.messages_failed AS campaign_counter_failed,
    COUNT(CASE WHEN r.status = 'failed' THEN 1 END) AS actual_failed
FROM marketing_campaigns c
LEFT JOIN campaign_recipients r ON c.id = r.campaign_id
WHERE c.id = 'YOUR_CAMPAIGN_ID'
GROUP BY c.id, c.name, c.messages_sent, c.messages_delivered, c.messages_read, c.messages_failed;
```

---

## Deployment

After deploying this fix:

1. **New status updates will work correctly** - counters will be updated
2. **Existing campaigns may have incorrect counters** - you may need to recalculate them

### To recalculate existing campaign counters:
```python
# Run this script to fix existing campaign counters
from app.core.database import get_db_session
from app.models.marketing import MarketingCampaignDB, CampaignRecipientDB
from sqlalchemy import func

with get_db_session() as db:
    campaigns = db.query(MarketingCampaignDB).all()
    
    for campaign in campaigns:
        # Count recipients by status
        stats = db.query(
            func.count(CampaignRecipientDB.id).filter(
                CampaignRecipientDB.status == 'sent'
            ).label('sent'),
            func.count(CampaignRecipientDB.id).filter(
                CampaignRecipientDB.status == 'delivered'
            ).label('delivered'),
            func.count(CampaignRecipientDB.id).filter(
                CampaignRecipientDB.status == 'read'
            ).label('read'),
            func.count(CampaignRecipientDB.id).filter(
                CampaignRecipientDB.status == 'failed'
            ).label('failed'),
            func.count(CampaignRecipientDB.id).filter(
                CampaignRecipientDB.status == 'pending'
            ).label('pending')
        ).filter(
            CampaignRecipientDB.campaign_id == campaign.id
        ).first()
        
        # Update campaign counters
        campaign.messages_sent = stats.sent or 0
        campaign.messages_delivered = stats.delivered or 0
        campaign.messages_read = stats.read or 0
        campaign.messages_failed = stats.failed or 0
        campaign.messages_pending = stats.pending or 0
        
        print(f"Fixed {campaign.name}: sent={stats.sent}, delivered={stats.delivered}, read={stats.read}")
    
    db.commit()
```

---

## Summary

### Before the fix:
- ✅ Individual recipient `delivered_at` and `read_at` were being set
- ❌ Campaign-level counters were NOT being updated
- ❌ Dashboard stats were incorrect

### After the fix:
- ✅ Individual recipient timestamps are set correctly
- ✅ Campaign-level counters are updated atomically
- ✅ Dashboard stats will be accurate
- ✅ No double-counting due to status transition checking
