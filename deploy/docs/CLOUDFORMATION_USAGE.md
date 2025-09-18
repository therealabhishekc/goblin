# CloudFormation Deployment Guide

## Overview
This CloudFormation template deploys the complete WhatsApp Business API infrastructure including App Runner, DynamoDB, RDS PostgreSQL, and IAM roles.

## Prerequisites
1. AWS CLI configured with appropriate permissions
2. AWS credentials set up (access key or IAM role)
3. Parameter files created for each environment

## File Usage

### 1. Initial Stack Deployment

For **development** environment:
```bash
aws cloudformation create-stack \
  --stack-name wa-app-dev \
  --template-body file://deploy/aws/cloudformation/infrastructure.yaml \
  --parameters file://deploy/aws/parameters/parameters-dev.json \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

For **staging** environment:
```bash
aws cloudformation create-stack \
  --stack-name wa-app-staging \
  --template-body file://deploy/aws/cloudformation/infrastructure.yaml \
  --parameters file://deploy/aws/parameters/parameters-staging.json \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

For **production** environment:
```bash
aws cloudformation create-stack \
  --stack-name wa-app-prod \
  --template-body file://deploy/aws/cloudformation/infrastructure.yaml \
  --parameters file://deploy/aws/parameters/parameters-prod.json \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

### 2. Stack Updates (Reusing with Same Data)

#### Option A: Direct Update
```bash
aws cloudformation update-stack \
  --stack-name wa-app-dev \
  --template-body file://deploy/aws/cloudformation/infrastructure.yaml \
  --parameters file://deploy/aws/parameters/parameters-dev.json \
  --capabilities CAPABILITY_IAM
```

#### Option B: Using Change Sets (Recommended)
```bash
# Create change set to preview changes
aws cloudformation create-change-set \
  --stack-name wa-app-dev \
  --template-body file://deploy/aws/cloudformation/infrastructure.yaml \
  --parameters file://deploy/aws/parameters/parameters-dev.json \
  --capabilities CAPABILITY_IAM \
  --change-set-name update-$(date +%Y%m%d-%H%M%S)

# Review the change set
aws cloudformation describe-change-set \
  --stack-name wa-app-dev \
  --change-set-name update-$(date +%Y%m%d-%H%M%S)

# Execute the change set if satisfied
aws cloudformation execute-change-set \
  --stack-name wa-app-dev \
  --change-set-name update-$(date +%Y%m%d-%H%M%S)
```

### 3. Updating Parameters

To update configuration values (like WhatsApp tokens):

1. **Edit the parameter file**:
   ```bash
   # Edit the relevant parameter file
   vim deploy/aws/parameters/parameters-dev.json
   ```

2. **Update the stack**:
   ```bash
   aws cloudformation update-stack \
     --stack-name wa-app-dev \
     --use-previous-template \
     --parameters file://deploy/aws/parameters/parameters-dev.json \
     --capabilities CAPABILITY_IAM
   ```

### 4. Monitoring Deployment

Check stack status:
```bash
aws cloudformation describe-stacks --stack-name wa-app-dev
```

Watch stack events in real-time:
```bash
aws cloudformation describe-stack-events --stack-name wa-app-dev
```

## Important Notes

### Data Persistence
- **RDS Database**: Data is preserved during updates (unless you change deletion policies)
- **DynamoDB**: Data is preserved during updates
- **Parameter Store**: Values are updated without data loss

### Safe Update Practices
1. Always use change sets for production
2. Test updates in development first
3. Backup databases before major updates
4. Monitor CloudFormation events during deployment

### Rolling Back
If an update fails:
```bash
aws cloudformation cancel-update-stack --stack-name wa-app-dev
```

Or create a change set to revert to previous template/parameters.

### Environment Isolation
Each environment (dev/staging/prod) uses:
- Separate CloudFormation stacks
- Separate parameter files
- Separate AWS resources
- Environment-specific naming conventions

## Troubleshooting

### Common Issues
1. **IAM Permissions**: Ensure your AWS credentials have CloudFormation, App Runner, RDS, and DynamoDB permissions
2. **Resource Limits**: Check AWS service limits in your region
3. **Naming Conflicts**: Stack names must be unique in your account/region

### Getting Stack Outputs
```bash
aws cloudformation describe-stacks \
  --stack-name wa-app-dev \
  --query 'Stacks[0].Outputs'
```

This will show you the App Runner service URL, database endpoints, and other important resource information.
