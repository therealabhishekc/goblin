# WhatsApp Business API - Automated Data Archival

This document describes the automated archival system for WhatsApp messages and media files using AWS Lambda functions that run every 2 days.

## Overview

The archival system consists of:
- **Message Archival Lambda**: Archives old messages from PostgreSQL to S3
- **Media Archival Lambda**: Archives media files from URLs to S3
- **EventBridge Scheduler**: Runs archival every 2 days at 2 AM and 3 AM UTC
- **Admin API**: Manual triggering and monitoring capabilities
- **CloudWatch Monitoring**: Comprehensive logging and alerting

## Architecture

```
WhatsApp Messages → PostgreSQL RDS → Lambda Archival → S3 Storage
                                   ↓
                               CloudWatch Logs & Metrics
                                   ↓
                               Admin API Monitoring
```

## Deployment

### Quick Start

1. **Deploy complete infrastructure** (includes main app + archival functions):
   ```bash
   ./deploy-github.sh production us-east-1 <github-connection-arn> <vpc-id>
   ```

2. **Test the deployment**:
   ```bash
   ./test-lambda-archival.sh
   ```

**Note**: Archival functions are now integrated into the main CloudFormation template (`infrastructure.yaml`) and deployed together with the main application. No separate deployment needed!

### Configuration

Edit `deploy/environments/lambda-archival.env` to customize:

```bash
# Archive thresholds
ARCHIVE_THRESHOLD_DAYS=90  # Messages older than 90 days
MEDIA_THRESHOLD_DAYS=30    # Media older than 30 days

# Schedule (every 2 days)
MESSAGE_ARCHIVAL_SCHEDULE="cron(0 2 */2 * ? *)"  # 2 AM UTC
MEDIA_ARCHIVAL_SCHEDULE="cron(0 3 */2 * ? *)"    # 3 AM UTC

# Performance tuning
LAMBDA_MEMORY_SIZE=512
LAMBDA_TIMEOUT=900  # 15 minutes
LAMBDA_BATCH_SIZE=100
```

## Usage

### Automatic Archival

The system runs automatically every 2 days:
- **Message archival**: Every 2 days at 2:00 AM UTC
- **Media archival**: Every 2 days at 3:00 AM UTC

### Manual Triggering

Use the Admin API to trigger archival manually:

```bash
# Test dry run (recommended first)
curl -X POST "https://your-service-url/api/admin/archival/trigger?job_type=both&dry_run=true"

# Trigger actual archival
curl -X POST "https://your-service-url/api/admin/archival/trigger?job_type=both"

# Trigger specific job type
curl -X POST "https://your-service-url/api/admin/archival/trigger?job_type=messages"
curl -X POST "https://your-service-url/api/admin/archival/trigger?job_type=media"
```

### Monitoring

#### Admin API Endpoints

```bash
# Check archival status
curl "https://your-service-url/api/admin/archival/status"

# View recent logs
curl "https://your-service-url/api/admin/archival/logs/messages"
curl "https://your-service-url/api/admin/archival/logs/media"

# Get metrics
curl "https://your-service-url/api/admin/archival/metrics"

# Toggle automatic scheduling
curl -X POST "https://your-service-url/api/admin/archival/schedule/toggle/messages"
curl -X POST "https://your-service-url/api/admin/archival/schedule/toggle/media"
```

#### CloudWatch Monitoring

**Log Groups**:
- `/aws/lambda/production-whatsapp-message-archival`
- `/aws/lambda/production-whatsapp-media-archival`

**View logs**:
```bash
aws logs tail /aws/lambda/production-whatsapp-message-archival --region us-east-1 --follow
```

**CloudWatch Alarms**:
- `production-whatsapp-message-archival-errors`
- `production-whatsapp-message-archival-duration`
- `production-whatsapp-media-archival-errors`
- `production-whatsapp-media-archival-duration`

## S3 Storage Structure

Archived data is stored in S3 with the following structure:

```
s3://your-data-bucket/
├── archived-messages/
│   ├── year=2024/
│   │   ├── month=01/
│   │   │   ├── day=01/
│   │   │   │   └── messages-2024-01-01-batch-001.json.gz
│   │   │   └── day=02/
│   │   └── month=02/
│   └── year=2025/
└── archived-media/
    ├── year=2024/
    │   ├── month=01/
    │   │   ├── day=01/
    │   │   │   ├── image_001.jpg
    │   │   │   ├── video_001.mp4
    │   │   │   └── document_001.pdf
    │   │   └── day=02/
    │   └── month=02/
    └── year=2025/
```

### S3 Lifecycle Policies

The system automatically creates S3 lifecycle policies:

- **Standard storage**: 30 days
- **Infrequent Access**: 60 days (after 30 days)
- **Glacier**: 180 days (after 90 days)
- **Deep Archive**: 365+ days (after 270 days)

## Lambda Functions

### Message Archival Function

**Purpose**: Archives old messages from PostgreSQL to S3
**Runtime**: Python 3.9
**Memory**: 512 MB
**Timeout**: 15 minutes
**Trigger**: EventBridge (every 2 days at 2 AM UTC)

**Process**:
1. Query messages older than threshold (default: 90 days)
2. Batch process messages (default: 100 per batch)
3. Compress and upload to S3 as JSON
4. Delete archived messages from PostgreSQL
5. Update archive metadata in database

**Configuration**:
- `ARCHIVE_THRESHOLD_DAYS`: Age threshold for archival
- `BATCH_SIZE`: Messages per batch
- `S3_BUCKET`: Target S3 bucket
- `DATABASE_URL`: PostgreSQL connection string

### Media Archival Function

**Purpose**: Archives media files from URLs to S3
**Runtime**: Python 3.9
**Memory**: 512 MB
**Timeout**: 15 minutes
**Trigger**: EventBridge (every 2 days at 3 AM UTC)

**Process**:
1. Query media records older than threshold (default: 30 days)
2. Download media files from URLs
3. Upload to S3 with proper naming
4. Update database with S3 locations
5. Mark media as archived

**Configuration**:
- `MEDIA_THRESHOLD_DAYS`: Age threshold for media archival
- `BATCH_SIZE`: Media files per batch
- `S3_BUCKET`: Target S3 bucket
- `DATABASE_URL`: PostgreSQL connection string

## Error Handling

### Automatic Retry Logic

Both Lambda functions include comprehensive error handling:
- **Database connection failures**: Exponential backoff retry
- **S3 upload failures**: Retry with different strategies
- **Media download failures**: Skip and continue with next batch
- **Timeout handling**: Graceful shutdown and state preservation

### Dead Letter Queue

Failed invocations are sent to a Dead Letter Queue (DLQ):
- **Queue**: `production-whatsapp-archival-dlq`
- **Retention**: 14 days
- **Monitoring**: CloudWatch alarms on message count

### Monitoring and Alerts

**CloudWatch Alarms**:
- **Error rate**: > 5 errors in 5 minutes
- **Duration**: > 10 minutes execution time
- **DLQ messages**: > 0 messages in queue

**Notification** (optional):
Configure SNS topics for alarm notifications.

## Troubleshooting

### Common Issues

1. **Lambda timeout**:
   - Increase `LAMBDA_TIMEOUT` in configuration
   - Reduce `BATCH_SIZE` for smaller batches
   - Check database query performance

2. **S3 upload failures**:
   - Verify IAM permissions for S3 access
   - Check S3 bucket policies
   - Monitor S3 service limits

3. **Database connection issues**:
   - Verify VPC configuration
   - Check security group rules
   - Validate database credentials

4. **Media download failures**:
   - Check media URL accessibility
   - Verify network connectivity from Lambda
   - Monitor for rate limiting

### Debugging Commands

```bash
# Check Lambda function status
aws lambda get-function --function-name production-whatsapp-message-archival

# View recent logs
aws logs filter-log-events \
    --log-group-name /aws/lambda/production-whatsapp-message-archival \
    --start-time $(date -d '1 hour ago' +%s)000

# Check EventBridge rule
aws events describe-rule --name production-whatsapp-message-archival-schedule

# Test function manually
aws lambda invoke \
    --function-name production-whatsapp-message-archival \
    --payload '{"test": true, "dry_run": true}' \
    response.json

# Check DLQ messages
aws sqs get-queue-attributes \
    --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/production-whatsapp-archival-dlq \
    --attribute-names ApproximateNumberOfMessages
```

### Performance Tuning

1. **Increase memory**: Higher memory = faster CPU
2. **Optimize batch size**: Balance between memory usage and efficiency
3. **Database indexing**: Ensure proper indexes on timestamp columns
4. **S3 multipart uploads**: For large files (>100MB)
5. **Concurrent processing**: Use async/await for I/O operations

## Security Considerations

### IAM Permissions

The Lambda functions use least-privilege IAM roles:

**Database Access**:
- RDS Connect permission
- VPC execution role

**S3 Access**:
- `s3:PutObject` on archive bucket
- `s3:GetObject` for verification
- `s3:DeleteObject` for cleanup

**CloudWatch**:
- Log group creation and writing
- Metric publishing

### Network Security

**VPC Configuration**:
- Lambda functions run in private subnets
- Database access through security groups
- No direct internet access (uses VPC endpoints)

**Encryption**:
- S3 objects encrypted at rest (SSE-S3 or SSE-KMS)
- Database connections use SSL/TLS
- Lambda environment variables encrypted

## Compliance and Retention

### Data Retention Policies

Configure retention based on your requirements:

```yaml
# Example lifecycle policy
MessageRetentionDays: 90    # Delete from PostgreSQL after 90 days
MediaRetentionDays: 30      # Archive media after 30 days
S3RetentionYears: 7         # Keep in S3 for 7 years
GlacierTransitionDays: 180  # Move to Glacier after 6 months
```

### Audit Trail

All archival operations are logged:
- **CloudWatch Logs**: Detailed execution logs
- **CloudTrail**: API calls and permissions
- **S3 Access Logs**: Object access patterns
- **Database Logs**: Query execution and performance

## Cost Optimization

### Lambda Costs

- **Execution time**: Optimize batch processing
- **Memory allocation**: Right-size based on usage
- **Invocation frequency**: Every 2 days (configurable)

**Estimated costs** (us-east-1):
- Lambda execution: ~$5-10/month
- CloudWatch logs: ~$2-5/month
- S3 storage: Variable based on data volume

### S3 Storage Costs

- **Lifecycle policies**: Automatic tier transitions
- **Compression**: JSON messages compressed with gzip
- **Intelligent Tiering**: Automatic cost optimization

## Backup and Recovery

### Backup Strategy

1. **Database backups**: RDS automated backups (point-in-time recovery)
2. **S3 versioning**: Object-level backup
3. **Cross-region replication**: Disaster recovery (optional)
4. **Lambda code**: Stored in deployment S3 bucket

### Recovery Procedures

1. **Restore from S3**: Re-import archived messages if needed
2. **Database recovery**: RDS point-in-time restore
3. **Lambda recovery**: Redeploy from CloudFormation template
4. **Configuration recovery**: Environment variables in template

## Development and Testing

### Local Development

```bash
# Set up local environment
python -m venv venv
source venv/bin/activate
pip install -r deploy/lambda/message-archival/requirements.txt

# Run tests locally
python -m pytest tests/test_archival_functions.py

# Test with local database
export DATABASE_URL="postgresql://user:pass@localhost:5432/testdb"
python deploy/lambda/message-archival/handler.py
```

### CI/CD Integration

The deployment scripts integrate with GitHub Actions:

```yaml
# .github/workflows/deploy-complete.yml
name: Deploy WhatsApp API with Archival
on:
  push:
    branches: [main]
      
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy complete infrastructure
        run: ./deploy-github.sh production us-east-1 ${{ secrets.GITHUB_CONNECTION_ARN }} ${{ secrets.DEFAULT_VPC_ID }}
        env:
          WHATSAPP_TOKEN: ${{ secrets.WHATSAPP_TOKEN }}
          VERIFY_TOKEN: ${{ secrets.VERIFY_TOKEN }}
          WHATSAPP_PHONE_NUMBER_ID: ${{ secrets.WHATSAPP_PHONE_NUMBER_ID }}
```

## Support and Maintenance

### Regular Maintenance

1. **Monitor logs**: Check for errors weekly
2. **Update dependencies**: Monthly security updates
3. **Performance review**: Quarterly optimization
4. **Cost review**: Monthly cost analysis

### Support Contacts

- **AWS Support**: For infrastructure issues
- **Development Team**: For application logic
- **Database Admin**: For PostgreSQL issues
- **Security Team**: For compliance and security

### Version History

- **v1.0.0**: Initial implementation with basic archival
- **v1.1.0**: Added media archival functionality
- **v1.2.0**: Enhanced error handling and monitoring
- **v1.3.0**: Added admin API and manual triggering
- **v2.0.0**: Current version with comprehensive features

For more information, see the [GitHub repository](https://github.com/therealabhishekc/goblin) or contact the development team.