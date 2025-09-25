# 🚀 Race-Safe Deployment Checklist
## Production Deployment Guide for Race Condition Prevention

This checklist ensures all race condition prevention mechanisms are properly configured for production deployment.

## 📋 Pre-Deployment Validation

### ✅ Code Implementation Status
- [x] **Atomic DynamoDB operations** implemented in `app/dynamodb_client.py`
- [x] **Race-safe webhook handler** implemented in `app/api/webhook.py`  
- [x] **Enhanced SQS service** with visibility timeout management in `app/services/sqs_service.py`
- [x] **Race-safe message processor** implemented in `app/workers/message_processor.py`
- [x] **Application lifecycle management** updated in `app/main.py`
- [x] **Comprehensive error handling** across all components
- [x] **Detailed logging and monitoring** implemented

### ✅ Infrastructure Requirements

#### DynamoDB Table Configuration
```bash
# Verify table exists with correct settings
aws dynamodb describe-table --table-name whatsapp-dedup-prod --region us-east-1

# Required table structure:
# - Partition Key: msgid (String) 
# - TTL Attribute: ttl (Number)
# - Read Capacity: 10 units minimum
# - Write Capacity: 10 units minimum
```

#### SQS Queue Configuration  
```bash
# Verify all required queues exist
aws sqs get-queue-url --queue-name whatsapp-incoming --region us-east-1
aws sqs get-queue-url --queue-name whatsapp-outgoing --region us-east-1
aws sqs get-queue-url --queue-name whatsapp-analytics --region us-east-1

# Verify Dead Letter Queues
aws sqs get-queue-url --queue-name whatsapp-incoming-dlq --region us-east-1
aws sqs get-queue-url --queue-name whatsapp-outgoing-dlq --region us-east-1
aws sqs get-queue-url --queue-name whatsapp-analytics-dlq --region us-east-1

# Required queue attributes:
# - VisibilityTimeoutSeconds: 900 (15 minutes)
# - MessageRetentionPeriod: 1209600 (14 days)
# - MaxReceiveCount: 3 (before DLQ)
# - ReceiveMessageWaitTimeSeconds: 20 (long polling)
```

## 🔧 Environment Configuration

### Critical Race-Safe Environment Variables
```bash
# Copy race-safe configuration template
cp race-safe-config.env .env

# Verify all required variables are set:
echo "Checking race-safe environment variables..."
required_vars=(
    "DYNAMODB_TABLE_NAME"
    "AWS_REGION"
    "INCOMING_QUEUE_URL"
    "OUTGOING_QUEUE_URL" 
    "ANALYTICS_QUEUE_URL"
    "INCOMING_DLQ_URL"
    "OUTGOING_DLQ_URL"
    "ANALYTICS_DLQ_URL"
    "SQS_VISIBILITY_TIMEOUT"
    "SQS_MAX_RECEIVE_COUNT"
    "SQS_WAIT_TIME_SECONDS"
)

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "❌ Missing required variable: $var"
        exit 1
    else
        echo "✅ $var is set"
    fi
done
```

### AWS IAM Permissions
Ensure the application has these minimum permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem", 
                "dynamodb:UpdateItem",
                "dynamodb:Query",
                "dynamodb:DescribeTable"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/whatsapp-dedup-prod"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sqs:ReceiveMessage",
                "sqs:SendMessage",
                "sqs:DeleteMessage",
                "sqs:ChangeMessageVisibility",
                "sqs:GetQueueAttributes"
            ],
            "Resource": [
                "arn:aws:sqs:*:*:whatsapp-*"
            ]
        }
    ]
}
```

## 🧪 Pre-Production Testing

### 1. Atomic Operation Testing
```bash
# Test DynamoDB atomic operations
python -c "
from app.dynamodb_client import DynamoDBClient
import asyncio

async def test_atomic():
    client = DynamoDBClient()
    
    # Test atomic message storage
    result1 = await client.store_message_id_atomic('test_msg_123')
    result2 = await client.store_message_id_atomic('test_msg_123')  # Should be duplicate
    
    print(f'First storage: {result1}')   # Should be True
    print(f'Duplicate storage: {result2}')  # Should be False
    
    # Test atomic claiming
    claim1 = await client.claim_message_processing('test_msg_123', 'processor_1')
    claim2 = await client.claim_message_processing('test_msg_123', 'processor_2') 
    
    print(f'First claim: {claim1}')   # Should be True
    print(f'Second claim: {claim2}')  # Should be False

asyncio.run(test_atomic())
"
```

### 2. Race Condition Simulation
```bash
# Test multiple processors racing for same message
python -c "
import asyncio
import concurrent.futures
from app.workers.message_processor import MessageProcessor

async def race_test():
    processors = [MessageProcessor() for _ in range(3)]
    
    # Start all processors concurrently
    tasks = [processor.process_next_message() for processor in processors]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print(f'Race test results: {results}')

asyncio.run(race_test())
"
```

### 3. Load Testing
```bash
# High-concurrency webhook testing
echo "Testing concurrent webhook handling..."
for i in {1..50}; do
    curl -X POST http://localhost:8080/webhook \
        -H "Content-Type: application/json" \
        -d "{
            \"entry\": [{
                \"id\": \"stress_test\",
                \"changes\": [{
                    \"value\": {
                        \"messages\": [{
                            \"id\": \"stress_msg_${i}_$(date +%s%N)\",
                            \"from\": \"1234567890\",
                            \"text\": {\"body\": \"Stress test message ${i}\"},
                            \"timestamp\": \"$(date +%s)\"
                        }]
                    }
                }]
            }]
        }" &
done
wait
echo "Load test completed"
```

## 📊 Monitoring Setup

### 1. Health Check Endpoint
```bash
# Verify detailed health check works
curl http://localhost:8080/health/detailed | jq

# Expected response structure:
# {
#   "status": "healthy",
#   "timestamp": "...",
#   "components": {
#     "dynamodb": "connected",
#     "sqs": "connected",
#     "message_processor": "running"
#   },
#   "processor": {
#     "id": "...",
#     "status": "running",
#     "processed_count": 0,
#     "errors_count": 0
#   }
# }
```

### 2. CloudWatch Metrics (Optional)
Set up monitoring for:
- DynamoDB ConditionalCheckFailedRequests (race condition attempts)
- SQS ApproximateNumberOfMessages (queue depth)
- Application response times and error rates

### 3. Alerting Thresholds
- **High duplicate rate** (>5%): May indicate webhook sender issues
- **Long processing times** (>15 minutes): May indicate processor hangs
- **High error rates** (>1%): May indicate infrastructure issues

## 🚀 Deployment Steps

### 1. Blue-Green Deployment Approach
```bash
# Deploy to staging environment first
export ENVIRONMENT=staging
python start.py

# Verify all race-safe features work
curl http://staging.example.com/health/detailed

# Run full test suite
python -m pytest tests/ -v

# Deploy to production with zero downtime
export ENVIRONMENT=production
# ... deployment commands specific to your infrastructure
```

### 2. Post-Deployment Verification
```bash
# Immediate post-deployment checks
echo "Verifying race-safe deployment..."

# Check application startup
curl http://production.example.com/ | jq

# Check health endpoints
curl http://production.example.com/health/detailed | jq

# Verify processor is running
curl http://production.example.com/health/detailed | jq '.processor.status'

# Send test webhook
curl -X POST http://production.example.com/webhook \
    -H "Content-Type: application/json" \
    -d '{
        "entry": [{
            "id": "deployment_test",
            "changes": [{
                "value": {
                    "messages": [{
                        "id": "deploy_verification_msg",
                        "from": "1234567890",
                        "text": {"body": "Deployment verification"},
                        "timestamp": "'$(date +%s)'"
                    }]
                }
            }]
        }]
    }'

echo "✅ Race-safe deployment verification complete"
```

## 🔒 Security Considerations

### 1. Environment Variable Security
```bash
# Ensure sensitive variables are properly secured
# Never expose these in logs or error messages:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY  
# - Database connection strings
# - API tokens

# Use AWS IAM roles instead of hardcoded credentials when possible
```

### 2. Rate Limiting
Consider implementing rate limiting to prevent abuse:
- Webhook endpoint: 100 requests/minute per IP
- Health check endpoints: 60 requests/minute per IP

### 3. Input Validation
All webhook inputs are validated for:
- Required fields presence
- Data type validation
- Size limits
- Malicious content detection

## ✅ Final Deployment Checklist

Before going live, ensure:

- [ ] All race-safe code changes deployed
- [ ] DynamoDB table configured with TTL
- [ ] SQS queues configured with proper visibility timeouts
- [ ] Environment variables set correctly
- [ ] IAM permissions configured
- [ ] Health checks passing
- [ ] Load testing completed successfully  
- [ ] Monitoring and alerting configured
- [ ] Rollback plan prepared
- [ ] Team trained on new race-safe features

## 📞 Emergency Procedures

### If Race Conditions Detected
1. **Immediate**: Check processor logs for conflicts
2. **Short-term**: Increase SQS visibility timeout temporarily
3. **Long-term**: Analyze root cause and implement additional safeguards

### If System Overload
1. **Scale**: Add more processor instances
2. **Throttle**: Implement request rate limiting
3. **Queue**: Increase SQS queue capacity

### Rollback Strategy
1. **Code rollback**: Previous version without race-safe features
2. **Database state**: DynamoDB entries have TTL, will self-clean
3. **Queue purge**: Clear SQS queues if needed for fresh start

## 📈 Success Metrics

Post-deployment success is measured by:
- **Zero duplicate processing** incidents
- **<5 second** webhook response times (99th percentile)  
- **>99.9%** message processing success rate
- **<30 second** recovery time from failures
- **Clean audit logs** showing proper race condition prevention

Regular monitoring of these metrics ensures the race-safe implementation continues to work effectively in production.