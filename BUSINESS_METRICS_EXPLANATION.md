# Business Metrics Table - Detailed Explanation

## Overview
The `business_metrics` table tracks daily aggregated statistics about your WhatsApp business operations.

## Table Structure

```sql
CREATE TABLE business_metrics (
    id UUID PRIMARY KEY,
    date TIMESTAMP NOT NULL UNIQUE,
    total_messages_received INT DEFAULT 0,
    total_responses_sent INT DEFAULT 0,
    unique_users INT DEFAULT 0,
    response_time_avg_seconds FLOAT,
    popular_keywords JSON,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Column Details

### 1. `total_messages_received`
- **Purpose**: Count of all incoming messages from customers for a specific day
- **Updated By**: `AnalyticsRepository.increment_messages_received()`
- **Called From**: Webhook handler when processing incoming messages
- **Location**: `backend/app/repositories/analytics_repository.py` (lines 40-62)

### 2. `total_responses_sent` ⚠️
- **Purpose**: Count of all outgoing messages (responses) sent to customers for a specific day
- **Updated By**: `AnalyticsRepository.increment_responses_sent()`
- **Called From**: 
  1. `OutgoingMessageProcessor` - when processing messages from SQS queue
     - Location: `backend/app/workers/outgoing_processor.py` (line 165)
  2. `WhatsAppService.send_message()` - when sending direct messages
     - Location: `backend/app/services/whatsapp_service.py` (line 132)

**Recent Fix Applied:**
- Changed log level from `debug` to `info` so you can see it in App Runner logs
- Added detailed logging showing the current count: `"total_responses_sent incremented to {count} for {date}"`
- Added stack trace logging (`exc_info=True`) for better error debugging

**How It Works:**
1. When a message is sent via WhatsApp API
2. After successfully storing the message in `whatsapp_messages` table
3. The `increment_responses_sent()` method is called
4. It either creates a new metrics row for today (if doesn't exist) or increments the existing count
5. Changes are committed immediately to the database

### 3. `unique_users`
- **Purpose**: Count of unique customers (distinct phone numbers) who sent messages on that day
- **Updated By**: `AnalyticsRepository.update_unique_users_count()`
- **Called From**: Typically called by a scheduled job or analytics update process
- **Calculation Method**: 
  ```python
  SELECT COUNT(DISTINCT from_phone) 
  FROM whatsapp_messages 
  WHERE DATE(timestamp) = target_date
  ```
- **Location**: `backend/app/repositories/analytics_repository.py` (lines 87-114)

### 4. `response_time_avg_seconds` ❌ NOT IMPLEMENTED
- **Purpose**: Average time taken to respond to customer messages
- **Current Status**: Column exists but **NO LOGIC** populates this field
- **Value**: Always NULL
- **Why Not Implemented**: Would require:
  1. Tracking when a customer message is received
  2. Tracking when the first response is sent
  3. Calculating the time difference
  4. Averaging across all conversations for the day

### 5. `popular_keywords`
- **Purpose**: Store frequently used keywords/phrases from customer messages
- **Data Type**: JSON object (e.g., `{"hello": 50, "order": 30}`)
- **Current Status**: Column exists but tracking logic not visible in the reviewed code

### 6. `date`
- **Purpose**: Date identifier for the metrics (set to midnight UTC)
- **Format**: `YYYY-MM-DD 00:00:00`
- **Unique**: Each day has exactly one row

## Data Flow for `total_responses_sent`

### Scenario 1: Regular Automated Responses
```
Customer Message
    ↓
Webhook receives message
    ↓
AI processes and generates response
    ↓
Response sent to SQS outgoing queue
    ↓
OutgoingMessageProcessor picks up message
    ↓
Sends via WhatsApp API
    ↓
Stores in whatsapp_messages table
    ↓
Calls analytics_repo.increment_responses_sent() ← INCREMENTS COUNTER
    ↓
Logs: "📊 Business metrics updated: total_responses_sent incremented to X for YYYY-MM-DD"
```

### Scenario 2: Campaign Messages
```
Campaign scheduled for today
    ↓
Lambda/API calls process_daily_campaigns()
    ↓
Gets pending recipients
    ↓
Sends messages to SQS outgoing queue
    ↓
OutgoingMessageProcessor picks up messages
    ↓
Sends via WhatsApp API
    ↓
Stores in whatsapp_messages table
    ↓
Calls analytics_repo.increment_responses_sent() ← INCREMENTS COUNTER
    ↓
Also updates campaign_recipients table with sent status
```

## How to Verify It's Working

After the deployment completes, check App Runner logs for messages like:

```
✅ Message sent successfully to 917XXXXXXXX
📊 Business metrics updated: total_responses_sent incremented to 15 for 2026-01-02
```

If you see errors like:
```
❌ Failed to update business metrics: <error details>
```

Then there's an actual problem that needs investigation.

## Common Issues

### Issue: Counter Not Incrementing
**Possible Causes:**
1. Messages not actually being sent (check for send errors in logs)
2. Database transaction issues (rolled back before commit)
3. Silent exceptions being caught (check error logs)

**Debugging Steps:**
1. Check App Runner logs for "📊 Business metrics updated" messages
2. Look for "❌ Failed to update business metrics" error messages
3. Verify messages are actually being sent (check WhatsApp message logs)
4. Query the database directly to see if rows exist

### Issue: Counter Shows Wrong Number
**Possible Causes:**
1. Multiple instances of the processor running simultaneously (should be OK due to atomic increments)
2. Messages counted multiple times due to SQS retries (shouldn't happen as we delete after success)

## Database Query Examples

### Get today's metrics:
```sql
SELECT * FROM business_metrics 
WHERE date = CURRENT_DATE 
ORDER BY date DESC;
```

### Get last 7 days:
```sql
SELECT 
    date,
    total_messages_received,
    total_responses_sent,
    unique_users
FROM business_metrics 
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC;
```

### Get totals:
```sql
SELECT 
    SUM(total_messages_received) as total_received,
    SUM(total_responses_sent) as total_sent,
    AVG(unique_users) as avg_daily_users
FROM business_metrics;
```

## Code Locations Reference

| Metric | Repository Method | Called From | Line Numbers |
|--------|------------------|-------------|--------------|
| `total_messages_received` | `increment_messages_received()` | Webhook handler | analytics_repository.py:40-62 |
| `total_responses_sent` | `increment_responses_sent()` | OutgoingProcessor, WhatsAppService | analytics_repository.py:64-85<br>outgoing_processor.py:165<br>whatsapp_service.py:132 |
| `unique_users` | `update_unique_users_count()` | Analytics job | analytics_repository.py:87-114 |

## Recent Changes (2026-01-02)

✅ **Improved Logging for `total_responses_sent`:**
- Changed from `logger.debug()` to `logger.info()` 
- Added current count value in log message
- Added full stack traces for errors
- Both locations (OutgoingProcessor and WhatsAppService) now have enhanced logging

This will help you see in real-time when the counter is being incremented and troubleshoot any issues.
