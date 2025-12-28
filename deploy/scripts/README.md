# Lambda Deployment Scripts

## Overview

This directory contains scripts for deploying Lambda functions to AWS using S3 upload for reliability.

## Main Script: `deploy-lambda.sh`

Unified deployment script for both `media-archival` and `message-archival` Lambda functions.

### Usage

```bash
# Deploy both Lambdas (default)
bash deploy/scripts/deploy-lambda.sh

# Deploy only media-archival
bash deploy/scripts/deploy-lambda.sh media

# Deploy only message-archival  
bash deploy/scripts/deploy-lambda.sh message

# Deploy both explicitly
bash deploy/scripts/deploy-lambda.sh both
```

### Features

- ✅ **S3 Upload Method**: More reliable than direct upload, prevents timeouts
- ✅ **Smart Packaging**: Excludes boto3 (already in Lambda runtime)
- ✅ **Automatic Testing**: Tests function after deployment
- ✅ **Selective Deployment**: Deploy one or both functions
- ✅ **Color-coded Output**: Easy-to-read progress indicators
- ✅ **Auto Cleanup**: Removes temporary build files

### How It Works

1. **Build**: Creates Lambda package with dependencies in `/tmp/lambda-build`
2. **Upload**: Uploads ZIP to S3 bucket `whatsapp-data-development-205924461245`
3. **Update**: Updates Lambda function code from S3
4. **Wait**: Waits for update to complete
5. **Test**: Invokes function to verify deployment
6. **Stats**: Shows package size and last modified time
7. **Cleanup**: Removes temporary build files

### Package Sizes

- **message-archival**: ~3 MB (only psycopg2-binary)
- **media-archival**: ~17 MB (includes requests library and psycopg2-binary)

### Environment

- **Environment**: `development`
- **S3 Bucket**: `whatsapp-data-development-205924461245`
- **Region**: `us-east-1`

### Lambda Functions

| Function Name | Purpose | Runtime | Memory | Timeout |
|--------------|---------|---------|--------|---------|
| `development-whatsapp-media-archival` | Archives media files to S3 | Python 3.9 | 2048 MB | 900s |
| `development-whatsapp-message-archival` | Archives messages to S3 | Python 3.9 | 512 MB | 300s |

## Other Scripts

### `deploy-archival-lambda.sh`

**Deprecated** - Use `deploy-lambda.sh` instead. This was the original script for media-archival only.

### `create-iam-role-manual.sh`

Creates IAM roles required for Lambda functions.

### `setup-iam-db-user.sh`

Sets up IAM database authentication for PostgreSQL.

### `fix_iam_auth.sh`

Fixes IAM authentication issues with RDS.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.9 installed
- pip3 available
- Access to S3 bucket: `whatsapp-data-development-205924461245`
- Lambda functions already created in AWS

## Troubleshooting

### Upload Timeouts

If you experience timeouts with direct uploads, the script automatically uses S3 upload method which is more reliable for larger packages.

### Permission Errors

Ensure your AWS credentials have permissions for:
- `lambda:UpdateFunctionCode`
- `lambda:GetFunction`
- `lambda:InvokeFunction`
- `s3:PutObject`
- `s3:GetObject`

### Package Size Too Large

Lambda has a 50 MB limit for direct upload and 250 MB limit for S3 upload (unzipped). If packages are too large:
- Remove unnecessary dependencies
- Use Lambda layers for common dependencies
- Exclude boto3 (already in Lambda runtime)

## Best Practices

1. **Test Locally First**: Test your Lambda code locally before deploying
2. **Incremental Deployments**: Deploy and test one function at a time when making changes
3. **Monitor Logs**: Check CloudWatch logs after deployment
4. **Version Control**: Commit changes before deploying
5. **Backup**: Keep the old deployment package in S3 for rollback

## Quick Reference

```bash
# Deploy both
./deploy-lambda.sh

# Deploy media only
./deploy-lambda.sh media

# Deploy message only
./deploy-lambda.sh message

# Check Lambda logs
aws logs tail /aws/lambda/development-whatsapp-media-archival --follow
aws logs tail /aws/lambda/development-whatsapp-message-archival --follow

# Manual test
aws lambda invoke --function-name development-whatsapp-media-archival /dev/stdout
aws lambda invoke --function-name development-whatsapp-message-archival /dev/stdout
```
