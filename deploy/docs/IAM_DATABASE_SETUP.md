# IAM Database Authentication Setup Guide

## 🔐 Overview
This guide shows how to use IAM authentication instead of passwords for your RDS PostgreSQL database.

## ✅ What's Been Updated

### 1. **Database Configuration** (`app/core/database.py`)
- ✅ Added IAM token generation
- ✅ Automatic token refresh every 15 minutes
- ✅ Fallback to password auth for local development
- ✅ Connection pooling with token refresh

### 2. **CloudFormation Template** (`infrastructure.yaml`)
- ✅ Enabled `EnableIAMDatabaseAuthentication: true`
- ✅ Added RDS IAM permissions to App Runner role
- ✅ Secure IAM policy with conditions

### 3. **IAM Policy** (`rds-iam-policy.json`)
- ✅ Restricted to specific database user
- ✅ Region and IP restrictions
- ✅ Minimal required permissions

## 🚀 Deployment Steps

### Step 1: Deploy Infrastructure
```bash
aws cloudformation create-stack \
  --stack-name whatsapp-prod \
  --template-body file://deploy/aws/cloudformation/infrastructure.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=production \
    ParameterKey=DatabasePassword,ParameterValue=SecurePassword123! \
    ParameterKey=WhatsAppToken,ParameterValue=your_token \
    ParameterKey=VerifyToken,ParameterValue=your_verify_token \
  --capabilities CAPABILITY_NAMED_IAM
```

### Step 2: Get Database Endpoint
```bash
aws cloudformation describe-stacks \
  --stack-name whatsapp-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
  --output text
```

### Step 3: Create IAM Database User
```bash
# Run the setup script
./deploy/scripts/setup-iam-db-user.sh \
  your-rds-endpoint.rds.amazonaws.com \
  whatsapp_business_production \
  postgres \
  app_user
```

### Step 4: Configure App Runner Environment Variables
```bash
# Set these in your App Runner service
USE_IAM_AUTH=true
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_NAME=whatsapp_business_production
DB_USER=app_user
AWS_REGION=us-east-1
```

## 🔧 Environment Configurations

### Production (IAM Auth)
```env
USE_IAM_AUTH=true
DB_HOST=prod-endpoint.rds.amazonaws.com
DB_NAME=whatsapp_business_production
DB_USER=app_user
```

### Development (Password Auth)
```env
USE_IAM_AUTH=false
DATABASE_URL=sqlite:///./local_wa_app.db
# or
DATABASE_URL=postgresql://postgres:password@localhost:5432/whatsapp_business
```

## 🔍 How It Works

### 1. **Token Generation**
```python
# Automatic IAM token generation
rds_client = boto3.client('rds')
token = rds_client.generate_db_auth_token(
    DBHostname=endpoint,
    Port=5432,
    DBUsername='app_user'
)
```

### 2. **Connection with Token**
```python
# Connection string with IAM token
url = f"postgresql://app_user:{token}@endpoint:5432/database"
```

### 3. **Automatic Refresh**
- Tokens expire every 15 minutes
- SQLAlchemy event listener refreshes tokens automatically
- No manual token management required

## 🛡️ Security Benefits

### ✅ **What You Get:**
- No stored passwords in environment variables
- Automatic credential rotation (15-minute tokens)
- Full audit trail via CloudTrail
- Fine-grained IAM permissions
- Network-level security via VPC

### ✅ **IAM Policy Conditions:**
- Regional restrictions
- Time-based access
- IP address restrictions
- Specific database user access

## 🧪 Testing

### 1. **Verify IAM Authentication**
```bash
# Check CloudTrail for database connection events
aws logs filter-log-events \
  --log-group-name /aws/rds/instance/whatsapp-postgres-production/postgresql \
  --filter-pattern "authentication"
```

### 2. **Test Token Generation**
```python
import boto3
rds = boto3.client('rds')
token = rds.generate_db_auth_token(
    DBHostname='your-endpoint.rds.amazonaws.com',
    Port=5432,
    DBUsername='app_user'
)
print(f"Token generated: {token[:50]}...")
```

## 🔄 Migration Path

### From Password → IAM Auth:
1. Deploy updated CloudFormation (enables IAM auth)
2. Create IAM database user
3. Update environment variables
4. Deploy application
5. Verify connections work
6. Remove password-based access (optional)

## 🚨 Troubleshooting

### Common Issues:
1. **"Authentication failed"** → Check IAM policy and user setup
2. **"Connection refused"** → Verify security groups
3. **"Token expired"** → Check automatic refresh logic
4. **"Permission denied"** → Verify database user permissions

### Debug Commands:
```bash
# Test IAM permissions
aws sts get-caller-identity

# Test database connectivity
psql -h endpoint -U app_user -d database_name

# Check CloudTrail logs
aws logs describe-log-groups --log-group-name-prefix "/aws/rds"
```

## 📊 Cost Impact

### IAM Auth vs Password:
- **Cost**: Same (no additional charges)
- **Security**: Significantly improved
- **Maintenance**: Reduced (no password rotation)
- **Compliance**: Enhanced audit capabilities

Your database is now secured with enterprise-grade IAM authentication! 🔐
