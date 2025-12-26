# Campaign Frontend & Infrastructure Setup

## 🎉 What Was Created

### ✅ Frontend Application (`frontend/campaign/`)

A complete React-based campaign manager with:

**Features:**
- 📋 Campaign List View (with filters)
- ➕ Multi-Step Campaign Creation Wizard
- 📊 Detailed Campaign Statistics  
- ⏸️ Pause/Resume/Cancel Controls
- 🚀 Manual Daily Processing Trigger
- 📈 Real-time Progress Tracking

**Tech Stack:**
- React 18
- React Router for navigation
- Axios for API calls
- Date-fns for date formatting
- Responsive CSS design

**Files Created:**
```
frontend/campaign/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── CampaignList.js          # Main campaign list
│   │   ├── CreateCampaign.js        # 3-step wizard
│   │   └── CampaignDetails.js       # Stats & management
│   ├── services/
│   │   └── api.js                   # API service layer
│   ├── utils/
│   │   └── formatters.js            # Formatting utilities
│   ├── App.js                       # Main app with routing
│   ├── App.css                      # Global styles
│   ├── index.js                     # Entry point
│   └── index.css                    # Base styles
├── package.json                     # Dependencies
├── .gitignore
└── README.md                        # Detailed docs
```

---

### ✅ CloudFormation Updates (`deploy/aws/cloudformation/infrastructure.yaml`)

Added automated daily campaign processing:

**Resources Added:**

1. **CampaignProcessorFunction** (Lambda)
   - Invokes App Runner `/api/marketing/process-daily` endpoint
   - Runs daily at 9 AM UTC
   - Python 3.11 runtime
   - 5-minute timeout
   - Auto-generated inline code

2. **CampaignProcessorRole** (IAM Role)
   - Lambda execution role
   - CloudWatch Logs permissions
   - App Runner describe permissions

3. **DailyCampaignScheduleRule** (EventBridge)
   - Cron schedule: `cron(0 9 * * ? *)`  
   - Triggers Lambda daily at 9 AM UTC
   - Configurable schedule expression

4. **CampaignProcessorInvokePermission** (Lambda Permission)
   - Allows EventBridge to invoke Lambda

5. **CampaignProcessorErrorAlarm** (CloudWatch Alarm)
   - Alerts on Lambda errors
   - 5-minute evaluation period

6. **CampaignProcessorLogGroup** (CloudWatch Logs)
   - 14-day log retention
   - Auto-created log group

**Outputs Added:**
- `CampaignProcessorFunctionArn` - Lambda function ARN
- `DailyCampaignSchedule` - EventBridge rule reference
- `CampaignProcessingTime` - Human-readable schedule

---

## 🚀 Quick Start

### 1. Install Frontend Dependencies

```bash
cd frontend/campaign
npm install
```

### 2. Start Development Server

```bash
npm start
```

Runs on [http://localhost:3000](http://localhost:3000)

### 3. Configure API URL

**Option A:** Use proxy (already configured)
```json
// package.json
"proxy": "http://localhost:8000"
```

**Option B:** Environment variable
```bash
# Create .env file
echo "REACT_APP_API_URL=http://localhost:8000/api" > .env
```

### 4. Build for Production

```bash
npm run build
```

Output: `build/` directory ready for deployment

---

## 🏗️ Deploy Infrastructure Updates

### Update CloudFormation Stack

```bash
aws cloudformation update-stack \
  --stack-name your-stack-name \
  --template-body file://deploy/aws/cloudformation/infrastructure.yaml \
  --parameters file://deploy/aws/cloudformation/parameters.json \
  --capabilities CAPABILITY_NAMED_IAM
```

### What Gets Deployed:

1. **Lambda Function**
   - Function name: `{Environment}-campaign-processor`
   - Automatically invokes your App Runner service
   - Logs to CloudWatch

2. **EventBridge Schedule**
   - Rule name: `{Environment}-daily-campaign-processing`
   - Runs at 9 AM UTC daily
   - Can be customized in template

3. **Monitoring**
   - CloudWatch alarm for Lambda errors
   - Logs retained for 14 days
   - Metrics available in CloudWatch

### Verify Deployment:

```bash
# Check Lambda function
aws lambda get-function --function-name development-campaign-processor

# Check EventBridge rule
aws events describe-rule --name development-daily-campaign-processing

# View recent logs
aws logs tail /aws/lambda/development-campaign-processor --follow
```

---

## 🎯 How It Works

### Daily Processing Flow

```
EventBridge (9 AM UTC)
    ↓
Lambda Function
    ↓
HTTP POST Request
    ↓
App Runner: /api/marketing/process-daily
    ↓
Backend processes campaigns
    ↓
Sends 250 messages per campaign
    ↓
Updates database
```

### Frontend User Flow

```
1. User creates campaign
   POST /marketing/campaigns
   
2. User adds recipients
   POST /campaigns/{id}/recipients
   
3. User activates campaign
   POST /campaigns/{id}/activate
   
4. EventBridge triggers daily (automated)
   Lambda → POST /marketing/process-daily
   
5. User monitors progress
   GET /campaigns/{id}/stats
```

---

## 📝 Configuration Options

### Change Processing Time

Edit CloudFormation template:

```yaml
DailyCampaignScheduleRule:
  Properties:
    ScheduleExpression: 'cron(0 9 * * ? *)'  # Change this
```

**Examples:**
- `cron(0 9 * * ? *)` - 9 AM UTC daily (current)
- `cron(0 14 * * ? *)` - 2 PM UTC daily (9 AM EST)
- `cron(0 3 * * ? *)` - 3 AM UTC daily (10 PM EST previous day)
- `cron(0 */6 * * ? *)` - Every 6 hours
- `rate(12 hours)` - Every 12 hours

### Disable Auto-Processing

Set EventBridge rule state to DISABLED:

```yaml
State: DISABLED  # Change from ENABLED
```

Or via AWS Console:
1. Go to EventBridge → Rules
2. Find `{environment}-daily-campaign-processing`
3. Click "Disable"

### Manual Processing

Users can trigger manually via frontend:
1. Click "🚀 Process Daily" button on Campaign List page
2. Or call API directly: `POST /api/marketing/process-daily`

---

## 🔧 Customization

### Frontend Customization

**Change API URL:**
```javascript
// src/services/api.js
const API_BASE_URL = 'https://your-api-domain.com/api';
```

**Change Colors:**
```css
/* src/App.css */
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

**Add Authentication:**
```javascript
// src/services/api.js
api.interceptors.request.use((config) => {
  config.headers['Authorization'] = `Bearer ${getToken()}`;
  return config;
});
```

### Backend Customization

**Change Daily Limit:**
```python
# backend/app/api/marketing.py
default_daily_limit = 250  # Change this
```

**Add Validation:**
```python
# Add checks before activating campaign
if campaign.total_target_customers > 100000:
    raise ValueError("Campaign too large")
```

---

## 📊 Monitoring

### CloudWatch Metrics

**Lambda Function:**
- Function: `{Environment}-campaign-processor`
- Metrics: Invocations, Errors, Duration, Throttles
- Logs: `/aws/lambda/{Environment}-campaign-processor`

**EventBridge Rule:**
- Rule: `{Environment}-daily-campaign-processing`
- Metrics: Invocations, FailedInvocations, TriggeredRules

### View Logs:

```bash
# Tail logs live
aws logs tail /aws/lambda/development-campaign-processor --follow

# View specific time range
aws logs tail /aws/lambda/development-campaign-processor \
  --since 1h \
  --format short
```

### Create Custom Alarms:

```bash
# Alarm on campaign processing failures
aws cloudwatch put-metric-alarm \
  --alarm-name campaign-processing-failures \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=FunctionName,Value=development-campaign-processor
```

---

## 🐛 Troubleshooting

### Frontend Issues

**Problem:** Can't connect to API
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check proxy in package.json
cat package.json | grep proxy
```

**Problem:** Build fails
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Lambda Issues

**Problem:** Lambda can't reach App Runner
```bash
# Check Lambda execution role has network access
# App Runner must be publicly accessible
# Or use VPC configuration
```

**Problem:** Function timing out
```yaml
# Increase timeout in CloudFormation
Timeout: 600  # 10 minutes
```

**Problem:** Function failing
```bash
# Check logs
aws logs tail /aws/lambda/development-campaign-processor --follow

# Test function manually
aws lambda invoke \
  --function-name development-campaign-processor \
  --payload '{"test": true}' \
  response.json
```

### Campaign Processing Issues

**Problem:** Campaigns not sending
```bash
# Check EventBridge rule is enabled
aws events describe-rule --name development-daily-campaign-processing

# Check Lambda is being triggered
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=development-campaign-processor \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

**Problem:** Messages not being sent
- Verify campaign status is 'active'
- Check recipients have `scheduled_send_date = TODAY`
- Verify users are still subscribed
- Check WhatsApp API credentials

---

## 📚 Additional Resources

### Documentation:
- [MARKETING_CAMPAIGN_GUIDE.md](../../MARKETING_CAMPAIGN_GUIDE.md) - Complete campaign API guide
- [DATABASE_SCHEMA_GUIDE.md](../../DATABASE_SCHEMA_GUIDE.md) - Database schema reference
- [frontend/campaign/README.md](../campaign/README.md) - Frontend detailed docs

### AWS Documentation:
- [EventBridge Cron Expressions](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html)
- [Lambda Functions](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html)

---

## ✅ Testing Checklist

### Frontend Testing:
- [ ] Campaign list loads
- [ ] Can create new campaign
- [ ] Can add recipients (auto and manual)
- [ ] Can activate campaign
- [ ] Campaign details shows stats
- [ ] Can pause/resume/cancel
- [ ] Manual "Process Daily" works

### Backend Testing:
- [ ] All API endpoints respond
- [ ] Campaign creation works
- [ ] Recipients are added correctly
- [ ] Activation creates schedule
- [ ] Daily processing sends messages
- [ ] Stats update in real-time

### Infrastructure Testing:
- [ ] CloudFormation stack updates successfully
- [ ] Lambda function is created
- [ ] EventBridge rule is enabled
- [ ] Lambda has correct permissions
- [ ] Logs are being written
- [ ] Alarms are configured

---

## 🎉 Summary

You now have:

✅ **Complete Campaign Frontend**
- 3-page React application
- Professional UI/UX
- Real-time updates
- Mobile responsive

✅ **Automated Daily Processing**
- EventBridge scheduler
- Lambda function
- CloudWatch monitoring
- Error alerts

✅ **Production Ready**
- Error handling
- Logging
- Alarms
- Documentation

### Next Steps:

1. **Deploy Frontend:**
   ```bash
   cd frontend/campaign
   npm install
   npm run build
   # Deploy build/ to S3 + CloudFront or hosting service
   ```

2. **Update CloudFormation:**
   ```bash
   aws cloudformation update-stack ...
   ```

3. **Test Campaign:**
   - Create a test campaign
   - Add 5-10 test recipients
   - Activate campaign
   - Wait for daily processing (or trigger manually)

4. **Monitor:**
   - Watch CloudWatch logs
   - Check campaign stats in frontend
   - Verify messages are sent

🚀 **Your campaign system is ready to scale to hundreds of thousands of messages!**
