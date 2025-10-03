# WhatsApp Template Quick Start Guide

## 🚀 Quick Examples

### 1. Simple Text Template (Most Common)
```bash
curl -X POST https://your-api.com/messaging/send/template \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "14694652751",
    "template_name": "hello_world",
    "parameters": [
      {"type": "text", "text": "John"}
    ]
  }'
```

### 2. Template in Spanish
```bash
curl -X POST https://your-api.com/messaging/send/template \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "14694652751",
    "template_name": "bienvenida",
    "language_code": "es",
    "parameters": [
      {"type": "text", "text": "Juan"}
    ]
  }'
```

### 3. Template with Image
```bash
curl -X POST https://your-api.com/messaging/send/template \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "14694652751",
    "template_name": "promo_sale",
    "language_code": "en_US",
    "components": [
      {
        "type": "header",
        "parameters": [{
          "type": "image",
          "image": {"link": "https://example.com/promo.jpg"}
        }]
      },
      {
        "type": "body",
        "parameters": [
          {"type": "text", "text": "50%"},
          {"type": "text", "text": "24 hours"}
        ]
      }
    ]
  }'
```

### 4. Order Tracking Template
```bash
curl -X POST https://your-api.com/messaging/send/template \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "14694652751",
    "template_name": "order_shipped",
    "components": [
      {
        "type": "body",
        "parameters": [
          {"type": "text", "text": "ORDER-12345"}
        ]
      },
      {
        "type": "button",
        "sub_type": "url",
        "index": 0,
        "parameters": [
          {"type": "text", "text": "ORDER-12345"}
        ]
      }
    ]
  }'
```

### 5. OTP/Authentication Template
```bash
curl -X POST https://your-api.com/messaging/send/template \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "14694652751",
    "template_name": "auth_otp",
    "components": [
      {
        "type": "body",
        "parameters": [
          {"type": "text", "text": "123456"}
        ]
      },
      {
        "type": "button",
        "sub_type": "url",
        "index": 0,
        "parameters": [
          {"type": "text", "text": "123456"}
        ]
      }
    ]
  }'
```

---

## 📋 Common Language Codes

| Language | Code | Example |
|----------|------|---------|
| English (US) | `en_US` | Default |
| English (UK) | `en_GB` | |
| Spanish | `es` | |
| Spanish (Mexico) | `es_MX` | |
| Portuguese (Brazil) | `pt_BR` | |
| French | `fr` | |
| German | `de` | |
| Italian | `it` | |

---

## 🎨 Component Types Cheat Sheet

### Header Types
```json
// Text
{"type": "header", "parameters": [{"type": "text", "text": "Hello"}]}

// Image
{"type": "header", "parameters": [{"type": "image", "image": {"link": "URL"}}]}

// Video
{"type": "header", "parameters": [{"type": "video", "video": {"link": "URL"}}]}

// Document
{"type": "header", "parameters": [{"type": "document", "document": {"link": "URL", "filename": "file.pdf"}}]}
```

### Body Parameters
```json
{
  "type": "body",
  "parameters": [
    {"type": "text", "text": "value1"},
    {"type": "text", "text": "value2"}
  ]
}
```

### Button Parameters
```json
{
  "type": "button",
  "sub_type": "url",
  "index": 0,
  "parameters": [
    {"type": "text", "text": "dynamic_value"}
  ]
}
```

---

## ⚠️ Common Issues

### Issue: Template not found
**Error:** `Template 'xyz' not found`
**Solution:** Create and approve template in Meta Business Manager

### Issue: User unsubscribed
**Error:** `User has unsubscribed from template messages`
**Solution:** User needs to send a message to re-subscribe

### Issue: Parameter count mismatch
**Error:** `Parameter count mismatch`
**Solution:** Ensure parameter count matches template placeholders ({{1}}, {{2}}, etc.)

### Issue: Language not supported
**Error:** `Template not available in language 'xx'`
**Solution:** Check template is approved for that language in Meta Business Manager

---

## 🔗 Full Documentation

- **Complete Examples:** `docs/template_examples.md`
- **Implementation Details:** `TEMPLATE_ENHANCEMENT_SUMMARY.md`
- **API Endpoint:** `POST /messaging/send/template`
- **Facebook Docs:** https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/

---

## ✅ Features Supported

- ✅ All template categories (Marketing, Utility, Authentication)
- ✅ 60+ languages
- ✅ Header components (text, image, video, document, location)
- ✅ Body parameters
- ✅ Button parameters (URL, phone, quick reply)
- ✅ Multiple components
- ✅ Subscription checking (auto-blocks unsubscribed users)
- ✅ Backward compatible with old format

---

## 🎯 When to Use What

### Marketing Templates
- Promotional campaigns
- Special offers
- Product announcements
- Event invitations

### Utility Templates
- Order confirmations
- Shipping updates
- Appointment reminders
- Account notifications

### Authentication Templates
- OTP codes
- Login verification
- Password reset
- Two-factor authentication

---

## 📞 Need Help?

Check the full documentation in `docs/template_examples.md` for:
- 10 detailed examples
- All component types
- Best practices
- Troubleshooting guide
