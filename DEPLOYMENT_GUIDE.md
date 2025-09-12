# AWS App Runner + DynamoDB Integration Guide

## 🎉 Your Setup is Complete!

Your AWS resources have been successfully created and configured. Here's what was set up:

### ✅ Created Resources

1. **DynamoDB Table**: `ttest`
   - Partition Key: `message_id` (String)
   - TTL enabled on `ttl` attribute
   - Pay-per-request billing

2. **IAM Role**: `AppRunnerDynamoDBRole`
   - ARN: `arn:aws:iam::461346075501:role/AppRunnerDynamoDBRole`
   - Trust policy allows App Runner to assume this role

3. **IAM Policy**: `AppRunnerDynamoDBPolicy`
   - Grants permissions to read/write DynamoDB table
   - Attached to the App Runner role

### 📱 Your Application Features

Your WhatsApp webhook application already includes:
- ✅ Message deduplication using DynamoDB
- ✅ Automatic TTL (6 hours) for stored message IDs
- ✅ Error handling for DynamoDB failures
- ✅ Health check endpoint at `/health`

## 🚀 Deploying to App Runner

### Option 1: Using AWS Console

1. **Create App Runner Service**:
   - Go to AWS App Runner in the console
   - Click "Create service"
   - Choose "Source code repository" or "Container image repository"

2. **Configure Source**:
   - If using GitHub: Connect your repository
   - If using container: Use your container image

3. **Configure Service**:
   - **Runtime**: Python 3.12
   - **Build command**: `pip install -r backend/requirements.txt`
   - **Start command**: `cd backend && gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000`
   - **Port**: 8000

4. **Configure Instance Role**:
   - **Instance role ARN**: `arn:aws:iam::461346075501:role/AppRunnerDynamoDBRole`

5. **Environment Variables**:
   ```
   DYNAMODB_TABLE_NAME=ttest
   AWS_REGION=us-east-1
   VERIFY_TOKEN=your_verify_token
   WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
   WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
   ```

### Option 2: Using AWS CLI

1. **Create apprunner.yaml** (already created for you!)

2. **Deploy using CLI**:
   ```bash
   aws apprunner create-service \
     --service-name "whatsapp-webhook" \
     --source-configuration '{
       "ImageRepository": {
         "ImageIdentifier": "your-image-uri",
         "ImageConfiguration": {
           "Port": "8000"
         }
       },
       "AutoDeploymentsEnabled": true
     }' \
     --instance-configuration '{
       "Cpu": "0.25 vCPU",
       "Memory": "0.5 GB",
       "InstanceRoleArn": "arn:aws:iam::461346075501:role/AppRunnerDynamoDBRole"
     }'
   ```

### Option 3: Using apprunner.yaml

The `apprunner.yaml` file has been created with your configuration. You can:

1. Push your code to a GitHub repository
2. Connect App Runner to your repository
3. It will automatically use the `apprunner.yaml` configuration

## 🔧 Environment Variables Required

Make sure to set these in your App Runner service:

| Variable | Value | Description |
|----------|-------|-------------|
| `DYNAMODB_TABLE_NAME` | `ttest` | DynamoDB table name |
| `AWS_REGION` | `us-east-1` | AWS region |
| `VERIFY_TOKEN` | `your_token` | WhatsApp webhook verify token |
| `WHATSAPP_ACCESS_TOKEN` | `your_token` | WhatsApp API access token |
| `WHATSAPP_PHONE_NUMBER_ID` | `your_id` | WhatsApp phone number ID |

## 🧪 Testing Your Setup

1. **Health Check**:
   ```bash
   curl https://your-apprunner-url.amazonaws.com/health
   ```

2. **Check DynamoDB Connection**:
   - Your app will log DynamoDB initialization status
   - Check App Runner logs for "DynamoDB client initialized" message

3. **Test Message Deduplication**:
   - Send the same WhatsApp message twice
   - Second message should be marked as "duplicate" in logs

## 📊 Monitoring

- **App Runner Metrics**: Available in CloudWatch
- **DynamoDB Metrics**: Monitor read/write capacity and throttling
- **Application Logs**: Available in App Runner console and CloudWatch

## 🔍 Troubleshooting

### Common Issues:

1. **DynamoDB Access Denied**:
   - Verify the Instance Role ARN is correctly set
   - Check IAM policy permissions

2. **Table Not Found**:
   - Verify `DYNAMODB_TABLE_NAME` environment variable
   - Ensure table exists in the correct region

3. **Application Won't Start**:
   - Check the start command in apprunner.yaml
   - Verify all dependencies in requirements.txt

### Log Messages to Look For:

- ✅ `"DynamoDB client initialized for table: ttest"`
- ✅ `"Message ID stored in DynamoDB: {message_id}"`
- ❌ `"DynamoDB initialization failed"`
- ❌ `"DynamoDB put_item failed"`

## 📁 File Structure

```
wa-app/
├── backend/
│   ├── app/
│   │   ├── dynamodb_client.py    # DynamoDB operations
│   │   ├── main.py               # FastAPI app
│   │   ├── whatsapp_webhook.py   # Webhook handler
│   │   └── ...
│   ├── requirements.txt          # Python dependencies
│   └── Procfile                 # Process definition
├── aws/
│   ├── dynamodb-policy.json     # IAM policy for DynamoDB
│   └── trust-policy.json        # Trust policy for App Runner
├── apprunner.yaml               # App Runner configuration
└── setup-aws-resources.sh      # Setup script (already run)
```

## 🎯 Next Steps

1. Deploy your App Runner service using one of the methods above
2. Configure your WhatsApp webhook URL to point to your App Runner service
3. Test the webhook with WhatsApp messages
4. Monitor logs and metrics

Your application is now ready for production with AWS App Runner and DynamoDB! 🚀
