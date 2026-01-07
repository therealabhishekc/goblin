# 🚀 Template Management System - Quick Reference

## Access Points

| Resource | URL |
|----------|-----|
| 🖥️ Frontend UI | http://localhost:3000/templates |
| 🔌 Backend API | http://localhost:8000/templates |
| 📚 API Docs | http://localhost:8000/docs |

## Common Commands

### Start Servers
```bash
# Backend
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend/app && npm start
```

### Test API
```bash
# List templates
curl http://localhost:8000/templates

# Create template
curl -X POST http://localhost:8000/templates \
  -H "Content-Type: application/json" \
  -d '{"template_name":"test","template_type":"button","menu_structure":{"body":"Test"}}'
```

## File Locations

```
Backend API:    backend/app/api/templates.py
Frontend UI:    frontend/app/src/pages/templates/
Data Models:    backend/app/models/conversation.py
API Service:    frontend/app/src/services/api.js
```

## Quick Actions

### Create Template (UI)
1. Go to /templates
2. Click "Create Template"
3. Fill form → Submit

### Edit Template (UI)
1. Find template in list
2. Click edit icon (✏️)
3. Modify → Update

### Delete Template (UI)
1. Find template
2. Click delete icon (🗑️)
3. Confirm

## API Endpoints

```
GET    /templates              List all
GET    /templates/{id}         Get by ID
POST   /templates              Create
PUT    /templates/{id}         Update
DELETE /templates/{id}         Delete
POST   /templates/{id}/toggle  Toggle status
```

## Template Structure

```json
{
  "template_name": "main_menu",
  "template_type": "button",
  "trigger_keywords": ["hi", "hello"],
  "menu_structure": {
    "body": "Welcome!",
    "footer": "Select option",
    "steps": {
      "initial": {
        "type": "button",
        "buttons": [
          {"id": "opt1", "title": "Option 1"}
        ],
        "next_steps": {}
      }
    }
  },
  "is_active": true
}
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Templates not loading | Check backend running, DB connected |
| Form not submitting | Fill all required fields |
| Template not triggering | Verify active status, check keyword |
| API 404 error | Verify router registered in main.py |

## Key Features

✅ Create/Edit/Delete templates  
✅ Search and filter  
✅ Quick toggle active/inactive  
✅ Keyword management  
✅ Button management (max 3)  
✅ Real-time validation  
✅ Beautiful glassmorphism UI  

## Documentation

- 📖 `TEMPLATE_SYSTEM_COMPLETE.md` - Quick start
- 📖 `docs/TEMPLATE_MANAGEMENT_SYSTEM.md` - Full docs
- 📖 `docs/TEMPLATE_SYSTEM_ARCHITECTURE.md` - Architecture
- 📖 `docs/TEMPLATE_TESTING_CHECKLIST.md` - Testing
- 📖 `IMPLEMENTATION_SUMMARY.md` - Summary

## Database Query

```sql
-- View all templates
SELECT * FROM workflow_templates;

-- Active templates only
SELECT * FROM workflow_templates WHERE is_active = true;

-- Find by keyword
SELECT * FROM workflow_templates 
WHERE 'hi' = ANY(trigger_keywords);
```

## Success Indicators

✅ Frontend loads without errors  
✅ Can create templates via UI  
✅ Templates saved in database  
✅ Keywords trigger templates  
✅ Interactive messages sent  

## Support

Check logs:
- Backend: Console output
- Frontend: Browser console (F12)
- Database: SQL logs

Review docs in `/docs/` folder

---

**Version:** 1.0.0  
**Status:** ✅ Complete
