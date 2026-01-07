# Templates Frontend Troubleshooting Guide

## Issue: Templates not showing in frontend

### Root Cause
The backend templates API endpoints were not deployed to AWS App Runner yet.

### Solution Status
✅ **Code has been pushed to GitHub** (commit b819285)

The following changes are being deployed:
1. Templates API endpoints (`/api/templates/*`)
2. CRUD operations for workflow templates
3. Model definitions and database integration

### Deployment Timeline
AWS App Runner automatically deploys from GitHub when changes are detected.
- **Typical deployment time**: 5-10 minutes
- **Started**: Just now (after git push)
- **Check status**: Run `./check-deployment.sh` or manually test the endpoint

### Manual Verification

#### 1. Check if API is deployed:
```bash
curl https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates
```

**Expected response when deployed:**
- HTTP 200 with JSON array of templates

**Current response (before deployment):**
- HTTP 404 with `{"detail":"Not Found"}`

#### 2. Check App Runner deployment status:
1. Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner)
2. Select your service
3. Check "Deployments" tab
4. Look for the latest deployment with commit `b819285`

#### 3. View deployment logs:
```bash
# Use AWS CLI if available
aws apprunner list-operations --service-arn <your-service-arn>
```

### Frontend Verification

Once the API is deployed, verify the frontend:

#### 1. Start the React app:
```bash
cd frontend/template
npm start
```

#### 2. Open browser console (F12):
Look for:
- ✅ `🔗 API Base URL: https://2hdfnnus3x.us-east-1.awsapprunner.com`
- ✅ Successful API call to `/api/templates`
- ✅ Templates list displayed

#### 3. Common errors and fixes:

**Error**: `Failed to fetch templates`
**Cause**: API not deployed yet
**Fix**: Wait for deployment to complete

**Error**: `CORS policy` error
**Cause**: CORS not configured properly
**Fix**: Already configured in backend (allows all origins)

**Error**: Empty list but no error
**Cause**: Database has no templates
**Fix**: Use the create template script to add templates

### What's in the Database

You mentioned there are already some templates in the database. Once the API is deployed, you should see:
- `main_menu` template with buttons (explore, talk to expert, visit us)
- Any other templates you created

### Next Steps After Deployment

1. ✅ **Verify API is working**: `curl https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates`
2. ✅ **Refresh frontend**: The templates should now appear
3. ✅ **Test CRUD operations**: Try creating, editing, and deleting templates
4. ✅ **Test WhatsApp integration**: Send "Hi" to your WhatsApp number

### Testing the Full Flow

Once deployed, test the complete workflow:

```bash
# 1. List templates
curl https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates

# 2. Get specific template
curl https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/<template-id>

# 3. Create template (example)
curl -X POST https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "test_menu",
    "template_type": "button",
    "trigger_keywords": ["test"],
    "menu_structure": {
      "text": "Test menu",
      "buttons": [{"id": "1", "title": "Option 1"}]
    },
    "is_active": true
  }'

# 4. Send WhatsApp message "Hi" to trigger main_menu template
```

### Estimated Resolution Time

- **Deployment**: 5-10 minutes from now
- **Frontend refresh**: Immediate after deployment
- **Total**: ~10 minutes

### Support

If the API is still not working after 15 minutes:
1. Check AWS App Runner service status
2. Check CloudWatch logs for errors
3. Verify the database connection
4. Ensure environment variables are set correctly

### Files Changed in This Update

- ✅ `backend/app/api/templates.py` - API endpoints
- ✅ `backend/app/models/conversation.py` - Template models
- ✅ `backend/app/main.py` - Router registration
- ✅ `frontend/template/*` - React frontend app

All changes have been pushed to GitHub and are deploying now.
