# Marketing Campaign System - Quick Start Guide

## 🎯 Problem
- Send to 10,000 customers
- WhatsApp limit: 250 messages/day
- Don't send duplicates
- Timeline: 40 days to complete

## 📊 Solution Overview

```
Day 1:  250 customers → Sent ✅
Day 2:  250 customers → Sent ✅
Day 3:  250 customers → Sent ✅
...
Day 40: 250 customers → Sent ✅
Total: 10,000 customers reached
```

## 🗄️ 3 New Database Tables

### 1. `marketing_campaigns`
Stores campaign details, template, targeting, and progress.

### 2. `marketing_campaign_recipients`  
Tracks EACH customer's delivery status for EACH campaign.
- **Key**: `(campaign_id, user_phone)` = UNIQUE (prevents duplicates)
- Stores: scheduled_date, sent_at, delivered_at, status

### 3. `marketing_daily_quotas`
Tracks daily usage to enforce 250/day limit.

## 🔄 How It Works

### Step 1: Create Campaign (One-Time)
```bash
POST /api/campaigns
{
  "name": "Summer Sale",
  "template_name": "discount_20_percent",
  "target_audience": {"customer_tier": ["premium"]},
  "start_date": "2025-06-01T09:00:00Z",
  "daily_limit": 250
}
```

**System automatically:**
1. Finds all subscribed premium customers (e.g., 10,000)
2. Assigns scheduled_date to each customer:
   - Customer 1-250: June 1
   - Customer 251-500: June 2
   - Customer 501-750: June 3
   - ... and so on
3. Creates 10,000 recipient records with status="pending"

### Step 2: Daily Sending (Automated)
Cron job runs every day at 9 AM:
```python
send_daily_marketing_messages()
```

**Process:**
1. Query: "Give me 250 recipients where scheduled_date=TODAY and status=pending"
2. For each recipient:
   - Send WhatsApp template message
   - Update status to "sent"
   - Store message_id
   - Increment daily counter
3. Stop when 250 reached or no more pending for today

### Step 3: Track Delivery (Real-Time)
WhatsApp sends webhooks when:
- ✅ Message delivered → Update status to "delivered"
- 👀 Customer reads → Update status to "read"
- ❌ Send failed → Update status to "failed", retry later

### Step 4: View Progress
```bash
GET /api/campaigns/{id}/stats

Response:
{
  "total_recipients": 10000,
  "messages_sent": 2500,      # Day 10
  "messages_delivered": 2450,
  "messages_read": 1200,
  "pending": 7500,             # Remaining
  "delivery_rate": 98.0,
  "estimated_completion": "2025-07-10"
}
```

## 🚫 How Duplicates Are Prevented

### Database Constraint:
```sql
UNIQUE(campaign_id, user_phone)
```

**Example:**
- Campaign A, Customer +1234567890 → ✅ Sent June 1
- Campaign A, Customer +1234567890 → ❌ BLOCKED (duplicate)
- Campaign B, Customer +1234567890 → ✅ Allowed (different campaign)

Even if you accidentally try to add the same customer twice, the database rejects it!

## 🎛️ Daily Quota Enforcement

```python
# Before sending each batch:
quota = get_today_quota()
if quota.messages_sent >= 250:
    return "Daily limit reached"

# After sending each message:
quota.messages_sent += 1
```

**Result:** Never sends more than 250/day, no matter how many campaigns are running.

## 📈 Example Timeline

### Campaign: "Holiday Sale" (10,000 customers)
```
June 1:  Send 250 → Total sent: 250    → Remaining: 9,750
June 2:  Send 250 → Total sent: 500    → Remaining: 9,500
June 3:  Send 250 → Total sent: 750    → Remaining: 9,250
...
July 10: Send 250 → Total sent: 10,000 → Remaining: 0 ✅ COMPLETE
```

## 🎨 Multiple Campaigns

### Scenario: 2 Campaigns Running Simultaneously
```
Campaign A: 5,000 customers (20 days)
Campaign B: 3,000 customers (12 days)
```

**Daily Distribution:**
```
Day 1:  
  - 125 from Campaign A
  - 125 from Campaign B
  - Total: 250 ✅

Day 2:  
  - 125 from Campaign A
  - 125 from Campaign B
  - Total: 250 ✅
```

System automatically balances across campaigns to respect 250/day total!

## 🔍 Tracking Per Customer

### Database Record Example:
```sql
SELECT * FROM marketing_campaign_recipients 
WHERE user_phone = '+1234567890';

Result:
campaign_id          | scheduled_date | status    | sent_at             | message_id
---------------------|----------------|-----------|---------------------|------------
campaign-A           | 2025-06-01     | delivered | 2025-06-01 09:00:00 | wamid.ABC123
campaign-B           | 2025-06-15     | read      | 2025-06-15 09:00:00 | wamid.XYZ789
campaign-C           | 2025-07-01     | pending   | NULL                | NULL
```

**Query:**
- "Which campaigns did customer receive?" → 2 (A, B)
- "Which campaigns still pending?" → 1 (C)
- "Did customer receive Campaign A?" → Yes, on June 1

## 🛠️ Implementation Steps

1. **Run Migration**
   ```bash
   psql -f backend/migrations/add_marketing_tables.sql
   ```

2. **Add Python Models**
   - Copy `marketing.py` to `backend/app/models/`

3. **Add Service**
   - Copy `marketing_service.py` to `backend/app/services/`

4. **Add Worker**
   - Copy `marketing_sender.py` to `backend/app/workers/`

5. **Add API Endpoints**
   - Add campaign routes to `api_endpoints.py`

6. **Setup Cron Job**
   ```bash
   0 9 * * * python /path/to/marketing_sender.py
   ```

## 📊 Query Examples

### Find which customers got which campaigns:
```sql
SELECT 
    u.whatsapp_phone,
    u.display_name,
    c.name AS campaign_name,
    r.status,
    r.sent_at
FROM marketing_campaign_recipients r
JOIN user_profiles u ON r.user_phone = u.whatsapp_phone
JOIN marketing_campaigns c ON r.campaign_id = c.id
WHERE u.whatsapp_phone = '+1234567890';
```

### Get today's pending sends:
```sql
SELECT COUNT(*) 
FROM marketing_campaign_recipients
WHERE scheduled_date = CURRENT_DATE 
  AND status = 'pending';
```

### Check daily quota usage:
```sql
SELECT messages_sent, daily_limit, (daily_limit - messages_sent) AS remaining
FROM marketing_daily_quotas
WHERE date = CURRENT_DATE;
```

## ✅ Benefits

1. **No Duplicates**: Database enforces uniqueness
2. **Automatic**: Set and forget - runs daily
3. **Scalable**: Handles millions of recipients
4. **Trackable**: See exactly who received what
5. **Compliant**: Respects API limits
6. **Targeted**: Send to specific customer segments
7. **Analytics**: Real-time campaign performance

---

**Result**: You can now send marketing messages to 10,000 customers over 40 days, with full tracking, no duplicates, and automatic daily sending! 🚀
