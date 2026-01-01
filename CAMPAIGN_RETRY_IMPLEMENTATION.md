# Campaign Retry Mechanism - Implementation Guide

## Overview
Implemented automatic retry logic for failed campaign messages. The system will automatically retry sending failed messages up to a configured maximum number of attempts.

## How It Works

### 1. Database Structure
Each recipient in the `campaign_recipients` table has:
- `retry_count`: Current number of retry attempts (default: 0)
- `max_retries`: Maximum allowed retries (default: 3)
- `status`: Current delivery status (pending, sent, delivered, read, failed, skipped)
- `failure_reason`: Reason for failure (populated when status = failed)

### 2. Retry Logic Flow

#### Daily Processing Enhancement
The daily campaign processor (`process_daily_campaigns`) now:

1. **Gets pending recipients** scheduled for today (normal flow)
2. **Gets failed recipients** eligible for retry where `retry_count < max_retries`
3. **Resets failed recipients** to pending status for retry
4. **Combines both lists** to send within daily limit

#### Retry Process
When a failed recipient is reset for retry:
- Status changes from `FAILED` → `PENDING`
- Timestamps reset (`sent_at`, `delivered_at`, `read_at` = NULL)
- `whatsapp_message_id` cleared
- `scheduled_send_date` set to today
- `retry_count` incremented when message fails again
- Previous `failed_at` and `failure_reason` preserved for history

### 3. New Repository Methods

#### `get_failed_recipients_for_retry(campaign_id, limit)`
```python
# Finds failed recipients eligible for retry
# Returns recipients where retry_count < max_retries
```

#### `reset_recipient_for_retry(recipient_id)`
```python
# Resets a failed recipient to pending status
# Clears timestamps and message ID
# Schedules for immediate sending (today)
# Preserves retry count and failure history
```

### 4. Automatic Retry Behavior

**Example Scenario:**
- Recipient A: max_retries = 3, current retry_count = 0
- First attempt fails → retry_count = 1, status = FAILED
- Next day's processing:
  - System finds recipient A (1 < 3, eligible for retry)
  - Resets to PENDING status
  - Attempts to send again
- If fails again → retry_count = 2, status = FAILED
- Process repeats until:
  - Message succeeds (status = SENT/DELIVERED/READ), OR
  - retry_count reaches max_retries (3)

**After Maximum Retries:**
- Recipient remains in FAILED status
- No more automatic retries
- Manual intervention required if needed

### 5. Priority Handling

Retry messages are processed **after** regular scheduled messages:
1. First: Send to recipients scheduled for today
2. Second: Fill remaining capacity with retry attempts
3. Total messages sent ≤ `daily_send_limit`

**Example:**
- Daily limit: 250 messages
- Scheduled today: 200 recipients
- Failed (eligible): 100 recipients
- Result: Sends 200 scheduled + 50 retries = 250 total

### 6. Monitoring & Logs

The system logs retry activity:
```
📊 Found 15 failed recipients eligible for retry in campaign [ID]
🔄 Reset recipient 917829844548 for retry (attempt 2/3)
📤 Found 265 pending recipients for campaign: Test Campaign (including 15 retries)
```

### 7. Campaign Counter Updates

When retrying:
- `messages_failed` count remains accurate
- `messages_pending` includes retry attempts
- `messages_sent` incremented on successful retry
- Campaign completion determined by `messages_pending = 0`

### 8. Configuration

**Per Recipient:**
- Default `max_retries = 3` (set in database schema)
- Can be customized per recipient if needed

**System-wide:**
- Retries processed during daily scheduled runs
- Currently: Every 5 minutes (for testing)
- Production: Daily at scheduled time

## Benefits

1. **Automatic Recovery**: Transient failures (network issues, rate limits) automatically recovered
2. **No Message Loss**: Failed messages get multiple chances to deliver
3. **Controlled Limits**: Max retries prevent infinite retry loops
4. **History Preserved**: All failure reasons and timestamps kept for analysis
5. **Rate Limit Aware**: Retries respect daily send limits
6. **Smart Scheduling**: Retries fill unused capacity, don't block new messages

## Testing the Retry Feature

1. **Create a campaign** with test recipients
2. **Force a failure** (use invalid phone number or blocked recipient)
3. **Check database**:
   ```sql
   SELECT phone_number, status, retry_count, max_retries, failure_reason 
   FROM campaign_recipients 
   WHERE status = 'failed';
   ```
4. **Wait for next processing cycle** (5 minutes)
5. **Verify retry logs** in App Runner
6. **Check updated status** in database

## Maintenance

### View Retry Statistics
```sql
-- Count recipients by retry status
SELECT 
    retry_count,
    COUNT(*) as recipient_count,
    status
FROM campaign_recipients
WHERE campaign_id = 'YOUR_CAMPAIGN_ID'
GROUP BY retry_count, status
ORDER BY retry_count;
```

### Find Exhausted Retries
```sql
-- Recipients who hit max retries
SELECT phone_number, retry_count, max_retries, failure_reason
FROM campaign_recipients
WHERE status = 'failed' 
  AND retry_count >= max_retries
  AND campaign_id = 'YOUR_CAMPAIGN_ID';
```

## Edge Cases Handled

1. **Concurrent Processing**: Retry resets happen within same transaction
2. **Status Transitions**: Hierarchy prevents downgrades (read → delivered blocked)
3. **Duplicate Prevention**: Existing WhatsApp message ID checks prevent duplicates
4. **Capacity Management**: Retries respect daily limits, won't exceed
5. **Campaign Completion**: Only completes when pending = 0 (includes retries)

---

**Last Updated**: December 31, 2025
**Version**: 1.0
