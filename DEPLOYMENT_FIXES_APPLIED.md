# Deployment Fixes Applied

**Date:** October 2, 2025

## Summary of Changes

I've reviewed your WhatsApp Business API application and applied fixes for the most critical issues.

### ✅ **Fixes Applied Automatically**

1. **Removed Hardcoded Local Path** (`backend/app/config.py`)
   - Before: `"env_file": [".env", "/Users/abskchsk/Documents/govindjis/wa-app/backend/.env"]`
   - After: `"env_file": ".env"`
   - **Impact:** Application will now work properly in deployment

2. **Created `.env.example` Template** (`backend/.env.example`)
   - Added comprehensive template with all required variables
   - Includes comments explaining where to get each value
   - Safe to commit to repository
   - **Impact:** New developers can easily set up their environment

### ⚠️ **Critical Actions YOU Must Take**

These require manual action because they involve your Meta Business account and AWS:

#### 1. 🔴 URGENT: Revoke Exposed WhatsApp Credentials

Your real WhatsApp API credentials are in `backend/.env` which may have been committed to git.

**Steps to Fix:**

```bash
# Step 1: Go to Meta Business Suite
# https://business.facebook.com
# Navigate to: Settings > System Users > [Your WhatsApp User] > Generate New Token
# Save the new token somewhere safe (NOT in git)

# Step 2: Generate new verify token
openssl rand -hex 32
# Save this too

# Step 3: Update your local .env file
cd /Users/abskchsk/Documents/govindjis/wa-app/backend
cp .env.example .env
# Edit .env and add your NEW credentials
```

#### 2. Update Git to Not Track .env

```bash
cd /Users/abskchsk/Documents/govindjis/wa-app

# Remove .env from git tracking (keeps local file)
git rm --cached backend/.env

# Commit the change
git add backend/.env.example
git add backend/app/config.py
git commit -m "Security fix: Remove hardcoded paths and create .env.example"

# Push the changes
git push
```

#### 3. (Optional but Recommended) Clean Git History

If the `.env` file with real credentials was already pushed:

```bash
# WARNING: This rewrites git history - coordinate with team!
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env" \
  --prune-empty --tag-name-filter cat -- --all

git push origin --force --all
```

---

## Deployment Architecture Review

### ✅ **What's Working Correctly**

Your CloudFormation template is actually quite well configured:

1. **Environment Variables** - All SQS queue URLs are properly injected (lines 488-499 in infrastructure.yaml)
2. **IAM Roles** - App Runner role has correct permissions for DynamoDB, SQS, S3
3. **Database** - PostgreSQL RDS with IAM authentication configured
4. **DynamoDB** - Deduplication table with TTL for automatic cleanup
5. **SQS Queues** - All queues (incoming, outgoing, analytics) with DLQs configured
6. **Health Checks** - App Runner health check pointing to /health endpoint

### ⚠️ **Deployment Considerations**

#### Database Setup Required

The CloudFormation creates the RDS instance, but you need to:

1. **Create the database and user:**
   ```bash
   # Connect to RDS (replace with your endpoint)
   psql -h your-rds-endpoint.rds.amazonaws.com -U postgres
   
   # Run these SQL commands:
   CREATE DATABASE whatsapp_business_production;
   CREATE USER app_user WITH PASSWORD 'temp_password';
   ALTER USER app_user WITH PASSWORD NULL;  # For IAM auth
   GRANT rds_iam TO app_user;
   GRANT ALL PRIVILEGES ON DATABASE whatsapp_business_production TO app_user;
   ```

2. **Run database migrations:**
   ```bash
   # From your local machine with access to RDS
   cd /Users/abskchsk/Documents/govindjis/wa-app/backend
   
   # Set DATABASE_URL to your RDS endpoint
   export DATABASE_URL="postgresql://app_user@your-rds-endpoint:5432/whatsapp_business_production?sslmode=require"
   
   # Initialize database tables
   python3 -c "from app.core.database import init_database; init_database()"
   ```

#### WhatsApp Webhook Configuration

After deployment:

1. **Get your App Runner URL:**
   ```bash
   aws apprunner describe-service \
     --service-arn <your-service-arn> \
     --query 'Service.ServiceUrl' \
     --output text
   ```

2. **Configure in Meta Developer Console:**
   - Go to: https://developers.facebook.com/apps/
   - Select your app > WhatsApp > Configuration
   - Webhook URL: `https://your-apprunner-url.awsapprunner.com/webhook`
   - Verify Token: (the VERIFY_TOKEN you set in CloudFormation parameters)
   - Subscribe to: `messages`, `message_status`

3. **Test the webhook:**
   ```bash
   # This should return your verify token
   curl "https://your-apprunner-url.awsapprunner.com/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=YOUR_VERIFY_TOKEN"
   ```

---

## Pre-Deployment Checklist

Use this before deploying:

### Security

- [x] Hardcoded paths removed from config
- [ ] New WhatsApp API tokens generated (YOU MUST DO)
- [ ] `.env` removed from git tracking (YOU MUST DO)
- [ ] AWS IAM roles configured in CloudFormation (Already done ✅)
- [ ] Database credentials secured (RDS uses IAM auth ✅)

### Configuration

- [x] Environment variables properly configured in CloudFormation
- [x] SQS queue URLs will be injected automatically
- [x] DynamoDB table name will be set correctly
- [x] Health check endpoint configured

### Infrastructure

- [ ] CloudFormation parameters prepared:
  - [ ] `Environment` (development/staging/production)
  - [ ] `WhatsAppToken` (NEW token from Meta)
  - [ ] `VerifyToken` (NEW random string)
  - [ ] `WhatsAppPhoneNumberId` (from Meta)
  - [ ] `GitHubConnectionArn` (from AWS App Runner Console)
  - [ ] `DefaultVPCId` (from AWS VPC Console)

### Database

- [ ] RDS instance will be created by CloudFormation ✅
- [ ] Database and user setup (see SQL commands above)
- [ ] Tables initialized (run init_database())
- [ ] IAM authentication configured

### Testing

- [ ] Local testing with new credentials
- [ ] Webhook verification test
- [ ] Send test message
- [ ] Check CloudWatch logs
- [ ] Verify message in database
- [ ] Monitor SQS queues

---

## Deployment Command

Once you've completed the checklist:

```bash
cd /Users/abskchsk/Documents/govindjis/wa-app

# Set your parameters
export ENVIRONMENT="production"
export WHATSAPP_TOKEN="<your_new_token>"
export VERIFY_TOKEN="<your_new_verify_token>"
export PHONE_NUMBER_ID="<your_phone_number_id>"
export GITHUB_CONNECTION_ARN="<your_github_connection_arn>"
export DEFAULT_VPC_ID="<your_vpc_id>"

# Deploy using the script
./deploy-github.sh \
  $ENVIRONMENT \
  us-east-1 \
  $GITHUB_CONNECTION_ARN \
  $DEFAULT_VPC_ID \
  "10.0.0.0/8"  # Or your office IP CIDR
```

Or deploy manually:

```bash
aws cloudformation create-stack \
  --stack-name whatsapp-api-production \
  --template-body file://deploy/aws/cloudformation/infrastructure.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=production \
    ParameterKey=WhatsAppToken,ParameterValue=$WHATSAPP_TOKEN \
    ParameterKey=VerifyToken,ParameterValue=$VERIFY_TOKEN \
    ParameterKey=WhatsAppPhoneNumberId,ParameterValue=$PHONE_NUMBER_ID \
    ParameterKey=GitHubConnectionArn,ParameterValue=$GITHUB_CONNECTION_ARN \
    ParameterKey=DefaultVPCId,ParameterValue=$DEFAULT_VPC_ID \
    ParameterKey=AllowedCIDR,ParameterValue="10.0.0.0/8" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

---

## Post-Deployment Verification

### 1. Check App Runner Service

```bash
# Get service status
aws apprunner describe-service \
  --service-arn <your-service-arn> \
  --query 'Service.Status' \
  --output text

# Should output: RUNNING
```

### 2. Test Health Endpoint

```bash
# Get service URL
SERVICE_URL=$(aws apprunner describe-service \
  --service-arn <your-service-arn> \
  --query 'Service.ServiceUrl' \
  --output text)

# Test health
curl https://$SERVICE_URL/health

# Should return: {"status":"healthy"}
```

### 3. Verify Components

```bash
# Check detailed health
curl https://$SERVICE_URL/health/detailed

# Should show status of:
# - dynamodb: healthy
# - sqs: healthy
# - message_processor: running
```

### 4. Monitor Logs

```bash
# Tail CloudWatch logs
aws logs tail /aws/apprunner/whatsapp-api-production --follow

# Look for:
# ✅ Database initialized successfully
# ✅ Race-safe SQS message processor started
# ✅ Archive API endpoints loaded
```

### 5. Test Webhook

```bash
# Send test message from WhatsApp to your business number
# Then check database:
psql -h your-rds-endpoint -U app_user whatsapp_business_production -c \
  "SELECT message_id, from_phone, message_type, status, created_at 
   FROM whatsapp_messages 
   ORDER BY created_at DESC 
   LIMIT 5;"
```

---

## Troubleshooting Guide

### App Runner Not Starting

**Check logs:**
```bash
aws logs tail /aws/apprunner/whatsapp-api-production --follow
```

**Common issues:**
- Missing environment variable → Check CloudFormation parameters
- Database connection failed → Verify RDS security group
- Import error → Check requirements.txt

### Webhook Not Receiving Messages

**Verify configuration:**
```bash
# Check webhook config endpoint
curl https://$SERVICE_URL/webhook/debug/config

# Should show all env vars configured (not actual values)
```

**Common issues:**
- Verify token mismatch → Check Meta config matches CloudFormation parameter
- URL not reachable → Check App Runner security
- SSL certificate issue → App Runner handles this automatically

### Messages Not Processing

**Check SQS queues:**
```bash
# Check message count in incoming queue
aws sqs get-queue-attributes \
  --queue-url <incoming-queue-url> \
  --attribute-names ApproximateNumberOfMessages

# If messages stuck, check DLQ:
aws sqs get-queue-attributes \
  --queue-url <incoming-dlq-url> \
  --attribute-names ApproximateNumberOfMessages
```

**Common issues:**
- Worker not started → Check logs for "Message processor started"
- DynamoDB permission denied → Check IAM role
- Database connection failed → Check RDS security group

### Database Connection Issues

**Test connection:**
```bash
# From App Runner (view logs) or local machine
python3 -c "
from app.core.database import create_database_url, create_db_engine
print(create_database_url())
engine = create_db_engine()
conn = engine.connect()
print('✅ Database connection successful')
"
```

**Common issues:**
- IAM auth token expired → Automatic refresh should handle this
- Security group blocking → Add App Runner service to RDS security group
- User not configured for IAM → Run the SQL setup commands

---

## Monitoring and Alerts

### CloudWatch Dashboards

Create a dashboard to monitor:

1. **App Runner Metrics:**
   - Active Instances
   - Request Count
   - Request Latency
   - HTTP 4xx/5xx Errors

2. **SQS Metrics:**
   - Messages Visible (should stay low)
   - Messages in DLQ (should stay at 0)
   - Age of Oldest Message

3. **DynamoDB Metrics:**
   - Consumed Read/Write Capacity
   - User Errors (should stay at 0)
   - System Errors (should stay at 0)

4. **RDS Metrics:**
   - CPU Utilization
   - Database Connections
   - Read/Write Latency

### CloudWatch Alarms

Set up alarms for:

```bash
# DLQ has messages (indicates failures)
aws cloudwatch put-metric-alarm \
  --alarm-name whatsapp-incoming-dlq-messages \
  --alarm-description "Alert when messages appear in DLQ" \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=QueueName,Value=whatsapp-incoming-dlq-production

# App Runner unhealthy
aws cloudwatch put-metric-alarm \
  --alarm-name whatsapp-apprunner-unhealthy \
  --alarm-description "Alert when App Runner service is unhealthy" \
  --metric-name 4xxStatusResponses \
  --namespace AWS/AppRunner \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

---

## Cost Estimates

Based on your configuration:

- **App Runner:** ~$25-50/month (production config: 1 vCPU, 2GB RAM)
- **RDS (db.t3.micro):** ~$15-20/month
- **DynamoDB (pay-per-request):** ~$1-5/month (depends on traffic)
- **SQS:** ~$0-1/month (first 1M requests free)
- **S3:** ~$1-5/month (depends on media storage)
- **CloudWatch Logs:** ~$0.50-2/month

**Total estimated:** ~$45-85/month for production environment

---

## Support Resources

- **Full Code Review:** See `CODE_REVIEW_REPORT.md`
- **Security Issues:** See `SECURITY_FIXES_REQUIRED.md`
- **Meta WhatsApp Docs:** https://developers.facebook.com/docs/whatsapp/
- **AWS App Runner Docs:** https://docs.aws.amazon.com/apprunner/
- **Your App Repository:** Check commit history for recent changes

---

## Next Steps

1. **Immediate (Today):**
   - [ ] Revoke old WhatsApp tokens
   - [ ] Generate new tokens
   - [ ] Update `.env` with new credentials
   - [ ] Remove `.env` from git tracking
   - [ ] Test application locally

2. **Before Deployment (This Week):**
   - [ ] Set up AWS GitHub connection for App Runner
   - [ ] Prepare CloudFormation parameters
   - [ ] Review security group configurations
   - [ ] Plan database initialization

3. **Deployment Day:**
   - [ ] Deploy CloudFormation stack
   - [ ] Initialize database
   - [ ] Configure WhatsApp webhook
   - [ ] Run test messages
   - [ ] Monitor for 24 hours

4. **Post-Deployment (Next Week):**
   - [ ] Set up CloudWatch alarms
   - [ ] Create monitoring dashboard
   - [ ] Document any issues encountered
   - [ ] Plan regular maintenance schedule

---

**Good luck with your deployment!** 🚀

The application architecture is solid. The main issues were:
1. ✅ Hardcoded paths (FIXED)
2. ⚠️ Exposed credentials (YOU MUST FIX)
3. ✅ CloudFormation configuration (Already correct)

Once you handle the credentials, you're ready to deploy!
