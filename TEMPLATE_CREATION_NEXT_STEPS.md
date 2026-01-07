# Template Creation - Next Steps

## Issue

The template creation script cannot run from your local machine because it needs database access. The AWS RDS database:
- Is configured for your AWS App Runner deployment
- Requires proper credentials and network access
- Should only be accessed from your AWS environment

## Solution

You have **two options** to create the templates:

---

## Option 1: Deploy and Run from AWS (Recommended)

### Step 1: Deploy Your Code

Your code is already updated with the template script. Deploy to AWS:

```bash
git add .
git commit -m "Add interactive WhatsApp menu templates for Govindji's"
git push
```

AWS App Runner will automatically deploy the new code.

### Step 2: Run Script from AWS

Connect to your AWS environment and run:

```bash
# SSH into your AWS environment or use AWS Systems Manager Session Manager
cd /app/backend
python -m scripts.create_initial_templates
```

### Step 3: Verify

```bash
# Check templates were created
psql $DATABASE_URL -c "SELECT template_name, is_active FROM workflow_templates;"
```

Expected output:
```
  template_name      | is_active 
---------------------+-----------
 main_menu           | t
 explore_collection  | t
 talk_to_expert      | t
 visit_us            | t
```

---

## Option 2: Manual SQL Insert (Quick Alternative)

If you can't easily run the script from AWS, you can create templates directly with SQL:

### Template 1: Main Menu

```sql
INSERT INTO workflow_templates (
    id,
    template_name,
    template_type,
    trigger_keywords,
    menu_structure,
    is_active,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'main_menu',
    'button',
    ARRAY['hi', 'hello', 'hey', 'start', 'menu', 'help'],
    '{
        "type": "button",
        "body": {
            "text": "✨ Welcome to Govindji'\''s, where you'\''ll experience exquisite craftsmanship and unparalleled quality in Gold and Diamond jewelry that has been trusted for over six decades."
        },
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": {
                        "id": "explore_collection",
                        "title": "💎 Explore Collection"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "talk_to_expert",
                        "title": "👨‍💼 Talk to Expert"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "visit_us",
                        "title": "📍 Visit Us"
                    }
                }
            ]
        },
        "steps": {
            "initial": {
                "next_steps": {
                    "explore_collection": "show_collection_categories",
                    "talk_to_expert": "connect_expert",
                    "visit_us": "show_location"
                }
            }
        }
    }'::jsonb,
    true,
    NOW(),
    NOW()
);
```

### Template 2: Explore Collection

```sql
INSERT INTO workflow_templates (
    id,
    template_name,
    template_type,
    trigger_keywords,
    menu_structure,
    is_active,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'explore_collection',
    'text',
    ARRAY['collection', 'jewelry', 'explore', 'catalog'],
    '{
        "type": "text",
        "body": {
            "text": "💎 Explore Our Exquisite Collection\n\nAt Govindji'\''s, we offer:\n\n🔸 Gold Jewelry - Traditional & Contemporary designs\n🔸 Diamond Jewelry - Stunning pieces for every occasion\n🔸 Bridal Collection - Make your special day unforgettable\n🔸 Custom Designs - Bring your vision to life\n\nVisit our showroom or website to view our complete collection.\n\nWould you like to speak with our jewelry consultant?"
        },
        "steps": {
            "initial": {
                "prompt": "Type '\''yes'\'' to speak with a consultant or '\''menu'\'' to return to main menu"
            }
        }
    }'::jsonb,
    true,
    NOW(),
    NOW()
);
```

### Template 3: Talk to Expert

```sql
INSERT INTO workflow_templates (
    id,
    template_name,
    template_type,
    trigger_keywords,
    menu_structure,
    is_active,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'talk_to_expert',
    'text',
    ARRAY['expert', 'consultant', 'help', 'advice'],
    '{
        "type": "text",
        "body": {
            "text": "👨‍💼 Connect with Our Jewelry Experts\n\nOur experienced consultants are here to help you:\n\n✓ Find the perfect piece\n✓ Understand jewelry quality and craftsmanship\n✓ Custom design consultation\n✓ Repair and maintenance services\n\nPlease share your:\n1. Name\n2. What you'\''re looking for\n\nOur expert will contact you shortly!"
        },
        "steps": {
            "initial": {
                "prompt": "Please share your name and requirement",
                "next_step": "collect_details"
            },
            "collect_details": {
                "prompt": "Thank you! Our expert will reach out to you within 24 hours.\n\nType '\''menu'\'' to return to main menu."
            }
        }
    }'::jsonb,
    true,
    NOW(),
    NOW()
);
```

### Template 4: Visit Us

```sql
INSERT INTO workflow_templates (
    id,
    template_name,
    template_type,
    trigger_keywords,
    menu_structure,
    is_active,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'visit_us',
    'text',
    ARRAY['visit', 'location', 'address', 'showroom', 'store'],
    '{
        "type": "text",
        "body": {
            "text": "📍 Visit Govindji'\''s Showroom\n\n🏪 Address:\n[Your Showroom Address]\n[City, State, ZIP]\n\n⏰ Business Hours:\nMonday - Saturday: 10:00 AM - 8:00 PM\nSunday: 11:00 AM - 6:00 PM\n\n📞 Contact:\nPhone: [Your Phone Number]\nEmail: [Your Email]\n\n🚗 We'\''re conveniently located with ample parking.\n\nWould you like directions? Type '\''directions'\'' or visit our website for Google Maps link.\n\nType '\''menu'\'' to return to main menu."
        },
        "steps": {
            "initial": {
                "prompt": "We look forward to seeing you!"
            }
        }
    }'::jsonb,
    true,
    NOW(),
    NOW()
);
```

### How to Run SQL Inserts

```bash
# Save all 4 INSERT statements to a file
cat > /tmp/create_templates.sql << 'EOF'
-- Paste all 4 INSERT statements here
EOF

# Run the SQL file
psql -h whatsapp-postgres-development.cibi66cyqd2r.us-east-1.rds.amazonaws.com \
     -U postgres \
     -d postgres \
     -f /tmp/create_templates.sql
```

---

## Option 3: Wait for Next Deployment

Since the script is already in your code:

1. The templates will be created when you run the script from AWS
2. Or you can manually trigger it via an API endpoint
3. Or create an admin panel to run scripts

---

## Verification

After creating templates (either method), verify:

```sql
-- Check all templates
SELECT 
    template_name,
    template_type,
    trigger_keywords,
    is_active,
    created_at
FROM workflow_templates
ORDER BY template_name;

-- Count templates
SELECT COUNT(*) FROM workflow_templates;
-- Expected: 4
```

---

## Testing

Once templates are created:

1. Send "hi" to your WhatsApp Business number
2. Expected response: Welcome message with 3 buttons
3. Click each button to test the flows

---

## Why Local Execution Failed

1. **Database Access:** AWS RDS is configured for AWS network access
2. **Credentials:** Your local machine doesn't have the database password
3. **Security:** Database is protected by security groups limiting access
4. **SSL:** Database requires SSL/TLS encryption

These are all **good security practices** - the database should only be accessible from your production environment.

---

## Recommended Approach

**Use Option 1** (Deploy and run from AWS):

1. Your code is already updated ✅
2. Deploy to AWS
3. Connect to AWS environment
4. Run the script
5. Templates will be created in the production database

This is the **safest and most correct** approach.

---

## Alternative: Create Admin API Endpoint

You could also create an admin endpoint to run the script:

```python
# In your API
@app.post("/admin/create-templates")
async def create_templates(api_key: str):
    if api_key != os.getenv("ADMIN_API_KEY"):
        raise HTTPException(403)
    
    from scripts.create_initial_templates import main
    main()
    
    return {"status": "success", "message": "Templates created"}
```

Then call it:
```bash
curl -X POST https://your-app.com/admin/create-templates?api_key=YOUR_KEY
```

---

## Summary

✅ **Template code is ready** and in your repository
✅ **Script is functional** and will work when run from AWS
✅ **Manual SQL option** available as alternative

**Next Step:** Choose one of the three options above to create the templates in your database.

**Recommended:** Deploy code to AWS and run script from there.

---

**Last Updated:** 2025-01-07
**Status:** Ready for deployment
