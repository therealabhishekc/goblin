# Marketing Campaign System - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Recent Updates](#recent-updates)
3. [Campaign Analytics](#campaign-analytics)
4. [Status Tracking](#status-tracking)
5. [Failure Reason Tracking](#failure-reason-tracking)
6. [Database Schema](#database-schema)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Marketing Campaign System allows sending WhatsApp marketing messages to thousands of customers with proper rate limiting, scheduling, and analytics tracking.

### Key Features
- **Rate Limiting**: Respects WhatsApp's 250 messages/day limit per campaign
- **Scheduled Sending**: Process campaigns on a schedule (currently every 5 minutes for testing)
- **Status Tracking**: Tracks sent, delivered, read, and failed statuses
- **Analytics**: Real-time campaign performance metrics
- **Failure Tracking**: Detailed error logging for failed messages

---

## Recent Updates

### ✅ Status Hierarchy Fix (Jan 1, 2025)
**Problem**: Read status was being overwritten by delivered status when webhooks arrived out of order.

**Solution**: Implemented status hierarchy to prevent downgrades:
- sent (level 1) → delivered (level 2) → read (level 3)
- Once a message reaches "read", it cannot go back to "delivered" or "sent"
- Failed status (level 99) can always be set

**Files Modified**:
- `backend/app/api/webhook.py` - Added hierarchy check in `process_status_update()`

### ✅ Failure Reason Tracking (Jan 1, 2025)
**Problem**: When campaign messages failed, the reason was not being captured.

**Solution**: Enhanced webhook handler to extract and store WhatsApp error details.

**Files Modified**:
- `backend/app/api/webhook.py` - Added error extraction in `process_status_update()`

### ✅ Campaign Analytics Fix (Dec 31, 2024)
**Problem**: `messages_sent`, `messages_delivered`, and `messages_read` columns were not being filled.

**Solution**: Fixed the `update_recipient_status()` method to properly increment campaign counters.

**Files Modified**:
- `backend/app/repositories/marketing_repository.py`

---

## Campaign Analytics

### Database Tables

#### 1. `marketing_campaigns`
Main campaign table storing campaign configuration and aggregate statistics.

**Key Columns**:
- `id` - Unique campaign identifier
- `name` - Campaign name
- `status` - active, completed, cancelled, paused, draft
- `template_name` - WhatsApp template to use
- `target_audience` - JSON filter criteria
- `daily_send_limit` - Messages per day (default: 250)
- `messages_sent` - Total messages sent
- `messages_delivered` - Total messages delivered
- `messages_read` - Total messages read
- `messages_failed` - Total messages failed
- `messages_pending` - Messages waiting to be sent

#### 2. `campaign_recipients`
Individual recipient tracking with detailed status information.

**Key Columns**:
- `id` - Unique recipient identifier
- `campaign_id` - Reference to marketing_campaigns
- `phone_number` - Recipient phone number
- `status` - pending, queued, sent, delivered, read, failed
- `whatsapp_message_id` - WhatsApp message ID
- `sent_at` - When message was sent
- `delivered_at` - When message was delivered
- `read_at` - When message was read
- `failed_at` - When message failed
- `failure_reason` - Detailed error message (NEW)
- `retry_count` - Number of retry attempts

#### 3. `campaign_send_schedule`
Daily batch scheduling for rate-limited sending.

**Key Columns**:
- `campaign_id` - Reference to marketing_campaigns
- `send_date` - Date for this batch
- `batch_number` - Batch number for the day
- `batch_size` - Maximum messages in this batch
- `messages_sent` - Messages sent in this batch
- `messages_remaining` - Messages left to send
- `status` - pending, processing, completed, failed

#### 4. `campaign_analytics`
Historical analytics snapshots (daily aggregates).

**Key Columns**:
- `campaign_id` - Reference to marketing_campaigns
- `analytics_date` - Date of this snapshot
- `messages_sent` - Messages sent on this date
- `messages_delivered` - Messages delivered on this date
- `messages_read` - Messages read on this date
- `messages_failed` - Messages failed on this date
- `delivery_rate` - % delivered
- `read_rate` - % read
- `failure_rate` - % failed

---

## Status Tracking

### Status Hierarchy

WhatsApp message statuses follow a progression:
```
pending → queued → sent → delivered → read
                              ↓
                           failed
```

### Status Update Logic

**Hierarchy Levels**:
- `pending`: 1
- `queued`: 2
- `sent`: 3
- `delivered`: 4
- `read`: 5
- `failed`: 99 (can always be set)

**Rules**:
1. Status can only progress forward (higher level)
2. Once "read", cannot go back to "delivered" or "sent"
3. "failed" can be set at any time
4. Prevents webhook timing issues from causing downgrades

**Implementation**: Both `whatsapp_messages` and `campaign_recipients` tables enforce this hierarchy.

---

## Failure Reason Tracking

### WhatsApp Error Structure

When a message fails, WhatsApp sends detailed error information:

```json
{
  "statuses": [{
    "id": "wamid.xxx",
    "status": "failed",
    "recipient_id": "91xxxxxxxxxx",
    "errors": [{
      "code": 131047,
      "title": "Re-engagement message",
      "message": "Re-engagement message not sent",
      "error_data": {
        "details": "User has not initiated conversation in 24 hours"
      }
    }]
  }]
}
```

### Common Error Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 130472 | Not on WhatsApp | User's number is not registered on WhatsApp |
| 131047 | Re-engagement required | 24-hour message window expired |
| 131026 | Undeliverable | Message could not be delivered |
| 131031 | Rate limited | Too many messages sent |
| 133000 | Template not found | Template does not exist |
| 132000 | Template inactive | Template is paused or disabled |

### Stored Format

Failure reasons are stored in `campaign_recipients.failure_reason` as:
```
Error {code}: {title} - {message} ({details})
```

Example:
```
Error 131047: Re-engagement message - Re-engagement message not sent (User has not initiated conversation in 24 hours)
```

### Querying Failed Messages

```sql
-- Get all failed messages with reasons
SELECT 
    cr.campaign_id,
    mc.name as campaign_name,
    cr.phone_number,
    cr.failure_reason,
    cr.retry_count,
    cr.failed_at
FROM campaign_recipients cr
JOIN marketing_campaigns mc ON cr.campaign_id = mc.id
WHERE cr.status = 'failed'
ORDER BY cr.failed_at DESC;

-- Count failures by error type
SELECT 
    SUBSTRING(failure_reason FROM 'Error ([0-9]+):') as error_code,
    COUNT(*) as failure_count,
    ARRAY_AGG(DISTINCT campaign_id) as affected_campaigns
FROM campaign_recipients
WHERE status = 'failed' AND failure_reason IS NOT NULL
GROUP BY error_code
ORDER BY failure_count DESC;
```

---

## Database Schema

### Complete Table Structures

#### marketing_campaigns
```sql
CREATE TABLE marketing_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    template_name VARCHAR(100) NOT NULL,
    language_code VARCHAR(10) DEFAULT 'en_US',
    target_audience JSON,
    total_target_customers INTEGER DEFAULT 0,
    daily_send_limit INTEGER DEFAULT 250,
    status VARCHAR(20) DEFAULT 'draft',
    priority INTEGER DEFAULT 5,
    scheduled_start_date TIMESTAMP,
    scheduled_end_date TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    template_components JSON,
    messages_sent INTEGER DEFAULT 0,
    messages_delivered INTEGER DEFAULT 0,
    messages_read INTEGER DEFAULT 0,
    messages_failed INTEGER DEFAULT 0,
    messages_pending INTEGER DEFAULT 0,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### campaign_recipients
```sql
CREATE TABLE campaign_recipients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES marketing_campaigns(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    whatsapp_message_id VARCHAR(100),
    scheduled_send_date DATE,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    failed_at TIMESTAMP,
    failure_reason TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    template_parameters JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Reference

### Campaign Endpoints

#### Create Campaign
```http
POST /api/marketing/campaigns
Content-Type: application/json

{
  "name": "Holiday Sale 2025",
  "description": "New Year promotion",
  "template_name": "holiday_sale_template",
  "language_code": "en_US",
  "target_audience": {
    "customer_tier": ["gold", "platinum"],
    "location": "Mumbai"
  },
  "daily_send_limit": 250,
  "priority": 5,
  "scheduled_start_date": "2025-01-01T00:00:00",
  "scheduled_end_date": "2025-01-07T23:59:59"
}
```

#### Get Campaign Stats
```http
GET /api/marketing/campaigns/{campaign_id}/stats
```

Response:
```json
{
  "campaign_id": "uuid",
  "campaign_name": "Holiday Sale 2025",
  "status": "active",
  "total_target": 1000,
  "sent": 250,
  "delivered": 245,
  "read": 180,
  "failed": 5,
  "pending": 750,
  "progress_percentage": 25.0,
  "delivery_rate": 98.0,
  "read_rate": 73.5,
  "estimated_completion_date": "2025-01-05"
}
```

#### Process Daily Campaigns
```http
POST /api/marketing/campaigns/process-daily
```

Manually trigger campaign processing (also runs automatically every 5 minutes via EventBridge).

---

## Troubleshooting

### Common Issues

#### 1. Recipients Not Receiving Messages

**Symptoms**: Campaign created, participants added, but messages not sent.

**Check**:
```sql
-- Check campaign status
SELECT id, name, status, messages_pending, messages_sent 
FROM marketing_campaigns 
WHERE id = 'your-campaign-id';

-- Check recipient status
SELECT phone_number, status, scheduled_send_date, failure_reason
FROM campaign_recipients 
WHERE campaign_id = 'your-campaign-id';

-- Check send schedule
SELECT send_date, status, messages_sent, messages_remaining
FROM campaign_send_schedule
WHERE campaign_id = 'your-campaign-id';
```

**Common Causes**:
- Campaign status not "active"
- Scheduled send date in the future
- Daily limit reached
- EventBridge rule disabled

#### 2. Failed Messages

**Check failure reasons**:
```sql
SELECT phone_number, failure_reason, retry_count, failed_at
FROM campaign_recipients
WHERE campaign_id = 'your-campaign-id' AND status = 'failed'
ORDER BY failed_at DESC;
```

**Common Reasons**:
- Error 131047: 24-hour window expired (user hasn't messaged in 24h)
- Error 130472: Number not on WhatsApp
- Error 133000: Template doesn't exist

#### 3. Status Not Updating

**Symptoms**: Messages sent but status stuck at "sent", not updating to "delivered" or "read".

**Check App Runner Logs**:
```bash
# Look for status update logs
grep "Status update:" logs.txt
grep "Updated campaign recipient status:" logs.txt
grep "Updated whatsapp_messages status:" logs.txt
```

**Common Causes**:
- Webhook not configured properly
- Status downgrade being prevented (by design)
- Database connection issues

#### 4. Campaign Not Processing

**Check EventBridge**:
1. Go to AWS EventBridge console
2. Find rule: `{StackName}-CampaignProcessingSchedule`
3. Check if enabled
4. View CloudWatch logs for Lambda function

**Manual Processing**:
```bash
curl -X POST https://your-app-runner-url/api/marketing/campaigns/process-daily
```

---

## Monitoring

### Key Metrics to Track

1. **Campaign Success Rate**: `(messages_delivered / messages_sent) * 100`
2. **Read Rate**: `(messages_read / messages_delivered) * 100`
3. **Failure Rate**: `(messages_failed / messages_sent) * 100`
4. **Processing Time**: Check App Runner logs
5. **Daily Send Volume**: Track against WhatsApp limits

### CloudWatch Logs

**App Runner Logs**:
- Campaign processing: `📥 Processing X campaigns`
- Message sending: `✅ Text message sent to {phone}`
- Status updates: `📊 Status update: {message_id} -> {status}`
- Failures: `❌ Message {message_id} failed: {reason}`

**Lambda Logs** (EventBridge trigger):
- Function invocation
- API call success/failure
- Processing results

---

## Best Practices

1. **Rate Limiting**: Keep daily_send_limit ≤ 250 to respect WhatsApp limits
2. **Testing**: Use test campaigns with small audience before full rollout
3. **Monitoring**: Check failure reasons regularly and adjust templates/audience
4. **24-Hour Rule**: Only send marketing messages to users who have messaged you in the last 24 hours, or use approved templates
5. **Template Management**: Ensure templates are approved and active before campaign
6. **Scheduling**: Allow buffer time for processing (don't schedule too close to current time)

---

## Future Enhancements

- [ ] Add failure reason to campaign analytics dashboard
- [ ] Create alerts for high failure rates
- [ ] Implement smart retry logic based on error type
- [ ] Export failure reports for analysis
- [ ] Add A/B testing support
- [ ] Implement customer segment management
- [ ] Add template preview before sending
- [ ] Create scheduled reports
- [ ] Add campaign cloning feature
- [ ] Implement cost tracking per campaign

