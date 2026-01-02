# Response Time Calculation Flow

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    CUSTOMER INTERACTION                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  📱 Customer sends WhatsApp message                              │
│     Timestamp: 10:00:00 AM                                       │
│     From: +917829844548                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  💾 Stored in whatsapp_messages table                            │
│     - direction: "incoming"                                      │
│     - from_phone: "917829844548"                                 │
│     - timestamp: 2026-01-02 10:00:00                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  🤖 System processes and generates response                      │
│     Processing time: ~5 seconds                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  📤 System sends WhatsApp response                               │
│     Timestamp: 10:05:00 AM                                       │
│     To: +917829844548                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  💾 Stored in whatsapp_messages table                            │
│     - direction: "outgoing"                                      │
│     - to_phone: "917829844548"                                   │
│     - timestamp: 2026-01-02 10:05:00                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  📊 Update business_metrics.total_responses_sent                 │
│     Increment counter for today                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ⏱️  Calculate Response Time (NEW!)                              │
│                                                                   │
│  1. Query all incoming messages for today                        │
│  2. For each incoming message:                                   │
│     - Find first outgoing to same phone number                   │
│     - Calculate: outgoing.timestamp - incoming.timestamp         │
│  3. Average all time differences                                 │
│  4. Update business_metrics.response_time_avg_seconds            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ✅ Complete                                                      │
│     Response Time: 300 seconds (5 minutes)                       │
└─────────────────────────────────────────────────────────────────┘
```

## Example Calculation for a Full Day

```
Day: 2026-01-02

Conversation 1:
  Incoming:  10:00:00 AM (Customer A)
  Outgoing:  10:05:00 AM
  Difference: 5 minutes = 300 seconds

Conversation 2:
  Incoming:  11:30:00 AM (Customer B)
  Outgoing:  11:32:00 AM
  Difference: 2 minutes = 120 seconds

Conversation 3:
  Incoming:  02:00:00 PM (Customer C)
  Outgoing:  02:15:00 PM
  Difference: 15 minutes = 900 seconds

Conversation 4:
  Incoming:  04:00:00 PM (Customer D)
  Outgoing:  04:01:00 PM
  Difference: 1 minute = 60 seconds

Average Response Time = (300 + 120 + 900 + 60) / 4 = 345 seconds
                      = 5.75 minutes

business_metrics table update:
  date: 2026-01-02
  response_time_avg_seconds: 345.0
```

## Database Query Logic

```sql
-- Step 1: Get all incoming messages for the day
SELECT * FROM whatsapp_messages 
WHERE direction = 'incoming'
  AND timestamp >= '2026-01-02 00:00:00'
  AND timestamp < '2026-01-03 00:00:00'
ORDER BY timestamp;

-- Step 2: For each incoming message, find the first outgoing response
SELECT * FROM whatsapp_messages
WHERE direction = 'outgoing'
  AND to_phone = :customer_phone  -- from incoming message
  AND timestamp > :incoming_timestamp
  AND timestamp < :incoming_timestamp + INTERVAL '24 hours'
ORDER BY timestamp
LIMIT 1;

-- Step 3: Calculate average and update
UPDATE business_metrics
SET response_time_avg_seconds = :calculated_average
WHERE date = '2026-01-02';
```

## Code Flow

```python
# In outgoing_processor.py - after sending message

# 1. Store the outgoing message
message_repo.create_from_dict(message_data)

# 2. Update business metrics counter
analytics_repo.increment_responses_sent()

# 3. Calculate response time (NEW!)
analytics_repo.update_response_time_avg()
   │
   ├─> Get today's incoming messages
   ├─> For each: find matching outgoing response
   ├─> Calculate time differences
   ├─> Average the results
   └─> Update business_metrics table
```

## Key Points

1. **Automatic**: Runs every time a response is sent
2. **Accurate**: Matches conversations by phone number
3. **Efficient**: Only processes messages for current day
4. **Safe**: Handles edge cases (no messages, no responses, etc.)
5. **Flexible**: Can recalculate historical data if needed

## Metrics Available

After implementation, you'll have access to:

- **Total Messages Received**: Count of incoming messages
- **Total Responses Sent**: Count of outgoing messages  
- **Unique Users**: Number of distinct customers
- **Response Time Average**: How fast you respond (in seconds)
- **Popular Keywords**: Most common words in messages

All metrics are available via the API at `/metrics/date/{date}` or `/metrics/summary`
