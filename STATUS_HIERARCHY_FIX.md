# WhatsApp Message Status Hierarchy Fix

## Problem
WhatsApp webhooks can arrive out of order, causing message status to be downgraded (e.g., from "read" to "delivered"). This was happening because the webhook handler was updating the status without checking if the new status was actually a progression or a regression.

### Example of the Issue
```
Time 1: Message sent -> status: "sent"
Time 2: Message read (webhook arrives first) -> status: "read" ✅
Time 3: Message delivered (webhook arrives late) -> status: "delivered" ❌ (downgrade!)
```

## Solution
Implemented a status hierarchy system that prevents status downgrades in both:
1. `whatsapp_messages` table
2. `campaign_recipients` table

### Status Hierarchy

#### For whatsapp_messages:
```
sent (1) < delivered (2) < read (3)
failed (99) - can always be set
```

#### For campaign_recipients:
```
pending (1) < queued (2) < sent (3) < delivered (4) < read (5)
failed (99) - can always be set
skipped (99) - can always be set
```

## Changes Made

### 1. Updated webhook.py
File: `backend/app/api/webhook.py`
Function: `process_status_update()`

**Before:**
```python
if status in valid_statuses:
    whatsapp_message.status = status
    db.commit()
```

**After:**
```python
# Define status hierarchy: sent < delivered < read
status_hierarchy = {
    "sent": 1,
    "delivered": 2,
    "read": 3,
    "failed": 99  # Failed is always updated
}

current_status = whatsapp_message.status or "sent"
current_level = status_hierarchy.get(current_status, 0)
new_level = status_hierarchy.get(status, 0)

# Only update if new status is higher in hierarchy or is "failed"
if new_level >= current_level:
    whatsapp_message.status = status
    db.commit()
    message_updated = True
    logger.info(f"✅ Updated whatsapp_messages status: {message_id} -> {status}")
else:
    logger.info(f"⏭️  Skipped whatsapp_messages status downgrade: {message_id} ({current_status} -> {status})")
```

### 2. Updated marketing_repository.py
File: `backend/app/repositories/marketing_repository.py`
Function: `update_recipient_status()`

**Added hierarchy check:**
```python
# Define status hierarchy to prevent downgrades
status_hierarchy = {
    "pending": 1,
    "queued": 2,
    "sent": 3,
    "delivered": 4,
    "read": 5,
    "failed": 99,  # Can always set to failed
    "skipped": 99  # Can always set to skipped
}

current_level = status_hierarchy.get(old_status, 0)
new_level = status_hierarchy.get(status.value, 0)

# Only update if new status is higher in hierarchy or is terminal (failed/skipped)
if new_level < current_level and new_level < 99:
    logger.info(f"⏭️  Skipped recipient status downgrade: {recipient.phone_number} ({old_status} -> {status.value})")
    return recipient
```

## Testing
After deployment, monitor the logs for messages like:
- `⏭️  Skipped whatsapp_messages status downgrade: <message_id> (read -> delivered)` - This is expected and correct
- `✅ Updated whatsapp_messages status: <message_id> -> read` - Normal progression

## Expected Behavior

### Scenario 1: Normal Order
```
1. sent -> status updated to "sent"
2. delivered -> status updated to "delivered" 
3. read -> status updated to "read"
```

### Scenario 2: Out of Order (Fixed)
```
1. sent -> status updated to "sent"
2. read (arrives first) -> status updated to "read"
3. delivered (arrives late) -> status remains "read" (downgrade prevented) ⏭️
```

### Scenario 3: Failed Status (Always Updated)
```
1. sent -> status updated to "sent"
2. failed -> status updated to "failed" (even if read)
```

## Benefits
1. ✅ Accurate status tracking regardless of webhook order
2. ✅ Prevents data inconsistency
3. ✅ Maintains status integrity
4. ✅ Better campaign analytics
5. ✅ Clearer audit trail with skip logs

## Deployment
No database migration required. Changes are backward compatible.

Deploy by restarting the backend application:
```bash
# The changes will take effect immediately upon restart
```
