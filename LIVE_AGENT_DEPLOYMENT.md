# Live Agent Feature - Deployment Guide

## Overview
Complete live agent "Talk to Expert" feature with 22-hour auto-expiration, chat history, search/filter, and supervisor view.

## Components Created

### Backend
1. **Database Migration**: `backend/migrations/add_live_agent_tables.sql`
   - Creates `agent_sessions` and `agent_messages` tables
   - Includes indexes for performance

2. **Models**: `backend/app/models/agent.py`
   - AgentSessionDB, AgentMessageDB models
   - Pydantic schemas for API

3. **Service Layer**: `backend/app/services/agent_service.py`
   - Business logic for agent operations
   - 10 methods including session management, message handling, auto-expiration

4. **API Routes**: `backend/app/api/agent_routes.py`
   - 9 REST endpoints for session and message management
   - Search/filter for history

5. **Message Handler Updates**: `backend/app/services/message_handler.py`
   - Added AGENT_MODE detection
   - Priority handling for active agent sessions
   - Customer can type "end chat" to exit

6. **Lambda Function**: `backend/lambda/agent-expiration/lambda_function.py`
   - Auto-expires sessions after 22 hours
   - Runs every 5 minutes via EventBridge

### Frontend
7. **Agent Dashboard**: `frontend/agent-dashboard/`
   - React app with 3 tabs (Active/All/History)
   - Real-time message updates
   - Search and filter capabilities
   - WhatsApp-style UI

## Deployment Steps

### 1. Database Migration
```bash
cd backend/migrations
./run_migration_on_rds.sh add_live_agent_tables.sql
```

Or manually:
```bash
psql -h whatsapp-postgres-development.cibi66cyqd2r.us-east-1.rds.amazonaws.com \
     -U your_username \
     -d whatsapp_db \
     -f add_live_agent_tables.sql
```

### 2. Deploy Backend (Already in App Runner)
The backend code is already deployed via App Runner. Just restart the service to pick up changes:
```bash
aws apprunner start-deployment --service-arn <your-service-arn>
```

Or push to GitHub and auto-deploy will trigger.

### 3. Deploy Lambda Function

#### Package Lambda
```bash
cd backend/lambda/agent-expiration
pip install -r requirements.txt -t .
zip -r agent-expiration.zip .
```

#### Create Lambda Function
```bash
aws lambda create-function \
  --function-name agent-session-expiration \
  --runtime python3.12 \
  --handler lambda_function.lambda_handler \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --zip-file fileb://agent-expiration.zip \
  --timeout 60 \
  --environment Variables="{
    DB_HOST=whatsapp-postgres-development.cibi66cyqd2r.us-east-1.rds.amazonaws.com,
    DB_NAME=whatsapp_db,
    DB_USER=your_username,
    DB_PASSWORD=your_password,
    WHATSAPP_API_URL=https://byqpifhtjq.us-east-1.awsapprunner.com,
    WHATSAPP_TOKEN=your_whatsapp_token
  }"
```

#### Create EventBridge Rule (Run every 5 minutes)
```bash
aws events put-rule \
  --name agent-expiration-trigger \
  --schedule-expression "rate(5 minutes)" \
  --state ENABLED

aws lambda add-permission \
  --function-name agent-session-expiration \
  --statement-id EventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:YOUR_ACCOUNT:rule/agent-expiration-trigger

aws events put-targets \
  --rule agent-expiration-trigger \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:YOUR_ACCOUNT:function:agent-session-expiration"
```

### 4. Deploy Frontend

#### Local Development
```bash
cd frontend/agent-dashboard
npm install
npm start
```

Access at: http://localhost:3000

#### Production Build
```bash
npm run build
```

Deploy the `build/` folder to:
- AWS S3 + CloudFront
- Netlify
- Vercel
- Or any static hosting

#### Example: Deploy to S3
```bash
aws s3 sync build/ s3://your-bucket-name/agent-dashboard/
aws s3 website s3://your-bucket-name/ --index-document index.html
```

## Testing

### 1. Test Database
```bash
psql -h whatsapp-postgres-development.cibi66cyqd2r.us-east-1.rds.amazonaws.com \
     -U your_username \
     -d whatsapp_db \
     -c "SELECT * FROM agent_sessions;"
```

### 2. Test API Endpoints
```bash
# Get waiting sessions
curl https://byqpifhtjq.us-east-1.awsapprunner.com/api/agent/sessions/waiting

# Get active sessions for agent
curl https://byqpifhtjq.us-east-1.awsapprunner.com/api/agent/sessions/my-chats/agent123

# Get history
curl "https://byqpifhtjq.us-east-1.awsapprunner.com/api/agent/sessions/history?status=ended&limit=10"
```

### 3. Test End-to-End Flow

1. **Customer Side** (WhatsApp):
   - Send "hi" to get main menu
   - Click "Talk to Expert" button (button ID must be "AGENT_MODE")
   - Customer receives: "🙋 Connecting you to an agent..."
   - Type messages to agent
   - Type "end chat" to exit

2. **Agent Side** (Dashboard):
   - Login with Agent ID and Name
   - See customer in "Waiting" queue
   - Click "Accept" to join chat
   - Send messages to customer
   - Click "End Chat" to close session

3. **Auto-Expiration** (Lambda):
   - Wait 22 hours (or modify expires_at in DB for testing)
   - Lambda runs every 5 minutes
   - Session automatically ends
   - Customer receives: "⏰ Chat expired after 22 hours"

### 4. Test Lambda Manually
```bash
aws lambda invoke \
  --function-name agent-session-expiration \
  --payload '{}' \
  response.json

cat response.json
```

## Configuration

### Add "Talk to Expert" Button to Template

Update your main menu template to include the AGENT_MODE button:

```json
{
  "type": "button",
  "header": {
    "type": "text",
    "text": "🙏 Welcome to Govindjis"
  },
  "body": {
    "text": "How can we help you today?"
  },
  "action": {
    "buttons": [
      {
        "type": "reply",
        "reply": {
          "id": "MENU_PRODUCTS",
          "title": "📦 Products"
        }
      },
      {
        "type": "reply",
        "reply": {
          "id": "MENU_ORDER",
          "title": "🛒 Place Order"
        }
      },
      {
        "type": "reply",
        "reply": {
          "id": "AGENT_MODE",
          "title": "👤 Talk to Expert"
        }
      }
    ]
  },
  "steps": {
    "initial": {
      "next_steps": {
        "MENU_PRODUCTS": "products_menu",
        "MENU_ORDER": "order_flow",
        "AGENT_MODE": "AGENT_MODE"
      }
    }
  }
}
```

**Important**: The button ID **must** be exactly `AGENT_MODE` for the message handler to detect it.

## API Endpoints

### Sessions
- `POST /api/agent/sessions/start/{phone_number}` - Start agent session
- `GET /api/agent/sessions/waiting` - Get waiting sessions
- `GET /api/agent/sessions/my-chats/{agent_id}` - Get agent's active chats
- `GET /api/agent/sessions/all` - Get all sessions (supervisor view)
- `GET /api/agent/sessions/history` - Get history with filters
- `POST /api/agent/sessions/{id}/assign` - Assign agent to session
- `POST /api/agent/sessions/{id}/end` - End session

### Messages
- `GET /api/agent/sessions/{id}/messages` - Get session messages
- `POST /api/agent/sessions/{id}/messages` - Send message

### Query Parameters for History
- `agent_id` - Filter by agent
- `status` - Filter by status (waiting/active/ended)
- `search` - Search phone or name
- `start_date` - From date (YYYY-MM-DD)
- `end_date` - To date (YYYY-MM-DD)
- `limit` - Results per page (default 50)
- `offset` - Pagination offset

## Architecture

```
Customer (WhatsApp) → WhatsApp API → App Runner (Backend)
                                         ↓
                                    PostgreSQL RDS
                                         ↑
Agent (Dashboard) → React App → API Endpoints

Lambda (every 5 min) → Check expired sessions → Notify customers
```

## Features

✅ Customer clicks "Talk to Expert" button
✅ Agent dashboard with 3 tabs (Active/All/History)
✅ Real-time message updates (auto-refresh every 3s)
✅ 22-hour auto-expiration via Lambda
✅ Search and filter chat history
✅ View all conversations (supervisor mode)
✅ WhatsApp-style UI
✅ Session status tracking (waiting/active/ended)
✅ System messages for events
✅ Customer can type "end chat" to exit

## Monitoring

### Check Lambda Logs
```bash
aws logs tail /aws/lambda/agent-session-expiration --follow
```

### Check Backend Logs
```bash
# App Runner logs in CloudWatch
aws logs tail /aws/apprunner/<service-name> --follow
```

### Check Database
```bash
# Count sessions by status
psql -h <host> -U <user> -d whatsapp_db -c "
  SELECT status, COUNT(*) 
  FROM agent_sessions 
  GROUP BY status;
"

# Check expired sessions
psql -h <host> -U <user> -d whatsapp_db -c "
  SELECT * FROM agent_sessions 
  WHERE expires_at < NOW() 
  AND status != 'ended';
"
```

## Troubleshooting

### Issue: Lambda not expiring sessions
- Check Lambda execution role has RDS access
- Verify environment variables are set
- Check CloudWatch logs for errors
- Test Lambda manually

### Issue: Agent dashboard not loading sessions
- Check API URL in config.js
- Verify CORS is enabled in backend
- Check browser console for errors
- Test API endpoints directly with curl

### Issue: Messages not appearing
- Check WebSocket connection (if using)
- Verify auto-refresh is working (3-second interval)
- Check agent_messages table for new rows
- Verify sender_type is correct ('customer' or 'agent')

### Issue: Button not triggering agent mode
- Verify button ID is exactly "AGENT_MODE"
- Check message_handler.py has AGENT_MODE detection
- Look for errors in backend logs
- Test with curl to webhook endpoint

## Next Steps

1. **Authentication**: Add real authentication for agents
2. **Notifications**: Add push notifications when new customer arrives
3. **Typing Indicators**: Show when agent/customer is typing
4. **File Sharing**: Support images, documents in chat
5. **Canned Responses**: Quick replies for common questions
6. **Analytics**: Track response times, satisfaction scores
7. **Assignment Rules**: Auto-assign based on agent availability
8. **Queue Management**: Priority queue for VIP customers

## Support

For issues or questions, check:
- Backend logs in CloudWatch
- Lambda logs in CloudWatch
- Browser console for frontend errors
- Database tables for data integrity
