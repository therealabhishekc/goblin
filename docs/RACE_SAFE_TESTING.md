# 🧪 Race-Safe Testing Guide
## Testing WhatsApp Webhook Race Condition Prevention

This guide provides comprehensive testing strategies to validate that race conditions have been eliminated from the WhatsApp webhook processing system.

## 📊 System Overview

The race-safe implementation uses:
- **Atomic DynamoDB operations** for message deduplication
- **SQS visibility timeouts** for processor coordination  
- **Unique processor ownership** to prevent conflicts
- **Conditional updates** to ensure data consistency

## 🏃‍♂️ Quick Start Testing

### 1. Start the Race-Safe Application
```bash
cd /Users/abskchsk/Documents/govindjis/wa-app/backend
python start.py
```

### 2. Verify Health Check
```bash
curl http://localhost:8080/health/detailed
```

Expected response shows all components as healthy:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "dynamodb": "connected",
    "sqs": "connected", 
    "message_processor": "running"
  },
  "processor": {
    "id": "uuid-here",
    "status": "running",
    "processed_count": 0,
    "errors_count": 0
  }
}
```

## 🔬 Race Condition Testing Scenarios

### Scenario 1: Duplicate Webhook Prevention
**Objective**: Verify that duplicate webhook messages are rejected

```bash
# Send same message twice rapidly
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "id": "page_id", 
      "changes": [{
        "value": {
          "messages": [{
            "id": "test_msg_001",
            "from": "1234567890",
            "text": {"body": "Test message"},
            "timestamp": "1642248600"
          }]
        }
      }]
    }]
  }'

# Send identical message again immediately
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "id": "page_id",
      "changes": [{
        "value": {
          "messages": [{
            "id": "test_msg_001",
            "from": "1234567890", 
            "text": {"body": "Test message"},
            "timestamp": "1642248600"
          }]
        }
      }]
    }]
  }'
```

**Expected Result**: 
- First request: HTTP 200, message queued
- Second request: HTTP 200, but message marked as duplicate in logs

### Scenario 2: Concurrent Processor Safety
**Objective**: Test multiple processors don't process same message

1. **Start multiple processor instances**:
```bash
# Terminal 1
python -c "
from app.workers.message_processor import MessageProcessor
import asyncio
processor1 = MessageProcessor()
asyncio.run(processor1.start())
"

# Terminal 2  
python -c "
from app.workers.message_processor import MessageProcessor
import asyncio
processor2 = MessageProcessor()
asyncio.run(processor2.start())
"
```

2. **Send burst of messages**:
```bash
# Send 10 messages rapidly
for i in {1..10}; do
  curl -X POST http://localhost:8080/webhook \
    -H "Content-Type: application/json" \
    -d "{
      \"entry\": [{
        \"id\": \"page_id\",
        \"changes\": [{
          \"value\": {
            \"messages\": [{
              \"id\": \"burst_msg_${i}\",
              \"from\": \"1234567890\",
              \"text\": {\"body\": \"Burst message ${i}\"},
              \"timestamp\": \"$(date +%s)\"
            }]
          }
        }]
      }]
    }" &
done
wait
```

**Expected Result**: Each message processed by exactly one processor

### Scenario 3: Message Status Race Prevention
**Objective**: Verify status updates are atomic and conflict-free

This is tested internally by the atomic update operations in DynamoDB.

## 📈 Load Testing

### High-Frequency Webhook Testing
```bash
# Install Apache Bench if needed
brew install httpd

# Test 100 concurrent requests
ab -n 100 -c 10 -p test_payload.json -T application/json http://localhost:8080/webhook

# Create test payload file
cat > test_payload.json << 'EOF'
{
  "entry": [{
    "id": "load_test_page",
    "changes": [{
      "value": {
        "messages": [{
          "id": "RANDOM_ID_HERE", 
          "from": "1234567890",
          "text": {"body": "Load test message"},
          "timestamp": "1642248600"
        }]
      }
    }]
  }]
}
EOF
```

### Sustained Load Testing
```bash
# 10-minute sustained load test
timeout 600 bash -c 'while true; do
  MSG_ID="load_$(date +%s%N)"
  curl -X POST http://localhost:8080/webhook \
    -H "Content-Type: application/json" \
    -d "{
      \"entry\": [{
        \"id\": \"sustained_page\", 
        \"changes\": [{
          \"value\": {
            \"messages\": [{
              \"id\": \"${MSG_ID}\",
              \"from\": \"1234567890\",
              \"text\": {\"body\": \"Sustained message\"},
              \"timestamp\": \"$(date +%s)\"
            }]
          }
        }]
      }]
    }"
  sleep 0.1
done'
```

## 🔍 Monitoring & Validation

### 1. Check DynamoDB for Duplicates
```bash
# Query DynamoDB directly to verify no duplicates
aws dynamodb scan --table-name whatsapp-dedup-prod --region us-east-1
```

### 2. Monitor SQS Queue Metrics
```bash
# Check queue depth and message statistics
aws sqs get-queue-attributes \
  --queue-url $INCOMING_QUEUE_URL \
  --attribute-names All
```

### 3. Application Logs Analysis
```bash
# Monitor for race condition indicators
tail -f app.log | grep -E "(duplicate|race|conflict|error)"
```

### 4. Health Check Monitoring
```bash
# Continuous health monitoring
watch -n 5 'curl -s http://localhost:8080/health/detailed | jq'
```

## 🚨 Error Scenarios to Test

### Network Failure During Processing
1. Start message processing
2. Disconnect network temporarily
3. Verify message visibility timeout prevents duplicate processing
4. Reconnect network
5. Verify message is reprocessed by available processor

### Processor Crash Simulation
1. Start processor and begin message processing
2. Kill processor mid-processing (`kill -9 <pid>`)
3. Verify message becomes available for retry after visibility timeout
4. Start new processor
5. Verify message is reprocessed successfully

### DynamoDB Temporary Unavailability
1. Block DynamoDB access (network rules or credentials)
2. Send webhook messages
3. Verify graceful error handling
4. Restore DynamoDB access
5. Verify system recovers and processes queued messages

## ✅ Success Criteria

The race-safe implementation passes testing when:

1. **Zero Duplicates**: No message is ever processed more than once
2. **Atomic Operations**: All DynamoDB updates are atomic and consistent
3. **Processor Safety**: Multiple processors never conflict on same message
4. **Graceful Recovery**: System recovers properly from failures
5. **Performance**: Webhook responses remain under 5 seconds
6. **Monitoring**: All health checks report accurate system status

## 🐛 Common Issues & Solutions

### Issue: Messages stuck in processing state
**Solution**: Check processor visibility timeout extension

### Issue: High duplicate detection rate  
**Solution**: Verify webhook sender isn't retrying unnecessarily

### Issue: Processors fighting for messages
**Solution**: Confirm SQS visibility timeout is sufficient

### Issue: DynamoDB throttling
**Solution**: Check table capacity and implement exponential backoff

## 📊 Performance Benchmarks

Target performance metrics:
- **Webhook Response Time**: < 5 seconds (99th percentile)
- **Message Processing Rate**: > 100 messages/second per processor
- **Duplicate Detection**: > 99.9% accuracy
- **Error Rate**: < 0.1% permanent failures
- **Recovery Time**: < 30 seconds after failure

Run these tests regularly to ensure race condition prevention remains effective as the system scales.