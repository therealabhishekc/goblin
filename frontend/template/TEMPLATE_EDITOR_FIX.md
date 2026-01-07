# Template Editor Fix - Menu Structure Display

## Problem
When clicking the edit icon on any template, the menu structure (header text, body text, footer text, and buttons) was not being displayed in the edit form.

## Root Cause
The database stores the menu structure in a nested format:
```json
{
  "menu_structure": {
    "header": { "text": "Header content" },
    "body": { "text": "Body content" },
    "footer": { "text": "Footer content" },
    "action": {
      "buttons": [
        {
          "type": "reply",
          "reply": {
            "id": "button_id",
            "title": "Button Text"
          }
        }
      ]
    }
  }
}
```

But the form was expecting a flat structure:
```json
{
  "menu_structure": {
    "header_text": "Header content",
    "body_text": "Body content",
    "footer_text": "Footer content",
    "buttons": [...]
  }
}
```

## Solution

### 1. Updated `TemplateForm.js` - Data Loading (Lines 20-38)
**Fixed the `useEffect` hook to properly parse the database structure:**
```javascript
useEffect(() => {
  if (template) {
    // Parse the actual menu_structure from database
    const menuStruct = template.menu_structure || {};
    
    // Extract values from the database structure
    const headerText = menuStruct.header?.text || '';
    const bodyText = menuStruct.body?.text || '';
    const footerText = menuStruct.footer?.text || '';
    const buttons = menuStruct.action?.buttons || [];
    
    setFormData({
      // ... set extracted values
    });
  }
}, [template]);
```

### 2. Updated `TemplateForm.js` - Data Submission (Lines 115-161)
**Fixed the submit handler to format data correctly for the backend:**
```javascript
// Format menu_structure to match backend expectations
const menuStructure = {
  type: formData.template_type,
};

// Add body text if present
if (formData.menu_structure.body_text) {
  menuStructure.body = {
    text: formData.menu_structure.body_text
  };
}

// Add header text if present
if (formData.menu_structure.header_text) {
  menuStructure.header = {
    text: formData.menu_structure.header_text
  };
}

// Add footer text if present
if (formData.menu_structure.footer_text) {
  menuStructure.footer = {
    text: formData.menu_structure.footer_text
  };
}

// Add buttons/action if button type
if (formData.template_type === 'button' && buttons.length > 0) {
  menuStructure.action = {
    buttons: buttons
  };
}
```

### 3. Updated `TemplateList.js` - Display Preview (Lines 72-110)
**Fixed the template preview to show data from both possible structures:**
```javascript
{(template.menu_structure.header_text || template.menu_structure.header?.text) && (
  <p className="menu-text">{template.menu_structure.header_text || template.menu_structure.header?.text}</p>
)}
{(template.menu_structure.body_text || template.menu_structure.body?.text) && (
  <p className="menu-text">{template.menu_structure.body_text || template.menu_structure.body?.text}</p>
)}
{(template.menu_structure.footer_text || template.menu_structure.footer?.text) && (
  <p className="menu-footer">{template.menu_structure.footer_text || template.menu_structure.footer?.text}</p>
)}
```

**Fixed button display to handle nested reply structure:**
```javascript
{template.menu_structure.action?.buttons && (
  <div className="menu-buttons">
    {template.menu_structure.action.buttons.map((btn, idx) => (
      <div key={idx} className="menu-button">
        {btn.reply?.title || btn.text || btn.title}
      </div>
    ))}
  </div>
)}
```

## Testing

### Access the Template Manager
The template manager is now running at:
- **Local:** http://localhost:3006
- **Network:** http://192.168.88.12:3006

### Test Steps
1. **View Templates:** You should see all templates with their menu structure displayed correctly
2. **Edit Template:** Click the edit icon (✏️) on any template
3. **Verify Display:** The form should now show:
   - Header text (if present)
   - Body text ✓
   - Footer text (if present)
   - All buttons with their titles ✓

4. **Test Edit:** Make changes and save to verify the data is correctly formatted for the backend

## Current Template Structure in Database

### Main Menu Template
```json
{
  "template_name": "main_menu",
  "template_type": "button",
  "trigger_keywords": ["hi", "hello", "hey", "start", "menu", "help"],
  "menu_structure": {
    "body": {
      "text": "✨ Welcome to Govindji's, where you'll experience exquisite craftsmanship..."
    },
    "type": "button",
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
    }
  }
}
```

## Files Modified
1. `/frontend/template/src/components/TemplateForm.js`
   - Updated data loading logic in `useEffect`
   - Updated data submission logic in `handleSubmit`

2. `/frontend/template/src/components/TemplateList.js`
   - Updated template preview to handle both data structures
   - Fixed button title display

## Status
✅ **FIXED** - Template edit form now properly displays all menu structure fields including header, body, footer, and buttons.
