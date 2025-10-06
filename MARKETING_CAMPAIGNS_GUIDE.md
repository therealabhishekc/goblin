# Marketing Campaigns System - Complete Guide

## 📊 Overview

This system allows you to send WhatsApp marketing messages to thousands of customers while respecting WhatsApp's rate limit of **250 messages per day**. It includes:

- ✅ **Duplicate Prevention**: Never send the same campaign message to a customer twice
- ✅ **Rate Limiting**: Automatically spreads sends across days (250/day limit)
- ✅ **Subscription Management**: Only sends to subscribed users
- ✅ **Campaign Tracking**: Track sent, delivered, read, failed messages
- ✅ **Scheduled Sending**: Set specific start/end dates
- ✅ **Progress Monitoring**: Real-time campaign statistics
- ✅ **Automated Replies Continue Working**: Marketing campaigns don't affect automated responses

---

## 🏗️ Architecture

### Database Tables

1. **`marketing_campaigns`** - Campaign metadata and configuration
2. **`campaign_recipients`** - Individual recipients and their send status
3. **`campaign_send_schedule`** - Daily send batches (250 messages/day)
4. **`campaign_analytics`** - Daily performance metrics

### Key Features

- **Duplicate Prevention**: `UNIQUE (campaign_id, phone_number)` constraint
- **Auto-Scheduling**: Recipients automatically distributed across days
- **Status Tracking**: `pending` → `queued` → `sent` → `delivered` → `read`
- **Analytics**: Automatic calculation of delivery rate, read rate, response rate

---

## 🚀 Quick Start

### Step 1: Run Database Migration

```bash
cd /Users/abskchsk/Documents/govindjis/wa-app

# Apply the migration
psql -h whatsapp-postgres-development.cyd40iccy9uu.us-east-1.rds.amazonaws.com \
     -U postgres \
     -d whatsapp_business_development \
     -f backend/migrations/add_marketing_campaigns.sql
```

### Step 2: Create a Campaign

```bash
curl -X POST https://your-api.com/marketing/campaigns \
-H "Content-Type: application/json" \
-d '{
  "name": "Summer Sale 2025",
  "description": "30% off all items",
  "template_name": "summer_sale_promo",
  "language_code": "en_US",
  "daily_send_limit": 250,
  "priority": 5,
  "target_audience": {
    "customer_tier": "premium"
  },
  "template_components": [
    {
      "type": "body",
      "parameters": [
        {"type": "text", "text": "30%"}
      ]
    }
  ]
}'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Summer Sale 2025",
  "status": "draft",
  "template_name": "summer_sale_promo",
  "message": "Campaign 'Summer Sale 2025' created successfully"
}
```

### Step 3: Add Recipients

**Option A: Use Target Audience (Recommended)**
```bash
curl -X POST "https://your-api.com/marketing/campaigns/{campaign_id}/recipients?use_target_audience=true"
```

This automatically selects all **subscribed** customers matching the campaign's target audience.

**Option B: Explicit Phone Numbers**
```bash
curl -X POST https://your-api.com/marketing/campaigns/{campaign_id}/recipients \
-H "Content-Type: application/json" \
-d '{
  "phone_numbers": [
    "14694652751",
    "19453083188",
    "14155551234",
    ...
  ]
}'
```

**Response:**
```json
{
  "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
  "recipients_added": 9847,
  "total_recipients": 9847,
  "message": "Added 9847 recipients to campaign"
}
```

### Step 4: Activate Campaign

```bash
curl -X POST "https://your-api.com/marketing/campaigns/{campaign_id}/activate?start_date=2025-10-05"
```

**Response:**
```json
{
  "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "recipients_scheduled": 9847,
  "daily_limit": 250,
  "estimated_days": 40,
  "estimated_completion_date": "2025-11-14",
  "message": "Campaign activated. Sending 250 messages/day starting 2025-10-05"
}
```

### Step 5: Daily Processing (Automated)

Set up a cron job or scheduled task to run daily:

```bash
# Run at 9 AM every day
0 9 * * * curl -X POST https://your-api.com/marketing/process-daily
```

Or run manually:
```bash
curl -X POST https://your-api.com/marketing/process-daily
```

This will:
- Send up to 250 messages for each active campaign
- Update recipient status
- Record analytics
- Skip unsubscribed users

---

## 📈 Monitoring & Management

### Get Campaign Statistics

```bash
curl https://your-api.com/marketing/campaigns/{campaign_id}/stats
```

**Response:**
```json
{
  "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
  "campaign_name": "Summer Sale 2025",
  "status": "active",
  "total_target": 9847,
  "sent": 750,
  "delivered": 732,
  "read": 489,
  "failed": 18,
  "pending": 9097,
  "progress_percentage": 7.62,
  "delivery_rate": 97.6,
  "read_rate": 65.2,
  "estimated_completion_date": "2025-11-14"
}
```

### List All Campaigns

```bash
# All campaigns
curl https://your-api.com/marketing/campaigns

# Filter by status
curl "https://your-api.com/marketing/campaigns?status=active"
```

### Pause Campaign

```bash
curl -X POST https://your-api.com/marketing/campaigns/{campaign_id}/pause
```

### Resume Campaign

```bash
curl -X POST https://your-api.com/marketing/campaigns/{campaign_id}/resume
```

### Cancel Campaign

```bash
curl -X POST https://your-api.com/marketing/campaigns/{campaign_id}/cancel
```

---

## 🔄 How It Works

### Sending Flow

```
1. Create Campaign (status: draft)
   ↓
2. Add Recipients (checks for duplicates, filters unsubscribed)
   ↓
3. Activate Campaign (creates daily schedule, status: active)
   ↓
4. Daily Processing Job Runs
   ↓
5. For each active campaign:
   - Get today's scheduled recipients (max 250)
   - Check subscription status
   - Send template message via SQS
   - Update recipient status: pending → queued → sent
   ↓
6. WhatsApp delivers messages
   - Status updates via webhook: sent → delivered → read
   ↓
7. Campaign completes when all recipients sent
```

### Duplicate Prevention

The system prevents duplicates in 3 ways:

1. **Database Constraint**: `UNIQUE (campaign_id, phone_number)`
2. **Add Recipients Check**: Automatically skips existing recipients
3. **Status Check**: Only processes recipients with status `pending`

Example:
```
Campaign has 10,000 recipients
Day 1: Send 250 ✅ (status: pending → sent)
Day 2: Send 250 ✅ (next batch)
Day 1 recipients: NEVER sent again ✅
```

### Subscription Management

- Only **subscribed** users receive marketing templates
- Users can unsubscribe by sending "STOP"
- Unsubscribed users are automatically skipped during sending
- **Automated replies still work** for unsubscribed users

---

## 💡 Use Cases

### Use Case 1: Send to 10,000 Customers

```bash
# 1. Create campaign
campaign_id=$(curl -X POST .../marketing/campaigns ... | jq -r '.id')

# 2. Add 10,000 phone numbers
curl -X POST .../marketing/campaigns/$campaign_id/recipients \
  -d '{"phone_numbers": [...10000 numbers...]}'

# 3. Activate (auto-schedules 40 days)
curl -X POST ".../marketing/campaigns/$campaign_id/activate"

# 4. Set up cron job to run daily
# Campaign will complete in ~40 days
```

**Timeline:**
- Day 1: Send 250 messages
- Day 2: Send 250 messages
- Day 3: Send 250 messages
- ...
- Day 40: Send final 250 messages ✅ Complete

### Use Case 2: Target Premium Customers

```bash
curl -X POST .../marketing/campaigns \
-d '{
  "name": "VIP Sale",
  "template_name": "vip_exclusive",
  "target_audience": {
    "customer_tier": "premium",
    "tags": ["high_value"]
  }
}'

# Auto-select all premium customers with high_value tag
curl -X POST ".../campaigns/$campaign_id/recipients?use_target_audience=true"
```

### Use Case 3: Multiple Simultaneous Campaigns

The system supports multiple active campaigns:

```
Campaign A: "Summer Sale" - 5000 recipients - Priority 1
Campaign B: "New Arrivals" - 3000 recipients - Priority 2
Campaign C: "Clearance" - 2000 recipients - Priority 3

Daily Processing:
- Campaign A: 250 messages (highest priority)
- Campaign B: 250 messages
- Campaign C: 250 messages
Total: 750 messages/day across 3 campaigns
```

Each campaign respects its own 250/day limit.

---

## 🛠️ API Reference

### Create Campaign

**POST** `/marketing/campaigns`

```json
{
  "name": "Campaign Name",
  "description": "Campaign description",
  "template_name": "your_template_name",
  "language_code": "en_US",
  "daily_send_limit": 250,
  "priority": 5,
  "target_audience": {
    "customer_tier": "premium",
    "tags": ["fashion", "accessories"]
  },
  "scheduled_start_date": "2025-10-05T09:00:00Z",
  "template_components": [...]
}
```

### Add Recipients

**POST** `/marketing/campaigns/{campaign_id}/recipients`

Query param: `use_target_audience=true|false`

Body (if not using target audience):
```json
{
  "phone_numbers": ["14694652751", "19453083188", ...]
}
```

### Activate Campaign

**POST** `/marketing/campaigns/{campaign_id}/activate`

Query param: `start_date=2025-10-05` (optional, defaults to tomorrow)

### Get Stats

**GET** `/marketing/campaigns/{campaign_id}/stats`

### List Campaigns

**GET** `/marketing/campaigns?status=active&limit=50`

### Pause/Resume/Cancel

**POST** `/marketing/campaigns/{campaign_id}/pause`
**POST** `/marketing/campaigns/{campaign_id}/resume`
**POST** `/marketing/campaigns/{campaign_id}/cancel`

### Process Daily (Cron Job)

**POST** `/marketing/process-daily`

---

## ⚙️ Configuration

### Campaign Settings

| Setting | Description | Default | Range |
|---------|-------------|---------|-------|
| `daily_send_limit` | Messages per day | 250 | 1-1000 |
| `priority` | Campaign priority | 5 | 1 (high) - 10 (low) |
| `retry_count` | Failed message retries | 0 | 0-3 |

### Template Requirements

- Template must be **approved** by WhatsApp
- Template must exist in your WhatsApp Business Account
- Use correct `language_code` (e.g., `en_US`, `es`, `pt_BR`)

---

## 🔍 Troubleshooting

### Issue: Recipients not receiving messages

**Check:**
1. Campaign status is `active`
2. Recipients have `scheduled_send_date` = today
3. User subscription status is `subscribed`
4. Daily process job is running
5. WhatsApp template is approved

**Solution:**
```bash
# Check campaign status
curl .../marketing/campaigns/{campaign_id}/stats

# Check subscription
SELECT subscription FROM user_profiles WHERE whatsapp_phone = '14694652751';

# Manually trigger daily process
curl -X POST .../marketing/process-daily
```

### Issue: Duplicate messages being sent

**This should NEVER happen** due to:
- Database unique constraint
- Status checking (only `pending` recipients processed)

If duplicates occur:
```sql
-- Check for duplicates
SELECT phone_number, COUNT(*) 
FROM campaign_recipients 
WHERE campaign_id = 'xxx' 
GROUP BY phone_number 
HAVING COUNT(*) > 1;
```

### Issue: Campaign stuck at 0% progress

**Check:**
1. Campaign has been activated
2. Send schedule has been created
3. Daily process job is running

**Solution:**
```sql
-- Check schedule
SELECT * FROM campaign_send_schedule 
WHERE campaign_id = 'xxx' 
AND send_date = CURRENT_DATE;

-- Check pending recipients
SELECT COUNT(*) FROM campaign_recipients 
WHERE campaign_id = 'xxx' 
AND status = 'pending';
```

---

## 📊 Database Queries

### View Campaign Progress

```sql
SELECT * FROM v_active_campaigns;
```

### View Today's Schedule

```sql
SELECT * FROM v_daily_campaign_schedule 
WHERE send_date = CURRENT_DATE;
```

### View Recipient Status

```sql
SELECT status, COUNT(*) as count
FROM campaign_recipients
WHERE campaign_id = 'xxx'
GROUP BY status
ORDER BY count DESC;
```

### View Daily Analytics

```sql
SELECT 
    date,
    messages_sent,
    messages_delivered,
    delivery_rate,
    read_rate
FROM campaign_analytics
WHERE campaign_id = 'xxx'
ORDER BY date DESC;
```

---

## ✅ Best Practices

1. **Test with Small Campaigns First**
   - Start with 10-50 recipients
   - Verify delivery and responses
   - Then scale to thousands

2. **Use Target Audience**
   - More maintainable than explicit lists
   - Automatically filters unsubscribed users
   - Easy to reuse for future campaigns

3. **Monitor Daily**
   - Check campaign stats daily
   - Monitor delivery rates
   - Adjust strategy based on analytics

4. **Respect Unsubscribes**
   - System automatically skips unsubscribed users
   - Never manually override subscription status
   - Keep unsubscribe process simple ("STOP")

5. **Set Appropriate Priorities**
   - Time-sensitive campaigns: Priority 1-3
   - General promotions: Priority 5
   - Low-priority updates: Priority 8-10

6. **Plan Ahead**
   - Large campaigns (10,000+) take 40+ days
   - Schedule start dates in advance
   - Consider campaign overlap

---

## 🎯 Summary

### What This System Does

✅ Sends marketing messages to thousands of customers
✅ Respects WhatsApp's 250 messages/day limit
✅ **Prevents duplicate sends** to same customer
✅ Only sends to subscribed users
✅ Tracks delivery, read, and engagement
✅ Supports multiple simultaneous campaigns
✅ Provides real-time progress monitoring

### What It Does NOT Affect

❌ Automated replies (still work normally)
❌ Incoming message processing
❌ Customer conversations
❌ Webhook handling

### Key Takeaways

- **10,000 recipients** = **~40 days** at 250/day
- **Duplicates prevented** by database constraints
- **Unsubscribed users skipped** automatically
- **Multiple campaigns** can run simultaneously
- **Daily cron job** required for sending

---

## 🆘 Support

For issues or questions:

1. Check `/marketing/health` endpoint
2. Review `/marketing/campaigns/{id}/stats`
3. Check database tables directly
4. Review application logs

**Common Commands:**
```bash
# Health check
curl https://your-api.com/marketing/health

# Campaign stats
curl https://your-api.com/marketing/campaigns/{id}/stats

# Database check
psql -h ... -U postgres -d whatsapp_business_development -c "SELECT * FROM v_active_campaigns;"
```

---

**Last Updated**: October 3, 2025
**Version**: 1.0.0
