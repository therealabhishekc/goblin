# S3 Configuration for WhatsApp Business API

## Environment Variables Required

Add these environment variables to your application:

```bash
# S3 Configuration
export S3_DATA_BUCKET="whatsapp-data-development-123456789"  # Replace with actual bucket name
export AWS_REGION="us-east-1"

# For local development (if not using IAM role)
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

## CloudFormation Output Integration

After deploying your CloudFormation stack, get the bucket name:

```bash
# Get S3 bucket name from CloudFormation
aws cloudformation describe-stacks \
  --stack-name wa-app-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`S3DataBucket`].OutputValue' \
  --output text
```

## Testing S3 Connection

Run the test script to validate your S3 setup:

```bash
cd backend
python test_s3_connection.py
```

## API Endpoints Available

Once S3 is connected, these endpoints will be available:

- `GET /api/v1/archive/messages` - Retrieve archived messages
- `GET /api/v1/archive/conversations/{phone_number}` - Get conversation history
- `GET /api/v1/archive/media/{message_id}` - Retrieve archived media
- `GET /api/v1/archive/stats` - Get storage statistics
- `POST /api/v1/archive/test-connection` - Test S3 connection

## Manual Setup Steps

1. **Deploy CloudFormation stack** (creates S3 bucket)
2. **Set environment variables** (S3_DATA_BUCKET, AWS_REGION)
3. **Run test script** to validate connection
4. **Set up archival schedule** (cron job or AWS Lambda)

## Current Status

❌ **Issues to Fix:**
- S3_DATA_BUCKET environment variable not configured
- Archival service not scheduled to run automatically
- No integration tests for archive/retrieval workflow

✅ **Ready Components:**
- S3 bucket created via CloudFormation
- IAM permissions configured
- Archival service implemented
- Retrieval service implemented
- API endpoints created
