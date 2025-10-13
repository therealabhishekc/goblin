# Complete AWS Deployment Guide for WhatsApp Business Application

This guide will walk you through deploying your entire WhatsApp Business application to AWS from scratch.

## Architecture Overview

Your application uses:
- **AWS App Runner**: Python backend hosting (auto-scaling)
- **Amazon RDS PostgreSQL**: Main database (user profiles, messages, campaigns)
- **Amazon DynamoDB**: Message deduplication
- **Amazon S3**: Media file storage
- **Amazon SQS**: Message queue processing
- **AWS Lambda**: Automated data archival
- **AWS Secrets Manager**: Credential management
- **Amazon CloudWatch**: Logging and monitoring

## Prerequisites

### 1. AWS Account Setup
- AWS account with admin access
- AWS CLI installed and configured
- Billing alerts configured (recommended)

### 2. WhatsApp Business API Setup
You need these from Meta Developer Console:
- **WHATSAPP_TOKEN**: Access token from Meta Business
- **VERIFY_TOKEN**: Your custom webhook verify token (create any secure string)
- **PHONE_NUMBER_ID**: WhatsApp Business Phone Number ID

### 3. GitHub Repository
- Code pushed to GitHub
- Repository access configured

### 4. Local Tools
```bash
# Install AWS CLI
brew install awscli  # macOS

# Configure AWS credentials
aws configure
# Enter: AWS Access Key ID, Secret Key, Region (e.g., us-east-1)
```

---

## Step-by-Step Deployment

### STEP 1: Prepare Your Environment Variables

First, gather all required information:

```bash
# WhatsApp Credentials (from Meta Developer Console)
WHATSAPP_TOKEN="your_token_here"
VERIFY_TOKEN="your_custom_verify_token"
PHONE_NUMBER_ID="your_phone_number_id"

# Database Password (create a strong password)
DATABASE_PASSWORD="YourSecureP@ssw0rd123!"

# AWS Region
AWS_REGION="us-east-1"

# Environment (development, staging, or production)
ENVIRONMENT="development"
```

### STEP 2: Find Your Default VPC ID

```bash
# Get your default VPC ID
aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text

# Output will be something like: vpc-0a1b2c3d4e5f6g7h8
# Save this VPC ID for the next step
```

### STEP 3: Create GitHub Connection for App Runner

**Important**: This must be done manually in AWS Console first.

1. Go to AWS Console → App Runner → Connections
2. Click "Create connection"
3. Select "GitHub"
4. Give it a name: `github-connection-whatsapp`
5. Authenticate with GitHub
6. Copy the Connection ARN (looks like: `arn:aws:apprunner:us-east-1:123456789:connection/xxx`)

### STEP 4: Update Database Migration

Make sure your database schema is up to date:

```bash
cd /Users/abskchsk/Documents/govindjis/wa-app

# Review the complete schema
cat backend/migrations/complete_schema.sql
```

The schema now includes:
- ✅ User profiles with address fields
- ✅ WhatsApp messages with direction and status
- ✅ Subscription management
- ✅ Marketing campaigns
- ✅ Business metrics

### STEP 5: Deploy Infrastructure with CloudFormation

```bash
cd /Users/abskchsk/Documents/govindjis/wa-app

# Deploy the complete infrastructure
aws cloudformation create-stack \
  --stack-name whatsapp-business-api-dev \
  --template-body file://deploy/aws/cloudformation/infrastructure.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=development \
    ParameterKey=WhatsAppToken,ParameterValue="YOUR_WHATSAPP_TOKEN" \
    ParameterKey=VerifyToken,ParameterValue="YOUR_VERIFY_TOKEN" \
    ParameterKey=WhatsAppPhoneNumberId,ParameterValue="YOUR_PHONE_NUMBER_ID" \
    ParameterKey=GitHubConnectionArn,ParameterValue="arn:aws:apprunner:us-east-1:YOUR_ACCOUNT:connection/xxx" \
    ParameterKey=GitHubRepositoryUrl,ParameterValue="https://github.com/therealabhishekc/goblin" \
    ParameterKey=GitHubBranch,ParameterValue="main" \
    ParameterKey=DefaultVPCId,ParameterValue="vpc-xxx" \
    ParameterKey=AllowedCIDR,ParameterValue="0.0.0.0/0" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# This will take 15-20 minutes to complete
```

Monitor the deployment:
```bash
# Watch stack creation progress
aws cloudformation describe-stacks \
  --stack-name whatsapp-business-api-dev \
  --query 'Stacks[0].StackStatus' \
  --output text

# View events
aws cloudformation describe-stack-events \
  --stack-name whatsapp-business-api-dev \
  --max-items 10
```

### STEP 6: Get Deployment Outputs

Once the stack is created (status = CREATE_COMPLETE):

```bash
# Get all important outputs
aws cloudformation describe-stacks \
  --stack-name whatsapp-business-api-dev \
  --query 'Stacks[0].Outputs' \
  --output table
```

Important outputs you'll need:
- **AppRunnerServiceUrl**: Your application URL
- **DatabaseEndpoint**: PostgreSQL endpoint
- **S3BucketName**: Media storage bucket
- **DynamoDBTableName**: Deduplication table

### STEP 7: Initialize Database Schema

The application should auto-create tables on first startup, but you can verify:

```bash
# Get database endpoint from CloudFormation output
DB_HOST=$(aws cloudformation describe-stacks \
  --stack-name whatsapp-business-api-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
  --output text)

# Connect to database (you'll need to allow your IP in security group first)
psql -h $DB_HOST -U app_user -d whatsapp_db

# Then run the migration
\i backend/migrations/complete_schema.sql
```

Or let the application auto-migrate on startup (recommended).

### STEP 8: Configure WhatsApp Webhook

1. Get your App Runner URL from CloudFormation outputs
2. Go to Meta Developer Console → WhatsApp → Configuration
3. Edit webhook:
   - **Callback URL**: `https://YOUR_APP_RUNNER_URL.amazonaws.com/webhook`
   - **Verify Token**: Same as VERIFY_TOKEN you set earlier
4. Subscribe to webhook fields:
   - ✅ messages
   - ✅ message_template_status_update
5. Test the webhook connection

### STEP 9: Verify Deployment

Test all endpoints:

```bash
# Get your App Runner URL
APP_URL=$(aws cloudformation describe-stacks \
  --stack-name whatsapp-business-api-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`AppRunnerServiceUrl`].OutputValue' \
  --output text)

# Health check
curl https://$APP_URL/health

# Detailed health check
curl https://$APP_URL/health/detailed

# Database health
curl https://$APP_URL/health/database
```

### STEP 10: Monitor Application

```bash
# View application logs
aws logs tail /aws/apprunner/whatsapp-api-development --follow

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/AppRunner \
  --metric-name RequestCount \
  --dimensions Name=ServiceName,Value=whatsapp-api-development \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

---

## Post-Deployment Configuration

### 1. Test Message Flow

Send a test message to your WhatsApp Business number and verify:
- ✅ Message appears in CloudWatch logs
- ✅ Message saved to database
- ✅ Auto-reply sent (if configured)

### 2. Import Existing Users (if needed)

```bash
# Prepare CSV file with user data
# Format: whatsapp_phone,display_name,address_line1,city,state,zipcode,email

# Upload to frontend
# Go to: https://YOUR_FRONTEND_URL/bulk-import
# Upload CSV file
```

### 3. Create Marketing Campaign

```bash
# Use the API to create a campaign
curl -X POST https://$APP_URL/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Welcome Campaign",
    "template_name": "welcome_message",
    "target_audience": {"subscription": "subscribed"},
    "daily_send_limit": 250
  }'
```

---

## Environment-Specific Deployments

### Development
```bash
# Already deployed above
# Use for testing and development
```

### Staging
```bash
aws cloudformation create-stack \
  --stack-name whatsapp-business-api-staging \
  --template-body file://deploy/aws/cloudformation/infrastructure.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=staging \
    [... other parameters ...] \
  --capabilities CAPABILITY_NAMED_IAM
```

### Production
```bash
aws cloudformation create-stack \
  --stack-name whatsapp-business-api-prod \
  --template-body file://deploy/aws/cloudformation/infrastructure.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=production \
    [... other parameters ...] \
  --capabilities CAPABILITY_NAMED_IAM
```

**Production-specific changes:**
- Use larger RDS instance (db.t3.small or higher)
- Enable Multi-AZ for RDS
- Set AllowedCIDR to specific IPs (not 0.0.0.0/0)
- Configure custom domain with Route 53
- Enable automated backups
- Set up CloudWatch alarms

---

## Updating the Application

### Update Code
```bash
# Push changes to GitHub
git add .
git commit -m "Your changes"
git push origin main

# App Runner will automatically detect changes and redeploy
# Monitor deployment in AWS Console → App Runner → your service
```

### Update Infrastructure
```bash
# Update the CloudFormation stack
aws cloudformation update-stack \
  --stack-name whatsapp-business-api-dev \
  --template-body file://deploy/aws/cloudformation/infrastructure.yaml \
  --parameters [... same parameters as create-stack ...] \
  --capabilities CAPABILITY_NAMED_IAM
```

### Run Database Migration
```bash
# For new schema changes, SSH to a bastion or use IAM authentication
psql -h $DB_HOST -U app_user -d whatsapp_db \
  -f backend/migrations/complete_schema.sql
```

---

## Troubleshooting

### Application Won't Start
```bash
# Check App Runner logs
aws logs tail /aws/apprunner/whatsapp-api-development --follow

# Common issues:
# - Database connection failed → Check security groups
# - Missing environment variables → Check CloudFormation parameters
# - Import errors → Check requirements.txt
```

### Database Connection Issues
```bash
# Test database connectivity
aws rds describe-db-instances \
  --db-instance-identifier whatsapp-db-development \
  --query 'DBInstances[0].Endpoint'

# Check security groups allow App Runner access
```

### WhatsApp Webhook Not Working
```bash
# Verify webhook is accessible
curl https://$APP_URL/webhook

# Check verify token matches
# Review CloudWatch logs for webhook attempts
```

### High Costs
```bash
# Check resource usage
aws ce get-cost-and-usage \
  --time-period Start=2025-01-01,End=2025-01-31 \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --group-by Type=SERVICE

# Optimize:
# - Scale down RDS instance for dev
# - Set DynamoDB to on-demand billing
# - Clean up old CloudWatch logs
# - Archive old media files to S3 Glacier
```

---

## Security Checklist

- [ ] Use Secrets Manager for all credentials
- [ ] Enable RDS encryption at rest
- [ ] Use VPC for RDS (private subnets)
- [ ] Restrict security group access
- [ ] Enable CloudTrail for audit logging
- [ ] Set up CloudWatch alarms for errors
- [ ] Use IAM roles (not access keys)
- [ ] Enable MFA on AWS account
- [ ] Regular security updates
- [ ] Backup and disaster recovery plan

---

## Cost Estimates

### Development Environment (Monthly)
- App Runner: ~$25-50 (with auto-scaling)
- RDS PostgreSQL (t3.micro): ~$15
- DynamoDB (on-demand): ~$1-5
- S3: ~$1-5
- CloudWatch Logs: ~$2
- **Total: ~$45-75/month**

### Production Environment (Monthly)
- App Runner: ~$100-200
- RDS PostgreSQL (t3.small, Multi-AZ): ~$60
- DynamoDB: ~$10-20
- S3: ~$10-20
- Lambda: ~$5
- CloudWatch: ~$10
- **Total: ~$200-325/month**

---

## Support and Resources

### AWS Documentation
- [App Runner](https://docs.aws.amazon.com/apprunner/)
- [RDS PostgreSQL](https://docs.aws.amazon.com/rds/)
- [CloudFormation](https://docs.aws.amazon.com/cloudformation/)

### WhatsApp Business API
- [Meta Developer Docs](https://developers.facebook.com/docs/whatsapp)
- [Cloud API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)

### Your Application
- Backend code: `/Users/abskchsk/Documents/govindjis/wa-app/backend/`
- Deployment scripts: `/Users/abskchsk/Documents/govindjis/wa-app/deploy/`
- Documentation: `/Users/abskchsk/Documents/govindjis/wa-app/docs/`

---

## Quick Reference Commands

```bash
# View stack status
aws cloudformation describe-stacks --stack-name whatsapp-business-api-dev

# View application logs
aws logs tail /aws/apprunner/whatsapp-api-development --follow

# Get app URL
aws cloudformation describe-stacks \
  --stack-name whatsapp-business-api-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`AppRunnerServiceUrl`].OutputValue' \
  --output text

# Delete entire stack (BE CAREFUL!)
aws cloudformation delete-stack --stack-name whatsapp-business-api-dev

# Redeploy app (force new deployment)
aws apprunner start-deployment --service-arn YOUR_SERVICE_ARN
```

---

## Next Steps

1. ✅ Deploy infrastructure (STEP 5)
2. ✅ Configure WhatsApp webhook (STEP 8)
3. ✅ Test message flow
4. 📊 Set up monitoring dashboards
5. 📧 Configure CloudWatch alarms
6. 🔒 Review security settings
7. 💰 Set up billing alerts
8. 📖 Document custom configurations

Good luck with your deployment! 🚀
