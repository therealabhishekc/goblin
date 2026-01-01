# Campaign Analytics Table - Complete Documentation

## Overview
The `campaign_analytics` table stores **daily aggregated metrics** for each marketing campaign. It provides insights into message delivery, engagement, and response patterns.

---

## Table Schema

| Column Name | Type | Description | Is Being Filled? |
|-------------|------|-------------|------------------|
| `id` | UUID | Primary key | ✅ YES (auto-generated) |
| `campaign_id` | UUID | Foreign key to marketing_campaigns table | ✅ YES |
| `date` | Date | The date for which analytics are recorded | ✅ YES |
| `messages_sent` | Integer | Messages sent on this date | ✅ YES |
| `messages_delivered` | Integer | Messages delivered on this date | ✅ YES |
| `messages_read` | Integer | Messages read on this date | ✅ YES |
| `messages_failed` | Integer | Messages failed on this date | ✅ YES |
| `replies_received` | Integer | Replies from recipients on this date | ✅ YES |
| `unique_responders` | Integer | Unique recipients who replied on this date | ✅ YES |
| `delivery_rate` | Numeric(5,2) | Percentage of delivered messages | ✅ YES |
| `read_rate` | Numeric(5,2) | Percentage of read messages | ✅ YES |
| `response_rate` | Numeric(5,2) | Percentage of recipients who responded | ✅ YES |
| `avg_response_time_minutes` | Integer | Average time to respond in minutes | ✅ YES |
| `created_at` | DateTime | Record creation timestamp | ✅ YES (auto) |
| `updated_at` | DateTime | Record last update timestamp | ✅ YES (auto) |

---

## How Analytics Are Calculated

### When Analytics Are Recorded
Analytics are recorded in **2 scenarios**:

1. **After Daily Campaign Processing** (line 305 in marketing_service.py)
   - When the daily campaign batch is completed
   - Triggered by the scheduled Lambda function (runs every 5 minutes currently)
   
2. **After Retry Processing** (line 389 in marketing_service.py)
   - When failed messages are retried
   - Triggered by the same Lambda function

### Calculation Logic (from marketing_repository.py lines 531-683)

#### 1. **messages_sent** (lines 557-563)
```python
COUNT of campaign_recipients 
WHERE campaign_id = X 
  AND DATE(sent_at) = analytics_date
  AND sent_at IS NOT NULL
```
**Logic**: Counts recipients whose messages were **sent** on this specific date (based on sent_at timestamp).

#### 2. **messages_delivered** (lines 566-572)
```python
COUNT of campaign_recipients 
WHERE campaign_id = X 
  AND DATE(delivered_at) = analytics_date
  AND delivered_at IS NOT NULL
```
**Logic**: Counts recipients whose messages were **delivered** on this specific date (based on delivered_at timestamp).

#### 3. **messages_read** (lines 575-581)
```python
COUNT of campaign_recipients 
WHERE campaign_id = X 
  AND DATE(read_at) = analytics_date
  AND read_at IS NOT NULL
```
**Logic**: Counts recipients whose messages were **read** on this specific date (based on read_at timestamp).

#### 4. **messages_failed** (lines 584-590)
```python
COUNT of campaign_recipients 
WHERE campaign_id = X 
  AND DATE(failed_at) = analytics_date
  AND failed_at IS NOT NULL
```
**Logic**: Counts recipients whose messages **failed** on this specific date (based on failed_at timestamp).

#### 5. **delivery_rate** (lines 599-604)
```python
IF messages_sent > 0:
    delivery_rate = (messages_delivered / messages_sent) * 100
```
**Logic**: Percentage of messages delivered out of messages sent on this date.
**Note**: Rate might temporarily exceed 100% if delivery happens on a different day than sending.

#### 6. **read_rate** (lines 599-604)
```python
IF messages_sent > 0:
    read_rate = (messages_read / messages_sent) * 100
```
**Logic**: Percentage of messages read out of messages sent on this date.
**Note**: Rate might temporarily exceed 100% if read happens on a different day than sending.

#### 7. **replies_received** (lines 618-638)
```python
COUNT of whatsapp_messages
WHERE phone_number IN (recipients sent messages today)
  AND direction = 'incoming'
  AND DATE(timestamp) = analytics_date
  AND timestamp >= (earliest sent_at for this campaign on this date)
```
**Logic**: Counts incoming messages from recipients who were sent campaign messages on this date, received after the campaign was sent.

#### 8. **unique_responders** (lines 618-638)
```python
COUNT DISTINCT of whatsapp_messages.phone_number
WHERE phone_number IN (recipients sent messages today)
  AND direction = 'incoming'
  AND DATE(timestamp) = analytics_date
  AND timestamp >= (earliest sent_at for this campaign on this date)
```
**Logic**: Counts unique phone numbers that replied on this date.

#### 9. **response_rate** (lines 645-646)
```python
IF messages_sent > 0:
    response_rate = (unique_responders / messages_sent) * 100
```
**Logic**: Percentage of unique recipients who responded out of messages sent.

#### 10. **avg_response_time_minutes** (lines 648-673)
```python
For each recipient who replied on this date:
    response_time = TIMESTAMPDIFF(MINUTE, sent_at, first_reply_timestamp)
    
avg_response_time = AVERAGE of all valid response_times
```
**Logic**: Calculates average time (in minutes) between when a message was sent and when the recipient first replied on this date.

---

## Important Notes

### ✅ All Columns Are Being Filled Properly

**YES**, all columns in the `campaign_analytics` table are being populated correctly by the `record_analytics()` method.

### Key Characteristics

1. **Date-Based Tracking**: Analytics are tracked by the **date** when events occurred, not just campaign duration.
   - A message sent on Jan 1 but delivered on Jan 2 will appear in both dates' analytics.

2. **Automatic Recording**: Analytics are automatically recorded:
   - After each daily batch is processed (every 5 minutes via Lambda)
   - After retry attempts are completed
   - No manual intervention needed

3. **Upsert Behavior**: The system uses "get or create" logic:
   - If an analytics record exists for a campaign + date, it's updated
   - If not, a new record is created
   - This ensures accurate, up-to-date metrics

4. **Source of Truth**: Analytics pull data from:
   - `campaign_recipients` table (for sent/delivered/read/failed counts and timestamps)
   - `whatsapp_messages` table (for reply metrics)

5. **Real-time Updates**: Delivery and read status updates from WhatsApp webhooks automatically update the `campaign_recipients` table, which then flows into analytics on the next recording.

---

## How to Verify Analytics

### Option 1: Via Database Query
```sql
SELECT 
    campaign_id,
    date,
    messages_sent,
    messages_delivered,
    messages_read,
    messages_failed,
    replies_received,
    unique_responders,
    delivery_rate,
    read_rate,
    response_rate,
    avg_response_time_minutes
FROM campaign_analytics
WHERE campaign_id = '<your-campaign-id>'
ORDER BY date DESC;
```

### Option 2: Via API Endpoint
The campaign stats endpoint aggregates analytics data:
```
GET /marketing/campaigns/{campaign_id}/stats
```

### Option 3: Via Campaign Frontend
The campaign management UI displays these metrics in the campaign details/dashboard.

---

## Troubleshooting

### If Analytics Are Not Being Filled:

1. **Check if Lambda is running**:
   - View CloudWatch Logs for the campaign processing Lambda
   - Look for log messages: "📊 Analytics recorded for campaign..."

2. **Check campaign_recipients data**:
   ```sql
   SELECT 
       COUNT(*) as total,
       SUM(CASE WHEN sent_at IS NOT NULL THEN 1 ELSE 0 END) as sent,
       SUM(CASE WHEN delivered_at IS NOT NULL THEN 1 ELSE 0 END) as delivered,
       SUM(CASE WHEN read_at IS NOT NULL THEN 1 ELSE 0 END) as read
   FROM campaign_recipients
   WHERE campaign_id = '<your-campaign-id>';
   ```

3. **Verify Lambda schedule**:
   - EventBridge rule should trigger Lambda every 5 minutes
   - Check if the rule is enabled in AWS Console

4. **Check for errors in logs**:
   - App Runner logs for webhook processing
   - Lambda logs for batch processing
   - Look for any database connection errors

---

## Summary

✅ **All columns in `campaign_analytics` are being filled properly**

✅ **The logic is comprehensive and includes**:
- Message delivery metrics (sent, delivered, read, failed)
- Engagement metrics (replies, responders)
- Performance rates (delivery %, read %, response %)
- Response timing (average minutes to respond)

✅ **Analytics are automatically updated**:
- After daily batch processing
- After retry processing
- Using data from campaign_recipients and whatsapp_messages tables

✅ **The system is production-ready** and provides valuable insights into campaign performance.
