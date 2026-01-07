# 🚀 Quick Start Guide - Template Manager

## Step 1: Verify Backend is Running

Before starting the frontend, ensure your backend has the templates API deployed.

### Check Backend Health
```bash
curl https://2hdfnnus3x.us-east-1.awsapprunner.com/health
```
Expected: `{"status":"healthy"}`

### Check Templates API
```bash
curl https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates
```
Expected: `[]` (empty array if no templates) or list of templates

**If you get 404 Not Found:**
The backend needs to be redeployed to include the templates API endpoints.

## Step 2: Start the Frontend

```bash
cd /Users/abskchsk/Documents/govindjis/wa-app/frontend/template
npm start
```

The app will automatically open at `http://localhost:3000`

## Step 3: Create Your First Template

### Main Menu Template Example

Click "Create New Template" and fill in:

1. **Template Name**: `main_menu`
2. **Template Type**: Select "Button"
3. **Trigger Keywords**: `hi, hello`
4. **Active Template**: ✓ (checked)

5. **Menu Structure**:
   - **Body Text**:
     ```
     Welcome to Govindji's, where you'll experience exquisite craftsmanship and unparalleled quality in Gold and Diamond jewelry that has been trusted for over six decades.
     ```
   
6. **Buttons**: Click "Add Button" three times:
   - Button 1: `Explore our collection`
   - Button 2: `Talk to an expert`
   - Button 3: `Visit us`

7. Click "Create Template"

## Common Issues & Solutions

### Issue 1: "Failed to fetch templates"
**Cause**: Backend not accessible or API not deployed
**Solution**: 
1. Verify backend is running: `curl https://2hdfnnus3x.us-east-1.awsapprunner.com/health`
2. Check if templates API exists in backend
3. Redeploy backend if needed

### Issue 2: CORS Error
**Cause**: Backend not allowing frontend origin
**Solution**: Ensure backend CORS configuration includes localhost:3000

### Issue 3: Port 3000 already in use
**Cause**: Another React app is running
**Solution**: 
- Stop other React apps, or
- Set custom port: `PORT=3001 npm start`

## Testing Checklist

- [ ] Backend health check passes
- [ ] Templates API returns 200 status
- [ ] Frontend starts without errors
- [ ] Can view empty template list
- [ ] Can create new template
- [ ] Can edit existing template
- [ ] Can delete template
- [ ] Template appears in AWS RDS

## API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/templates` | List all templates |
| GET | `/api/templates/{id}` | Get single template |
| POST | `/api/templates` | Create template |
| PUT | `/api/templates/{id}` | Update template |
| DELETE | `/api/templates/{id}` | Delete template |

## Development Tips

### View Console Logs
Open browser DevTools (F12) to see:
- API requests and responses
- Error messages
- Loading states

### Check Network Tab
Monitor API calls to debug issues:
1. Open DevTools → Network tab
2. Filter by "XHR" or "Fetch"
3. Click on requests to see details

### Test with cURL

Create template:
```bash
curl -X POST https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "test_menu",
    "template_type": "button",
    "trigger_keywords": ["test"],
    "is_active": true,
    "menu_structure": {
      "body_text": "Test menu",
      "buttons": [
        {
          "type": "reply",
          "reply": {
            "id": "option1",
            "title": "Option 1"
          }
        }
      ]
    }
  }'
```

## Next Steps After Setup

1. **Create all your templates** using the UI
2. **Test keywords** by sending WhatsApp messages
3. **Monitor logs** to see template triggering
4. **Adjust menu structures** based on user feedback

## Support

If you encounter issues:
1. Check browser console for errors
2. Check backend logs in AWS CloudWatch
3. Verify database connectivity
4. Ensure all migrations are applied

Happy template building! 🎨
