# Template Management System - Testing Checklist

## Pre-Flight Checklist

Before testing, ensure:

- [ ] Backend server is running (`uvicorn app.main:app --reload`)
- [ ] Frontend server is running (`npm start`)
- [ ] Database connection is working
- [ ] `workflow_templates` table exists in database
- [ ] Browser console is open (F12) for debugging

## Backend API Testing

### 1. List Templates
```bash
curl http://localhost:8000/templates
```
**Expected:** 200 OK with array (may be empty initially)

### 2. Create Template
```bash
curl -X POST http://localhost:8000/templates \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "test_menu",
    "template_type": "button",
    "trigger_keywords": ["test"],
    "menu_structure": {
      "body": "Test menu",
      "footer": "Select option",
      "steps": {
        "initial": {
          "type": "button",
          "buttons": [
            {"id": "test1", "title": "Test 1"}
          ],
          "next_steps": {}
        }
      }
    },
    "is_active": true
  }'
```
**Expected:** 201 Created with template object

### 3. Get Template by ID
```bash
# Replace {id} with actual template ID from step 2
curl http://localhost:8000/templates/{id}
```
**Expected:** 200 OK with template object

### 4. Update Template
```bash
# Replace {id} with actual template ID
curl -X PUT http://localhost:8000/templates/{id} \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```
**Expected:** 200 OK with updated template

### 5. Toggle Status
```bash
# Replace {id} with actual template ID
curl -X POST http://localhost:8000/templates/{id}/toggle
```
**Expected:** 200 OK with status message

### 6. Delete Template
```bash
# Replace {id} with actual template ID
curl -X DELETE http://localhost:8000/templates/{id}
```
**Expected:** 200 OK with deletion confirmation

## Frontend UI Testing

### Page Load
- [ ] Navigate to http://localhost:3000/templates
- [ ] Page loads without errors
- [ ] No console errors
- [ ] "Templates" menu item is highlighted
- [ ] "Create Template" button is visible

### List View (Empty State)
- [ ] Shows "No templates found" if database is empty
- [ ] Shows "Create Your First Template" button
- [ ] Search box is visible
- [ ] Filter dropdowns are visible

### Create Template
- [ ] Click "Create Template" button
- [ ] Modal opens with form
- [ ] All fields are visible:
  - [ ] Template Name
  - [ ] Template Type dropdown
  - [ ] Active checkbox (checked by default)
  - [ ] Keywords section with input
  - [ ] Body text textarea
  - [ ] Footer text input
  - [ ] Buttons section (for button type)

### Add Keywords
- [ ] Type "hi" in keyword input
- [ ] Click + button or press Enter
- [ ] Keyword appears as tag below
- [ ] Can add multiple keywords
- [ ] Can remove keywords with X button
- [ ] Duplicate keywords are rejected

### Add Buttons
- [ ] Type "Explore Collection" in button input
- [ ] Click + button or press Enter
- [ ] Button appears in list below
- [ ] Can add up to 3 buttons
- [ ] + button disables after 3 buttons
- [ ] Can remove buttons with trash icon

### Form Validation
- [ ] Submit empty form → Shows validation errors
- [ ] Submit without template name → Error
- [ ] Submit without body text → Error
- [ ] Submit with valid data → Success

### Create Success
- [ ] Form submits successfully
- [ ] Modal closes
- [ ] Template appears in list
- [ ] No errors in console

### Template Card Display
- [ ] Template name is shown
- [ ] Type badge displays correct color
  - [ ] Blue for button
  - [ ] Purple for list
  - [ ] Green for text
- [ ] Status badge shows (Active/Inactive)
- [ ] Keywords appear as tags
- [ ] Menu structure preview is visible
- [ ] Timestamps are formatted correctly
- [ ] Action buttons are visible (toggle, edit, delete)

### Search Functionality
- [ ] Type in search box
- [ ] Templates filter in real-time
- [ ] Matches template name
- [ ] Matches keywords
- [ ] Empty search shows all templates

### Filter by Type
- [ ] Select "Button Templates"
- [ ] Only button templates shown
- [ ] Select "List Templates"
- [ ] Only list templates shown
- [ ] Select "All Types"
- [ ] All templates shown

### Filter by Status
- [ ] Select "Active Only"
- [ ] Only active templates shown
- [ ] Select "Inactive Only"
- [ ] Only inactive templates shown
- [ ] Select "All Status"
- [ ] All templates shown

### Toggle Status
- [ ] Click toggle icon on active template
- [ ] Icon changes to inactive (gray with left arrow)
- [ ] Badge changes to "Inactive"
- [ ] Click toggle again
- [ ] Icon changes to active (green with right arrow)
- [ ] Badge changes to "Active"

### Edit Template
- [ ] Click edit icon (✏️)
- [ ] Modal opens with form
- [ ] All fields populated with existing data
- [ ] Template name field is disabled
- [ ] Modify keywords
- [ ] Modify body text
- [ ] Modify buttons
- [ ] Click "Update"
- [ ] Modal closes
- [ ] Changes reflected in list
- [ ] No errors

### Delete Template
- [ ] Click delete icon (🗑️)
- [ ] Confirmation modal appears
- [ ] Click "Cancel" → Modal closes, template remains
- [ ] Click delete icon again
- [ ] Click "Delete" → Template removed from list
- [ ] No errors

### Responsive Design
- [ ] Resize browser window
- [ ] Layout adjusts appropriately
- [ ] Mobile view works correctly
- [ ] No horizontal scrolling
- [ ] Buttons remain accessible

### Error Handling
- [ ] Stop backend server
- [ ] Try to load templates → Error message shown
- [ ] Try to create template → Error message shown
- [ ] Start backend server
- [ ] Click retry → Templates load successfully

### Animation & UX
- [ ] Button hover effects work
- [ ] Button click animations work
- [ ] Modal open/close is smooth
- [ ] Template cards fade in
- [ ] Loading spinner appears during API calls

## Integration Testing

### End-to-End Conversation Flow
1. [ ] Create template via UI:
   ```
   Name: main_menu
   Type: button
   Keywords: hi, hello
   Body: Welcome to our service!
   Buttons: Option 1, Option 2, Option 3
   Active: ✓
   ```
2. [ ] Verify template appears in list
3. [ ] Send "hi" to your WhatsApp test number
4. [ ] Check backend logs for:
   ```
   🎯 Template 'main_menu' matched keyword 'hi'
   🆕 Started conversation: {phone} -> main_menu
   ```
5. [ ] Verify interactive message is sent
6. [ ] Check WhatsApp - buttons should appear
7. [ ] Click a button
8. [ ] Verify response is handled

### Database Verification
```sql
-- Check template was created
SELECT * FROM workflow_templates WHERE template_name = 'main_menu';

-- Check conversation state was created
SELECT * FROM conversation_state WHERE conversation_flow = 'main_menu';
```

### Template Triggers
- [ ] Create template with keyword "start"
- [ ] Send "start" → Template triggers
- [ ] Send "START" (uppercase) → Still triggers (case insensitive)
- [ ] Send "starting" → Should not trigger (exact match)
- [ ] Deactivate template
- [ ] Send "start" → Should not trigger (uses fallback)

## Performance Testing

### Large Dataset
- [ ] Create 10+ templates
- [ ] List loads quickly (< 1 second)
- [ ] Search is responsive
- [ ] Filters apply quickly
- [ ] No lag in UI

### Concurrent Operations
- [ ] Create template
- [ ] Immediately create another
- [ ] Both succeed
- [ ] No conflicts

## Browser Compatibility

Test in multiple browsers:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (if on Mac)
- [ ] Edge

## Common Issues & Solutions

### Templates Not Loading
**Issue:** Empty list, no error  
**Check:** Backend running? Database connected? Console errors?  
**Fix:** Start backend, verify DB connection

### Form Not Submitting
**Issue:** Button click does nothing  
**Check:** Console errors? All required fields filled?  
**Fix:** Fill required fields, check validation

### Template Not Triggering
**Issue:** Send keyword but no template  
**Check:** Is template active? Keyword exact match? Backend logs?  
**Fix:** Verify active status, check keyword spelling, review logs

### Buttons Not Appearing in WhatsApp
**Issue:** Message sent but no buttons  
**Check:** Template type is "button"? Message handler working?  
**Fix:** Verify template type, check message_handler.py logs

### API Endpoint Not Found
**Issue:** 404 error  
**Check:** Templates router registered in main.py?  
**Fix:** Verify router import and app.include_router call

## Success Criteria

System is working correctly when:

✅ All backend API endpoints return correct responses  
✅ Frontend loads without errors  
✅ Can create templates via UI  
✅ Can edit templates  
✅ Can delete templates  
✅ Search and filters work  
✅ Toggle changes status  
✅ Templates are stored in database  
✅ Templates trigger on keyword match  
✅ Interactive messages are sent to WhatsApp  
✅ No console errors  
✅ No backend exceptions  

## Post-Deployment Checklist

Before going to production:

- [ ] Remove test templates
- [ ] Create production templates
- [ ] Test with real WhatsApp number
- [ ] Verify SSL/HTTPS
- [ ] Check error logging
- [ ] Set up monitoring
- [ ] Document custom templates
- [ ] Train team on UI usage
- [ ] Set up backup for templates

---

**Date Tested:** _____________  
**Tested By:** _____________  
**All Tests Passed:** ☐ Yes ☐ No  
**Notes:** _____________________________________________
