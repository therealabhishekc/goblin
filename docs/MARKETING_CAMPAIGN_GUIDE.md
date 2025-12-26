# Marketing Campaign Complete Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [Campaign Setup Flow](#campaign-setup-flow)
3. [API Endpoints Reference](#api-endpoints-reference)
4. [Database Storage Flow](#database-storage-flow)
5. [Complete Step-by-Step Example](#complete-step-by-step-example)
6. [Data Flow Diagram](#data-flow-diagram)
7. [Best Practices](#best-practices)

---

## 🎯 Overview

The marketing campaign system allows you to send WhatsApp template messages to thousands of customers while:
- ✅ **Enforcing 250 messages/day rate limit** (WhatsApp policy)
- ✅ **Preventing duplicate sends** to the same customer
- ✅ **Respecting subscription preferences** (STOP/START commands)
- ✅ **Tracking delivery and engagement** metrics

### Key Features
- Create campaigns with target audience filtering
- Automatically schedule sends across multiple days
- Real-time progress tracking
- Pause/resume/cancel campaigns
- Detailed analytics and reporting

---

## 🔄 Campaign Setup Flow

```
1. CREATE CAMPAIGN (Draft)
   ↓
2. ADD RECIPIENTS (Manual or Auto-select)
   ↓
3. ACTIVATE CAMPAIGN (Create Schedule)
   ↓
4. DAILY PROCESSING (Automatic via scheduler)
   ↓
5. TRACK PROGRESS (Real-time stats)
```

---

## 📡 API Endpoints Reference

### Base URL
```
/api/marketing
```

---

### 1️⃣ Create Campaign

**Endpoint:** `POST /marketing/campaigns`

**Purpose:** Create a new marketing campaign (starts in DRAFT status)

**Request Body:**
```json
{
  "name": "Summer Sale 2025",
  "description": "Promotional campaign for summer sale",
  "template_name": "summer_sale_promo",
  "language_code": "en_US",
  "daily_send_limit": 250,
  "priority": 5,
  "target_audience": {
    "customer_tier": "premium",
    "city": "New York",
    "tags": ["fashion", "accessories"]
  },
  "template_components": [
    {
      "type": "header",
      "parameters": [
        {
          "type": "image",
          "image": {"link": "https://example.com/sale-banner.jpg"}
        }
      ]
    },
    {
      "type": "body",
      "parameters": [
        {"type": "text", "text": "30%"}
      ]
    }
  ]
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Summer Sale 2025",
  "status": "draft",
  "template_name": "summer_sale_promo",
  "message": "Campaign 'Summer Sale 2025' created successfully"
}
```

**Database Changes:**
- ✅ Creates record in `marketing_campaigns` table with status='draft'
- Fields: name, template_name, target_audience, daily_send_limit, priority
- Auto-generated: id (UUID), created_at, updated_at

---

### 2️⃣ Add Recipients

**Endpoint:** `POST /marketing/campaigns/{campaign_id}/recipients`

**Purpose:** Add customers to the campaign

#### Option A: Explicit Phone Numbers

**Request Body:**
```json
{
  "phone_numbers": [
    "14694652751",
    "19453083188",
    "15551234567"
  ]
}
```

#### Option B: Auto-select from Target Audience

**Request:** `POST /marketing/campaigns/{campaign_id}/recipients?use_target_audience=true`

This automatically selects all **SUBSCRIBED** customers matching the campaign's target_audience criteria.

**Response:**
```json
{
  "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
  "recipients_added": 10000,
  "total_recipients": 10000,
  "message": "Added 10000 recipients to campaign"
}
```

**Database Changes:**
- ✅ Creates records in `campaign_recipients` table
- One row per recipient with:
  - campaign_id (FK to marketing_campaigns)
  - phone_number
  - status='pending'
  - scheduled_send_date=NULL (assigned later during activation)
  - UNIQUE constraint prevents duplicates
- ✅ Updates `marketing_campaigns`:
  - total_target_customers += count
  - messages_pending += count

**Important Notes:**
- 🔴 **Duplicate Prevention:** UNIQUE(campaign_id, phone_number) prevents adding same customer twice
- 🔴 **Subscription Check:** Only SUBSCRIBED users are added when using target_audience
- Unsubscribed users are automatically filtered out

---

### 3️⃣ Activate Campaign

**Endpoint:** `POST /marketing/campaigns/{campaign_id}/activate?start_date=2025-01-15`

**Purpose:** Activate campaign and create send schedule

**Query Parameters:**
- `start_date` (optional): Date to start sending (defaults to tomorrow)

**Response:**
```json
{
  "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "active",
  "recipients_scheduled": 10000,
  "daily_limit": 250,
  "estimated_days": 40,
  "estimated_completion_date": "2025-02-24",
  "message": "Campaign activated. Sending 250 messages/day starting 2025-01-15"
}
```

**Database Changes:**

**1. Updates `campaign_recipients` table:**
- Assigns `scheduled_send_date` to each recipient
- Distributes recipients across days based on daily_send_limit
- Example: 10,000 recipients ÷ 250/day = 40 days
  - Day 1: Recipients 1-250 get scheduled_send_date = 2025-01-15
  - Day 2: Recipients 251-500 get scheduled_send_date = 2025-01-16
  - ... and so on

**2. Creates records in `campaign_send_schedule` table:**
- One record per day with:
  - campaign_id
  - send_date (2025-01-15, 2025-01-16, ...)
  - batch_number = 1
  - batch_size = 250 (or remaining count for last day)
  - messages_remaining = 250
  - status = 'pending'

**3. Updates `marketing_campaigns` table:**
- status = 'active'
- started_at = current timestamp

**Validation:**
- ❌ Error if campaign has 0 recipients
- ❌ Error if campaign not found

---

### 4️⃣ Process Daily Campaigns

**Endpoint:** `POST /marketing/process-daily`

**Purpose:** Send today's scheduled messages (called by scheduled job/cron)

**⚠️ Important:** This endpoint should be called **once per day** by a scheduler (cron job, AWS EventBridge, etc.)

**Response:**
```json
{
  "date": "2025-01-15",
  "campaigns_processed": 3,
  "messages_sent": 750,
  "message": "Processed 3 campaigns, sent 750 messages"
}
```

**What It Does:**

**1. Queries `campaign_send_schedule` table:**
```sql
SELECT * FROM campaign_send_schedule
WHERE send_date = CURRENT_DATE
AND status IN ('pending', 'processing')
ORDER BY created_at ASC
```

**2. For each schedule, queries `campaign_recipients`:**
```sql
SELECT * FROM campaign_recipients
WHERE campaign_id = ?
AND status = 'pending'
AND scheduled_send_date = CURRENT_DATE
LIMIT 250
```

**3. For each recipient:**
- ✅ **Check subscription:** Verify user is still subscribed
  - If unsubscribed → Update status='skipped', skip sending
- ✅ **Send message:** Queue template message via WhatsApp API
- ✅ **Update recipient:** Set status='queued', store whatsapp_message_id
- ❌ **Handle failures:** Set status='failed', record failure_reason

**4. Database updates:**

**Updates `campaign_recipients`:**
```sql
-- For successfully sent
UPDATE campaign_recipients
SET status = 'queued',
    whatsapp_message_id = 'wamid.xxx',
    updated_at = NOW()
WHERE id = ?

-- For failures
UPDATE campaign_recipients
SET status = 'failed',
    failed_at = NOW(),
    failure_reason = 'Error message',
    retry_count = retry_count + 1
WHERE id = ?

-- For unsubscribed
UPDATE campaign_recipients
SET status = 'skipped',
    failure_reason = 'User unsubscribed'
WHERE id = ?
```

**Updates `marketing_campaigns` (via trigger):**
- Automatically recalculates counts when recipient status changes
- messages_sent, messages_delivered, messages_read, messages_failed, messages_pending

**Creates records in `campaign_analytics`:**
- One row per campaign per day with daily metrics

---

### 5️⃣ Get Campaign Stats

**Endpoint:** `GET /marketing/campaigns/{campaign_id}/stats`

**Response:**
```json
{
  "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
  "campaign_name": "Summer Sale 2025",
  "status": "active",
  "total_target": 10000,
  "sent": 2500,
  "delivered": 2400,
  "read": 1800,
  "failed": 50,
  "pending": 7450,
  "progress_percentage": 25.0,
  "delivery_rate": 96.0,
  "read_rate": 72.0,
  "estimated_completion_date": "2025-02-24"
}
```

**Database Query:**
Reads from `marketing_campaigns` table (counts are auto-updated by triggers)

---

### 6️⃣ List Campaigns

**Endpoint:** `GET /marketing/campaigns?status=active&limit=50`

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Summer Sale 2025",
    "status": "active",
    "template_name": "summer_sale_promo",
    "total_target": 10000,
    "messages_sent": 2500,
    "messages_pending": 7450,
    "progress": 25.0,
    "created_at": "2025-01-10T10:00:00"
  }
]
```

---

### 7️⃣ Pause Campaign

**Endpoint:** `POST /marketing/campaigns/{campaign_id}/pause`

**Response:**
```json
{
  "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "paused",
  "message": "Campaign 'Summer Sale 2025' paused"
}
```

**Database Changes:**
- Updates `marketing_campaigns.status = 'paused'`
- Daily processor will skip paused campaigns

---

### 8️⃣ Resume Campaign

**Endpoint:** `POST /marketing/campaigns/{campaign_id}/resume`

**Response:**
```json
{
  "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "active",
  "message": "Campaign 'Summer Sale 2025' resumed"
}
```

---

### 9️⃣ Cancel Campaign

**Endpoint:** `POST /marketing/campaigns/{campaign_id}/cancel`

**Response:**
```json
{
  "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "cancelled",
  "message": "Campaign 'Summer Sale 2025' cancelled"
}
```

**⚠️ Note:** Cancelled campaigns **cannot** be reactivated

---

## 💾 Database Storage Flow

### Campaign Lifecycle in Database

#### Stage 1: Draft Campaign
```sql
-- After POST /marketing/campaigns
INSERT INTO marketing_campaigns (
    id, name, template_name, status,
    daily_send_limit, priority, target_audience,
    total_target_customers, messages_pending
) VALUES (
    'uuid-here', 'Summer Sale', 'sale_template', 'draft',
    250, 5, '{"tier":"premium"}',
    0, 0
);
```

#### Stage 2: Recipients Added
```sql
-- After POST /marketing/campaigns/{id}/recipients
INSERT INTO campaign_recipients (
    id, campaign_id, phone_number, status
) VALUES
    ('uuid-1', 'campaign-uuid', '14694652751', 'pending'),
    ('uuid-2', 'campaign-uuid', '19453083188', 'pending'),
    -- ... 10,000 more rows
;

-- Update campaign
UPDATE marketing_campaigns
SET total_target_customers = 10000,
    messages_pending = 10000
WHERE id = 'campaign-uuid';
```

#### Stage 3: Campaign Activated
```sql
-- Update recipients with scheduled dates
UPDATE campaign_recipients
SET scheduled_send_date = '2025-01-15'
WHERE campaign_id = 'campaign-uuid'
AND id IN (/* first 250 recipients */);

UPDATE campaign_recipients
SET scheduled_send_date = '2025-01-16'
WHERE campaign_id = 'campaign-uuid'
AND id IN (/* next 250 recipients */);
-- ... repeat for 40 days

-- Create daily schedules
INSERT INTO campaign_send_schedule (
    id, campaign_id, send_date, batch_number,
    batch_size, messages_remaining, status
) VALUES
    ('uuid', 'campaign-uuid', '2025-01-15', 1, 250, 250, 'pending'),
    ('uuid', 'campaign-uuid', '2025-01-16', 1, 250, 250, 'pending'),
    -- ... 40 rows total
;

-- Update campaign status
UPDATE marketing_campaigns
SET status = 'active',
    started_at = NOW()
WHERE id = 'campaign-uuid';
```

#### Stage 4: Daily Processing
```sql
-- Get today's pending recipients
SELECT * FROM campaign_recipients
WHERE campaign_id = 'campaign-uuid'
AND status = 'pending'
AND scheduled_send_date = CURRENT_DATE
LIMIT 250;

-- After sending each message
UPDATE campaign_recipients
SET status = 'queued',
    whatsapp_message_id = 'wamid.xxx',
    sent_at = NOW(),
    updated_at = NOW()
WHERE id = 'recipient-uuid';

-- Trigger automatically updates campaign counts
-- (see trigger_update_campaign_stats)

-- Create daily analytics
INSERT INTO campaign_analytics (
    campaign_id, date,
    messages_sent, messages_delivered, messages_read,
    delivery_rate, read_rate
) VALUES (
    'campaign-uuid', CURRENT_DATE,
    250, 0, 0,
    0.0, 0.0
) ON CONFLICT (campaign_id, date)
DO UPDATE SET messages_sent = 250;
```

#### Stage 5: Status Updates (Webhooks)
```sql
-- When message is delivered (from WhatsApp webhook)
UPDATE campaign_recipients
SET status = 'delivered',
    delivered_at = NOW()
WHERE whatsapp_message_id = 'wamid.xxx';

-- When message is read
UPDATE campaign_recipients
SET status = 'read',
    read_at = NOW()
WHERE whatsapp_message_id = 'wamid.xxx';

-- Triggers automatically update campaign stats
```

---

## 📊 Complete Step-by-Step Example

### Scenario: Send 10,000 promotional messages

#### Step 1: Create Campaign
```bash
POST /api/marketing/campaigns
```

```json
{
  "name": "New Year Sale 2025",
  "description": "50% off everything",
  "template_name": "new_year_promo",
  "language_code": "en_US",
  "daily_send_limit": 250,
  "priority": 5,
  "target_audience": {
    "customer_tier": "premium",
    "tags": ["fashion"]
  }
}
```

**Database After Step 1:**
```
marketing_campaigns:
  id: abc123
  name: "New Year Sale 2025"
  status: "draft"
  total_target_customers: 0
  messages_pending: 0
```

---

#### Step 2: Add Recipients (Auto-select)
```bash
POST /api/marketing/campaigns/abc123/recipients?use_target_audience=true
```

**What Happens:**
1. Queries `user_profiles` for subscribed premium customers with "fashion" tag
2. Finds 10,000 matching customers
3. Inserts 10,000 rows into `campaign_recipients`

**Database After Step 2:**
```
campaign_recipients: (10,000 rows)
  Row 1: campaign_id=abc123, phone="14694652751", status="pending", scheduled_send_date=NULL
  Row 2: campaign_id=abc123, phone="19453083188", status="pending", scheduled_send_date=NULL
  ... 9,998 more rows

marketing_campaigns:
  id: abc123
  status: "draft"
  total_target_customers: 10000
  messages_pending: 10000
```

---

#### Step 3: Activate Campaign
```bash
POST /api/marketing/campaigns/abc123/activate?start_date=2025-01-15
```

**What Happens:**
1. Calculates: 10,000 ÷ 250 = 40 days needed
2. Assigns scheduled_send_date to all recipients:
   - Recipients 1-250: 2025-01-15
   - Recipients 251-500: 2025-01-16
   - ... and so on
3. Creates 40 schedule entries
4. Activates campaign

**Database After Step 3:**
```
campaign_recipients: (10,000 rows updated)
  Rows 1-250:    scheduled_send_date = '2025-01-15'
  Rows 251-500:  scheduled_send_date = '2025-01-16'
  Rows 501-750:  scheduled_send_date = '2025-01-17'
  ... 40 days total

campaign_send_schedule: (40 rows created)
  Row 1: send_date='2025-01-15', batch_size=250, status='pending'
  Row 2: send_date='2025-01-16', batch_size=250, status='pending'
  ... 40 rows total

marketing_campaigns:
  status: "active"
  started_at: 2025-01-10T10:00:00
```

---

#### Step 4: Daily Processing (Day 1: Jan 15)

**Scheduled Job Runs:**
```bash
POST /api/marketing/process-daily
```

**What Happens:**
1. Queries schedule: "Get schedules for 2025-01-15"
2. Finds 1 schedule for campaign abc123
3. Queries recipients: "Get 250 pending recipients for Jan 15"
4. For each recipient:
   - Check if still subscribed
   - Send template message via WhatsApp API
   - Update status to 'queued'

**Database After Day 1:**
```
campaign_recipients:
  Rows 1-250 (sent):
    status: "queued"
    whatsapp_message_id: "wamid.xxx"
    sent_at: 2025-01-15T09:00:00
  
  Rows 251-10000 (still pending):
    status: "pending"
    scheduled_send_date: (future dates)

marketing_campaigns:
  messages_sent: 250
  messages_pending: 9750
  (trigger auto-updated these counts)

campaign_analytics: (new row)
  campaign_id: abc123
  date: 2025-01-15
  messages_sent: 250
  messages_delivered: 0 (will update via webhooks)
```

---

#### Step 5: WhatsApp Status Updates (via Webhooks)

**As messages are delivered:**
```
WhatsApp → Webhook → Updates campaign_recipients status
```

**Database Updates:**
```
campaign_recipients:
  Row 1: status="delivered", delivered_at=2025-01-15T09:05:00
  Row 2: status="delivered", delivered_at=2025-01-15T09:05:12
  ... more updates as they happen

marketing_campaigns: (trigger auto-updates)
  messages_sent: 250
  messages_delivered: 240 (updating in real-time)
  messages_read: 180 (as customers read messages)
  messages_pending: 9750
```

---

#### Step 6-45: Continue Daily Processing

**Day 2 (Jan 16):** Send next 250  
**Day 3 (Jan 17):** Send next 250  
...  
**Day 40 (Feb 23):** Send final 250

**Final Database State:**
```
campaign_recipients: (10,000 rows)
  9,800 rows: status="read" or "delivered"
  150 rows:   status="failed"
  50 rows:    status="skipped" (unsubscribed)

marketing_campaigns:
  status: "completed"
  total_target_customers: 10000
  messages_sent: 9950
  messages_delivered: 9800
  messages_read: 7500
  messages_failed: 150
  messages_pending: 0
  completed_at: 2025-02-23T09:30:00

campaign_analytics: (40 rows)
  One row per day with daily metrics
```

---

## 📈 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAMPAIGN CREATION FLOW                       │
└─────────────────────────────────────────────────────────────────┘

1. CREATE CAMPAIGN
   API Request → MarketingService.create_campaign()
                 ↓
   [marketing_campaigns] INSERT new row (status='draft')

2. ADD RECIPIENTS  
   API Request → MarketingService.add_recipients_to_campaign()
                 ↓
   Query [user_profiles] for subscribed customers
                 ↓
   [campaign_recipients] INSERT 10,000 rows (status='pending')
                 ↓
   [marketing_campaigns] UPDATE (total_target_customers=10000)

3. ACTIVATE
   API Request → MarketingService.activate_campaign()
                 ↓
   Calculate schedule: 10,000 ÷ 250 = 40 days
                 ↓
   [campaign_recipients] UPDATE scheduled_send_date for all rows
                 ↓
   [campaign_send_schedule] INSERT 40 rows (one per day)
                 ↓
   [marketing_campaigns] UPDATE (status='active')

┌─────────────────────────────────────────────────────────────────┐
│                     DAILY PROCESSING FLOW                        │
└─────────────────────────────────────────────────────────────────┘

4. DAILY PROCESSOR (Scheduled Job)
   Cron/Scheduler → MarketingService.process_daily_campaigns()
                    ↓
   Query [campaign_send_schedule] WHERE send_date=TODAY
                    ↓
   Query [campaign_recipients] (250 pending for today)
                    ↓
   For each recipient:
     ├─ Check [user_profiles] subscription status
     ├─ Send message via WhatsApp API
     ├─ [campaign_recipients] UPDATE status='queued'
     └─ [whatsapp_messages] INSERT new message record
                    ↓
   [marketing_campaigns] AUTO-UPDATE via trigger
                    ↓
   [campaign_analytics] INSERT/UPDATE daily metrics

┌─────────────────────────────────────────────────────────────────┐
│                   STATUS UPDATE FLOW (Webhooks)                  │
└─────────────────────────────────────────────────────────────────┘

5. WHATSAPP WEBHOOKS
   WhatsApp → Webhook Handler
              ↓
   [campaign_recipients] UPDATE status='delivered'/'read'
              ↓
   [marketing_campaigns] AUTO-UPDATE via trigger
              ↓
   [campaign_analytics] UPDATE metrics

┌─────────────────────────────────────────────────────────────────┐
│                        QUERY FLOW                                │
└─────────────────────────────────────────────────────────────────┘

6. GET STATS
   API Request → MarketingService.get_campaign_stats()
                 ↓
   Query [marketing_campaigns] (pre-calculated counts)
                 ↓
   Return real-time statistics
```

---

## 🎓 Key Concepts

### 1. Duplicate Prevention

**How it works:**
- `campaign_recipients` has UNIQUE constraint on (campaign_id, phone_number)
- Attempting to add same phone number twice will be silently skipped
- This ensures no customer receives the same campaign message twice

**Database Constraint:**
```sql
CONSTRAINT unique_campaign_recipient 
UNIQUE (campaign_id, phone_number)
```

---

### 2. Rate Limiting

**How it works:**
- Campaign has `daily_send_limit` (default 250)
- During activation, recipients are divided into daily batches
- Each batch gets a specific `scheduled_send_date`
- Daily processor only sends messages scheduled for today

**Example:**
```
10,000 recipients ÷ 250/day = 40 days

Day 1:  Recipients 1-250    → scheduled_send_date = Jan 15
Day 2:  Recipients 251-500  → scheduled_send_date = Jan 16
...
Day 40: Recipients 9751-10000 → scheduled_send_date = Feb 23
```

---

### 3. Subscription Respect

**Double-check mechanism:**

**Check 1:** When adding recipients (use_target_audience=true)
```sql
SELECT whatsapp_phone FROM user_profiles
WHERE subscription = 'subscribed'
AND is_active = true
AND ... (target audience filters)
```

**Check 2:** Before sending each message
```python
is_subscribed = user_repo.is_user_subscribed(phone_number)
if not is_subscribed:
    skip_recipient(status='skipped', reason='User unsubscribed')
```

This double-check ensures:
- Campaign respects current subscription status
- Users who unsubscribe after campaign creation won't receive messages

---

### 4. Auto-updating Statistics

**Trigger mechanism:**

When `campaign_recipients.status` changes:
```sql
CREATE TRIGGER trigger_update_campaign_stats
AFTER UPDATE OF status ON campaign_recipients
FOR EACH ROW
EXECUTE FUNCTION update_campaign_stats();
```

The trigger recounts all recipient statuses and updates `marketing_campaigns`:
- messages_sent = COUNT(status IN ['sent', 'delivered', 'read'])
- messages_delivered = COUNT(status IN ['delivered', 'read'])
- messages_read = COUNT(status = 'read')
- messages_failed = COUNT(status = 'failed')
- messages_pending = COUNT(status = 'pending')

This means campaign statistics are **always up-to-date** without manual updates!

---

## ⚙️ Setting Up Daily Processing

The daily processor **must** be called by a scheduled job. Here are options:

### Option 1: AWS EventBridge (Recommended for AWS)
```yaml
# CloudFormation/Terraform
ScheduleRule:
  Type: AWS::Events::Rule
  Properties:
    ScheduleExpression: "cron(0 9 * * ? *)"  # 9 AM UTC daily
    Targets:
      - Arn: !GetAtt MyLambdaFunction.Arn
        Input: |
          {
            "endpoint": "/api/marketing/process-daily",
            "method": "POST"
          }
```

### Option 2: Cron Job (Linux Server)
```bash
# crontab -e
0 9 * * * curl -X POST https://your-domain.com/api/marketing/process-daily
```

### Option 3: Node.js Scheduler
```javascript
const cron = require('node-cron');

// Run daily at 9 AM
cron.schedule('0 9 * * *', async () => {
  try {
    await axios.post('http://localhost:8000/api/marketing/process-daily');
    console.log('✅ Daily campaigns processed');
  } catch (error) {
    console.error('❌ Error processing campaigns:', error);
  }
});
```

---

## 🚀 Best Practices

### 1. Campaign Planning

**DO:**
- ✅ Test template with 5-10 users first (small campaign)
- ✅ Set realistic daily_send_limit (250 is safe for WhatsApp)
- ✅ Use target_audience filters to segment customers
- ✅ Schedule campaigns during business hours

**DON'T:**
- ❌ Send to ALL customers without segmentation
- ❌ Exceed 250 messages/day (WhatsApp may block)
- ❌ Activate campaign without testing template
- ❌ Send campaigns at night/weekends

---

### 2. Recipient Management

**DO:**
- ✅ Use `use_target_audience=true` for automatic selection
- ✅ Verify subscription status before activating
- ✅ Export recipient list for records

**DON'T:**
- ❌ Add manually without checking subscriptions
- ❌ Activate campaign with 0 recipients
- ❌ Try to add same recipient twice (constraint prevents this)

---

### 3. Monitoring

**DO:**
- ✅ Check campaign stats daily: `GET /campaigns/{id}/stats`
- ✅ Monitor failed messages and investigate
- ✅ Review campaign_analytics for insights
- ✅ Set up alerts for high failure rates

**DON'T:**
- ❌ Ignore failed messages
- ❌ Forget to monitor delivery rates
- ❌ Leave campaigns in 'paused' state indefinitely

---

### 4. Template Design

**DO:**
- ✅ Use approved WhatsApp templates only
- ✅ Include opt-out instructions
- ✅ Personalize with customer name/data
- ✅ Keep messages concise and clear

**DON'T:**
- ❌ Send promotional content to STOP users
- ❌ Use templates not approved by WhatsApp
- ❌ Send same message repeatedly

---

## 📊 Monitoring Queries

### Check Campaign Progress
```sql
SELECT 
  name,
  status,
  total_target_customers,
  messages_sent,
  messages_pending,
  ROUND(messages_sent::decimal / total_target_customers * 100, 2) as progress_pct
FROM marketing_campaigns
WHERE status = 'active';
```

### Check Today's Schedule
```sql
SELECT 
  c.name,
  s.send_date,
  s.batch_size,
  s.messages_sent,
  s.status
FROM campaign_send_schedule s
JOIN marketing_campaigns c ON s.campaign_id = c.id
WHERE s.send_date = CURRENT_DATE;
```

### Check Failed Sends
```sql
SELECT 
  r.phone_number,
  r.failure_reason,
  r.retry_count,
  r.failed_at
FROM campaign_recipients r
WHERE r.campaign_id = 'your-campaign-id'
AND r.status = 'failed';
```

### Check Unsubscribed Users in Campaign
```sql
SELECT 
  r.phone_number,
  r.status,
  u.subscription
FROM campaign_recipients r
JOIN user_profiles u ON r.phone_number = u.whatsapp_phone
WHERE r.campaign_id = 'your-campaign-id'
AND u.subscription = 'unsubscribed';
```

---

## 🔧 Troubleshooting

### Campaign Not Sending

**Check:**
1. Is campaign status 'active'? `SELECT status FROM marketing_campaigns WHERE id = ?`
2. Is scheduled_send_date today? `SELECT COUNT(*) FROM campaign_recipients WHERE scheduled_send_date = CURRENT_DATE`
3. Are there pending recipients? `SELECT COUNT(*) FROM campaign_recipients WHERE status = 'pending'`
4. Is daily processor running? Check logs for "process_daily"

---

### High Failure Rate

**Check:**
1. Template approved by WhatsApp?
2. Users still subscribed? Query subscription status
3. Phone numbers valid format? Must be international format
4. WhatsApp API credentials working? Test with single message

---

### Recipients Not Added

**Check:**
1. Are users subscribed? `SELECT COUNT(*) FROM user_profiles WHERE subscription = 'subscribed'`
2. Do users match target_audience? Check filters
3. Duplicate recipients? UNIQUE constraint prevents duplicates

---

## 📝 Summary

### Campaign Lifecycle
```
DRAFT → (add recipients) → DRAFT → (activate) → ACTIVE → (daily processing) → COMPLETED
```

### Key Tables
1. **marketing_campaigns** - Campaign master data
2. **campaign_recipients** - Individual recipient tracking (prevents duplicates)
3. **campaign_send_schedule** - Daily batch management (enforces rate limits)
4. **campaign_analytics** - Daily performance metrics

### Critical Features
- ✅ Duplicate prevention via UNIQUE constraint
- ✅ Rate limiting via scheduled sends
- ✅ Subscription respect via double-check
- ✅ Real-time stats via database triggers

### Automation Required
- 🤖 Daily scheduler to call `/marketing/process-daily`
- 🤖 WhatsApp webhooks to update delivery status

---

**Your marketing campaign system is production-ready and designed to safely scale to hundreds of thousands of messages!** 🚀
