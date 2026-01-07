# 🚀 Quick Start: Using the Templates API

## 📍 Base URL
```
https://2hdfnnus3x.us-east-1.awsapprunner.com
```

## 🔗 Quick Reference

### List All Active Templates
```bash
curl "https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/?active_only=true"
```

### Get Template by Name
```bash
curl "https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/by-name/main_menu"
```

### Create Template
```bash
curl -X POST "https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/" \
  -H "Content-Type: application/json" \
  -d @template.json
```

Where `template.json` contains:
```json
{
  "template_name": "my_menu",
  "template_type": "button",
  "trigger_keywords": ["keyword1", "keyword2"],
  "menu_structure": {
    "initial": {
      "message": "Your message here",
      "type": "button",
      "buttons": [
        {"id": "btn1", "title": "Button 1"},
        {"id": "btn2", "title": "Button 2"}
      ],
      "next_steps": {
        "btn1": "step1",
        "btn2": "step2"
      }
    }
  },
  "is_active": true
}
```

### Update Template
```bash
curl -X PUT "https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/{id}" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

### Delete Template
```bash
curl -X DELETE "https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/{id}"
```

### Toggle Active Status
```bash
curl -X POST "https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/{id}/toggle"
```

## 🌐 Interactive Docs
Visit: https://2hdfnnus3x.us-east-1.awsapprunner.com/docs

## 🧪 Run All Tests
```bash
./backend/scripts/test_templates_api.sh
```

## 📚 Full Documentation
- API Reference: `backend/docs/TEMPLATES_API.md`
- Complete Guide: `TEMPLATES_API_COMPLETE.md`

---

**Note**: After deploying the backend, all endpoints will be automatically available. The templates router is already integrated into the main FastAPI app.
