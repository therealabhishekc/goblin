# WhatsApp Business API Deployment Guide

This guide covers deploying the WhatsApp Business API application to AWS using App Runner, RDS PostgreSQL, and DynamoDB.

## Prerequisites

- AWS CLI configured with appropriate permissions
- WhatsApp Business API credentials
- Domain name for webhook (optional but recommended)

## Deployment Steps

### 1. Infrastructure Setup

Deploy the AWS infrastructure using CloudFormation:

```bash
# Navigate to deployment directory
cd deploy/aws/cloudformation

# Deploy infrastructure
aws cloudformation create-stack \
  --stack-name whatsapp-business-api-dev \
  --template-body file://infrastructure.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=development \
    ParameterKey=DatabasePassword,ParameterValue=YourSecurePassword123 \
    ParameterKey=WhatsAppToken,ParameterValue=your_whatsapp_token \
    ParameterKey=VerifyToken,ParameterValue=your_verify_token \
  --capabilities CAPABILITY_NAMED_IAM
```

### 2. Environment Configuration

Update the environment files with actual values:

```bash
# Copy environment template
cp deploy/environments/development.env backend/.env

# Edit with your actual credentials
vim backend/.env
```

### 3. App Runner Deployment

Create App Runner service:

```bash
# Use the setup script
./deploy/aws/scripts/setup-aws-resources.sh
```

Or manually create App Runner service using the AWS Console with the `apprunner.yaml` configuration.

### 4. Database Migration

The application will automatically create database tables on startup. Monitor the logs to ensure successful initialization.

### 5. Webhook Configuration

Configure WhatsApp webhook URL:
- URL: `https://your-app-runner-url.amazonaws.com/webhook`
- Verify Token: Use the token from your environment configuration

## Environment-Specific Deployment

### Development
```bash
# Use development environment
export ENVIRONMENT=development
./scripts/deploy.sh
```

### Staging
```bash
# Use staging environment
export ENVIRONMENT=staging
./scripts/deploy.sh
```

### Production
```bash
# Use production environment
export ENVIRONMENT=production
./scripts/deploy.sh
```

## Monitoring and Troubleshooting

### Health Checks
- Application: `GET /health`
- Database: `GET /health/database`
- Detailed: `GET /health/detailed`

### Logs
Monitor App Runner logs in CloudWatch for application behavior.

### Common Issues

1. **Database Connection Failed**
   - Check RDS security groups
   - Verify database credentials
   - Ensure VPC configuration is correct

2. **Webhook Verification Failed**
   - Verify VERIFY_TOKEN environment variable
   - Check WhatsApp webhook configuration

3. **DynamoDB Access Denied**
   - Check IAM role permissions
   - Verify DynamoDB table exists

## Scaling Considerations

- **App Runner**: Automatically scales based on traffic
- **RDS**: Consider Multi-AZ for production
- **DynamoDB**: Pay-per-request scales automatically

## Security Best Practices

1. Use AWS Secrets Manager for sensitive credentials
2. Enable RDS encryption at rest
3. Use VPC endpoints for DynamoDB access
4. Implement proper IAM policies with least privilege
5. Enable CloudTrail for audit logging

## Cost Optimization

- Use t3.micro for development RDS instances
- Enable DynamoDB auto-scaling in production
- Monitor CloudWatch metrics for unused resources

## Backup and Recovery

- RDS automated backups are enabled (7 days retention)
- Consider cross-region backup for production
- DynamoDB point-in-time recovery available

## Support

For issues and support:
1. Check application logs in CloudWatch
2. Verify health endpoints
3. Review AWS service status
4. Contact development team
