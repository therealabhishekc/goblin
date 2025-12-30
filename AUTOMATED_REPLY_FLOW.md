# Automated Reply System - Flow Analysis

## Current State: NO DELAYS - Replies Are Immediate

### How Automated Replies Work

1. **Message Received** (Webhook)
   - WhatsApp sends webhook → FastAPI endpoint
   - Message queued in **INCOMING** SQS queue

2. **Message Processor** (background worker)
   - Picks up message from INCOMING queue
   - Stores in database
   - Calls `reply_automation.process_incoming_message()`
   - Reply immediately queued in **OUTGOING** SQS queue

3. **Outgoing Processor** (background worker)
   - Picks up reply from OUTGOING queue
   - Sends via WhatsApp API
   - Updates database

### Flow Diagram
```
User → WhatsApp → Webhook → INCOMING Queue
                               ↓
                         Message Processor
                               ↓
                    Reply Automation Engine
                               ↓
                         OUTGOING Queue
                               ↓
                      Outgoing Processor
                               ↓
                    WhatsApp API → User
```

**Total Time: Typically 1-5 seconds**

---

## Why Replies Might SEEM Delayed

### 1. SQS Long Polling (Main Cause)
- **Outgoing processor** waits up to **20 seconds** for new messages (efficiency optimization)
- If queue is empty when reply arrives, processor is "sleeping"
- Reply sent when processor wakes up

**Solution**: Reduce wait time from 20 to 5 seconds

### 2. Visibility Timeout
- Messages have 5-15 minute visibility timeouts
- If processor crashes, message locked for this duration
- Prevents duplicate processing but delays retries

### 3. Processing Order
- Multiple messages processed concurrently
- Not guaranteed FIFO unless using FIFO queues

### 4. Rate Limiting
- WhatsApp API rate limits (80 messages/second)
- High volume causes natural queueing

---

## Automated Reply Rules (Priority Order)

### STOP/START Commands (Priority: 20)
- **STOP**: Unsubscribes from marketing templates
- **START**: Resubscribes to marketing templates
- Response: Immediate confirmation message

### Greetings (Priority: 10)
- **Hi/Hello/Hey**: Welcome message
- **Good morning**: Morning greeting

### FAQ Auto-Responses (Priority: 6-8)
- **Hours/Open/Close**: Business hours info
- **Price/Cost**: Pricing information
- **Support/Help**: Support guidance
- **Contact**: Contact information

### Fallback (Priority: 0)
- Matches any message not caught by other rules
- Generic acknowledgment

---

## Campaign Messages vs Automated Replies

### Campaign Messages (Marketing)
- **Scheduled**: Processed daily by EventBridge (every 5 mins for testing)
- **Rate Limited**: 250 messages/day per campaign
- **Subscription Required**: Only sent to subscribed users
- **Type**: Template messages

### Automated Replies (Customer Service)
- **Immediate**: Sent as soon as message received
- **No Rate Limit**: Always responds
- **No Subscription Check**: Works for all users
- **Type**: Text/template messages

---

## Monitoring & Debugging

### Check Processing Status

1. **AWS CloudWatch Logs**
   - App Runner service logs for main application
   - Look for: `"✅ Auto-reply sent"` or `"❌ Error"`

2. **SQS Queue Metrics**
   - Incoming queue: Should be empty or low
   - Outgoing queue: Should be empty or low
   - High queue depth = processing lag

3. **Database**
   ```sql
   -- Check message status
   SELECT message_id, content, status, direction, created_at 
   FROM whatsapp_messages 
   WHERE direction = 'incoming' 
   ORDER BY created_at DESC 
   LIMIT 10;

   -- Check for unprocessed messages
   SELECT COUNT(*) 
   FROM whatsapp_messages 
   WHERE status = 'processing' 
   AND created_at < NOW() - INTERVAL '5 minutes';
   ```

### Expected Log Flow

**Normal processing:**
```
🔄 Processing message: wamid.xxx (type: text, from: +1234567890)
✅ Message completed: wamid.xxx (time: 0.123s)
🤖 Automated reply queued for +1234567890: msg-uuid
📤 Sending message to +1234567890: template
✅ Message sent successfully to +1234567890: wamid.yyy
```

**Delayed processing (problem):**
```
🔄 Processing message: wamid.xxx
✅ Message completed: wamid.xxx
🤖 Automated reply queued for +1234567890: msg-uuid
📥 Received 0 messages for processing  ← Processor waiting
📥 Received 0 messages for processing
📥 Received 1 outgoing messages to send  ← 20+ seconds later
📤 Sending message to +1234567890
```

---

## Recommendations

### To Reduce Reply Latency

1. **Reduce Long Polling Wait Time**
   - Change from 20 seconds to 5 seconds
   - File: `backend/app/workers/message_processor.py` and `outgoing_processor.py`
   - Line: `wait_time_seconds=20` → `wait_time_seconds=5`

2. **Increase Concurrent Processing**
   - More App Runner instances = more processors
   - Current: 1 instance = 1 processor
   - Recommended: 2-3 instances for redundancy

3. **Monitor Queue Depth**
   - Set CloudWatch alarms for queue depth > 10
   - Indicates processing lag

4. **Use FIFO Queues (Optional)**
   - Guarantees message ordering
   - Slightly higher latency but more predictable

### To Debug Delays

1. **Enable Detailed Logging**
   ```python
   # Add timestamps to critical steps
   logger.info(f"⏱️ Step 1: Message received at {datetime.now()}")
   logger.info(f"⏱️ Step 2: Reply queued at {datetime.now()}")
   logger.info(f"⏱️ Step 3: Reply sent at {datetime.now()}")
   ```

2. **Check SQS Metrics**
   - ApproximateNumberOfMessages
   - ApproximateAgeOfOldestMessage
   - NumberOfMessagesSent/Received

3. **Verify Processor Health**
   ```bash
   # Check if processors are running
   curl http://localhost:8000/health
   ```

---

## Configuration Files

### SQS Service
- **File**: `backend/app/services/sqs_service.py`
- **Queues**: incoming, outgoing, analytics
- **Settings**: visibility_timeout, wait_time_seconds

### Message Processor
- **File**: `backend/app/workers/message_processor.py`
- **Handles**: Incoming messages
- **Calls**: Reply automation

### Outgoing Processor
- **File**: `backend/app/workers/outgoing_processor.py`
- **Handles**: Outgoing messages
- **Sends**: Via WhatsApp API

### Reply Automation
- **File**: `backend/app/services/reply_automation.py`
- **Rules**: Pattern matching for auto-replies
- **Priority**: 0-20 (higher = processed first)

---

## Summary

**✅ Automated replies are NOT delayed by design** - they are sent immediately through SQS queues.

**⚠️ Perceived delays** are due to:
1. SQS long polling (20 second wait)
2. Processing time (1-3 seconds)
3. Queue visibility timeouts on failures

**🔧 To improve**:
- Reduce long polling wait time to 5 seconds
- Monitor queue depth and age
- Add detailed timestamp logging

**📊 Current performance**:
- Best case: 1-3 seconds (immediate)
- Typical: 5-10 seconds (with long polling)
- Worst case: 60+ seconds (on retry/failure)
