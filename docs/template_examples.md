# WhatsApp Template Message Examples

## Endpoint
```
POST https://your-api-url.com/messaging/send/template
```

## Authentication
```
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

---

## Example 1: Simple Text Template (Backward Compatible)

**Use Case:** Basic template with text parameters in body

**Request:**
```json
{
    "phone_number": "14694652751",
    "template_name": "hello_world",
    "parameters": [
        {"type": "text", "text": "John Doe"}
    ]
}
```

**Template Structure:**
```
Hello {{1}}, welcome to our service!
```

---

## Example 2: Template with Custom Language

**Use Case:** Send template in Spanish

**Request:**
```json
{
    "phone_number": "14694652751",
    "template_name": "bienvenida",
    "language_code": "es",
    "parameters": [
        {"type": "text", "text": "Juan"}
    ]
}
```

---

## Example 3: Template with Image Header

**Use Case:** Welcome message with promotional image

**Request:**
```json
{
    "phone_number": "14694652751",
    "template_name": "welcome_promo",
    "language_code": "en_US",
    "components": [
        {
            "type": "header",
            "parameters": [
                {
                    "type": "image",
                    "image": {
                        "link": "https://example.com/promo-image.jpg"
                    }
                }
            ]
        },
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": "John"},
                {"type": "text", "text": "Premium"}
            ]
        }
    ]
}
```

**Template Structure:**
```
[IMAGE HEADER]

Welcome {{1}}! You've been upgraded to {{2}} tier.

Click the button below to explore your benefits.
```

---

## Example 4: Template with Document Header

**Use Case:** Send invoice with PDF attachment

**Request:**
```json
{
    "phone_number": "14694652751",
    "template_name": "invoice_ready",
    "language_code": "en",
    "components": [
        {
            "type": "header",
            "parameters": [
                {
                    "type": "document",
                    "document": {
                        "link": "https://example.com/invoice-12345.pdf",
                        "filename": "Invoice_12345.pdf"
                    }
                }
            ]
        },
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": "John Doe"},
                {"type": "text", "text": "INV-12345"},
                {"type": "text", "text": "$299.99"}
            ]
        }
    ]
}
```

---

## Example 5: Template with Video Header

**Use Case:** Product demonstration video

**Request:**
```json
{
    "phone_number": "14694652751",
    "template_name": "product_demo",
    "language_code": "en_US",
    "components": [
        {
            "type": "header",
            "parameters": [
                {
                    "type": "video",
                    "video": {
                        "link": "https://example.com/product-demo.mp4"
                    }
                }
            ]
        },
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": "Premium Widget"}
            ]
        }
    ]
}
```

---

## Example 6: Template with Dynamic Button URL

**Use Case:** Order tracking link with dynamic order ID

**Request:**
```json
{
    "phone_number": "14694652751",
    "template_name": "order_shipped",
    "language_code": "en",
    "components": [
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": "John"},
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
}
```

**Template Structure:**
```
Hi {{1}},

Your order {{2}} has been shipped!

[Track Package] (button with URL: https://example.com/track/{{1}})
```

---

## Example 7: Authentication/OTP Template

**Use Case:** Send one-time password for login

**Request:**
```json
{
    "phone_number": "14694652751",
    "template_name": "auth_otp",
    "language_code": "en",
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
}
```

**Template Structure:**
```
Your verification code is: {{1}}

This code expires in 10 minutes.

[Autofill Code] (button with OTP: {{1}})
```

---

## Example 8: Multi-Button Template

**Use Case:** Template with multiple action buttons

**Request:**
```json
{
    "phone_number": "14694652751",
    "template_name": "appointment_reminder",
    "language_code": "en_US",
    "components": [
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": "Dr. Smith"},
                {"type": "text", "text": "Tomorrow at 2:00 PM"}
            ]
        },
        {
            "type": "button",
            "sub_type": "url",
            "index": 0,
            "parameters": [
                {"type": "text", "text": "APT-789"}
            ]
        }
    ]
}
```

**Template Structure:**
```
Reminder: You have an appointment with {{1}} on {{2}}.

[View Details] (button 1 - URL)
[Call to Confirm] (button 2 - Phone)
[Cancel] (button 3 - Quick Reply)
```

---

## Example 9: Complex Marketing Template

**Use Case:** Promotional campaign with all components

**Request:**
```json
{
    "phone_number": "14694652751",
    "template_name": "flash_sale",
    "language_code": "en",
    "components": [
        {
            "type": "header",
            "parameters": [
                {
                    "type": "image",
                    "image": {
                        "link": "https://example.com/flash-sale-banner.jpg"
                    }
                }
            ]
        },
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": "Sarah"},
                {"type": "text", "text": "50%"},
                {"type": "text", "text": "6 hours"}
            ]
        },
        {
            "type": "button",
            "sub_type": "url",
            "index": 0,
            "parameters": [
                {"type": "text", "text": "FLASH50"}
            ]
        }
    ]
}
```

**Template Structure:**
```
[PROMO IMAGE HEADER]

Hi {{1}}! 🎉

Flash Sale Alert! Get {{2}} off everything! 

⏰ Offer expires in {{3}}

Use code at checkout: FLASH50

[Shop Now] (button with URL including promo code)

Terms and conditions apply.
```

---

## Example 10: Location-Based Template

**Use Case:** Store opening with location header

**Request:**
```json
{
    "phone_number": "14694652751",
    "template_name": "store_opening",
    "language_code": "en_US",
    "components": [
        {
            "type": "header",
            "parameters": [
                {
                    "type": "location",
                    "location": {
                        "latitude": 37.7749,
                        "longitude": -122.4194,
                        "name": "Our New Store",
                        "address": "123 Market St, San Francisco, CA"
                    }
                }
            ]
        },
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": "San Francisco"},
                {"type": "text", "text": "Saturday, March 15th"}
            ]
        }
    ]
}
```

---

## Supported Languages

Common language codes:
- `en` or `en_US` - English (US)
- `en_GB` - English (UK)
- `es` - Spanish
- `es_MX` - Spanish (Mexico)
- `pt_BR` - Portuguese (Brazil)
- `fr` - French
- `de` - German
- `it` - Italian
- `ja` - Japanese
- `ko` - Korean
- `zh_CN` - Chinese (Simplified)
- `zh_TW` - Chinese (Traditional)
- `ar` - Arabic
- `hi` - Hindi
- `ru` - Russian

---

## Component Types

### Header Component
```json
{
    "type": "header",
    "parameters": [
        // One of: text, image, video, document, location
    ]
}
```

### Body Component
```json
{
    "type": "body",
    "parameters": [
        {"type": "text", "text": "value1"},
        {"type": "text", "text": "value2"}
    ]
}
```

### Button Component
```json
{
    "type": "button",
    "sub_type": "url",  // or "quick_reply"
    "index": 0,  // button position (0, 1, 2)
    "parameters": [
        {"type": "text", "text": "dynamic_value"}
    ]
}
```

---

## Response Format

**Success (202 Accepted):**
```json
{
    "status": "queued",
    "message_id": "msg_abc123",
    "phone_number": "14694652751",
    "message_type": "template",
    "template_name": "hello_world",
    "language_code": "en_US",
    "subscription_status": "subscribed",
    "estimated_processing_time": "1-5 minutes"
}
```

**User Unsubscribed (403 Forbidden):**
```json
{
    "status": "blocked",
    "message": "User has unsubscribed from template messages",
    "phone_number": "14694652751",
    "reason": "User sent STOP command to opt-out"
}
```

---

## Testing Tips

1. **Start Simple:** Test with basic text parameters first
2. **Test Language:** Ensure template is approved for the language code
3. **Media URLs:** Use publicly accessible URLs for headers
4. **Button Index:** Match the button order in your template
5. **Parameter Count:** Must match placeholders in template
6. **Subscription:** User must be subscribed to receive templates

---

## Common Errors

### Error: Template Not Found
```
Template 'xyz' not found or not approved
```
**Solution:** Ensure template is created and approved in Meta Business Manager

### Error: Invalid Language
```
Template not available in language 'xx'
```
**Solution:** Check approved languages for the template

### Error: Parameter Mismatch
```
Parameter count mismatch
```
**Solution:** Ensure parameter count matches template placeholders

### Error: User Unsubscribed
```
User has unsubscribed from template messages
```
**Solution:** User needs to send a message to re-subscribe

---

## Best Practices

1. **Use appropriate language codes** based on user preference
2. **Keep media files optimized** - images < 5MB, videos < 16MB
3. **Test templates** before sending to customers
4. **Monitor delivery rates** via analytics
5. **Respect opt-outs** - system automatically blocks unsubscribed users
6. **Use marketing templates** only for promotional content
7. **Use utility templates** for transactional messages (orders, shipping, etc.)
8. **Use authentication templates** only for OTP/verification codes

---

## Need Help?

- Check template approval status in Meta Business Manager
- Review WhatsApp Business API documentation
- Contact support for template creation assistance
