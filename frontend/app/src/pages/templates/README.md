# Template Management UI

## Overview

A complete React-based user interface for managing WhatsApp interactive menu templates. This system allows you to create, edit, delete, and manage workflow templates through a modern glassmorphism UI.

## Location

```
frontend/app/src/pages/templates/
├── TemplateManagement.js  # Main list/management page
├── TemplateForm.js         # Create/Edit form modal
└── index.js                # Export file
```

## Features

### TemplateManagement Component

**Main Features:**
- 📋 List all templates in a responsive grid
- 🔍 Real-time search by name or trigger keywords
- 🎯 Filter by template type (button/list/text)
- ✅ Filter by status (active/inactive/all)
- 🔄 Quick toggle active/inactive status
- ✏️ Edit templates via modal
- 🗑️ Delete with confirmation
- 🎨 Modern glassmorphism design
- ⚡ Animated transitions

**UI Elements:**
- Template cards showing:
  - Template name and type icon
  - Status badges (active/inactive)
  - Trigger keywords as tags
  - Menu structure preview
  - Creation/update timestamps
  - Action buttons (toggle, edit, delete)

### TemplateForm Component

**Form Features:**
- ✨ Create new templates
- ✏️ Edit existing templates
- 📝 Full validation
- ⚠️ Error handling
- 💾 Auto-save on submit

**Form Fields:**
1. **Template Name** (required, unique, immutable after creation)
2. **Template Type** (button/list/text)
3. **Active Status** (checkbox)
4. **Trigger Keywords** (dynamic array with add/remove)
5. **Menu Structure:**
   - Body Text (required)
   - Footer Text (optional)
   - Buttons (for button type, max 3)

**Keyboard Shortcuts:**
- `Enter` in keyword input → Add keyword
- `Enter` in button input → Add button
- `Escape` → Close form (when implemented)

## Usage Guide

### Accessing the UI

1. Start the frontend application
2. Navigate to `/templates` route
3. Or click "Templates" in the navigation menu

### Creating a Template

1. Click the "Create Template" button (top right)
2. Fill in the form:
   ```
   Template Name: main_menu
   Template Type: Button
   Active: ✓ Checked
   
   Trigger Keywords:
   - hi
   - hello
   - menu
   
   Body Text:
   Welcome to our service! How can we help you today?
   
   Footer Text:
   Select an option below
   
   Buttons:
   - Explore Collection
   - Talk to Expert
   - Visit Us
   ```
3. Click "Create"
4. Template will appear in the list immediately

### Editing a Template

1. Find the template in the list
2. Click the blue edit icon (✏️)
3. Modify any fields (except template name)
4. Click "Update"

**Note:** Template name cannot be changed after creation. If you need a different name, create a new template.

### Deleting a Template

1. Click the red delete icon (🗑️)
2. Confirm deletion in the modal
3. Template is permanently removed

**Warning:** This action cannot be undone!

### Toggling Status

- Click the toggle icon to quickly activate/deactivate
- Green icon with arrow right = Active
- Gray icon with arrow left = Inactive
- Only active templates trigger in conversations

### Searching & Filtering

**Search:**
- Type in the search box to filter by:
  - Template name
  - Trigger keywords

**Type Filter:**
- All Types (default)
- Button Templates
- List Templates
- Text Templates

**Status Filter:**
- All Status (default)
- Active Only
- Inactive Only

## API Integration

The UI communicates with the backend via these methods:

```javascript
// Get all templates with optional filters
apiService.getTemplates({ 
  is_active: true,
  template_type: 'button'
})

// Get single template by ID
apiService.getTemplateById(id)

// Get by name
apiService.getTemplateByName('main_menu')

// Create new template
apiService.createTemplate({
  template_name: 'main_menu',
  template_type: 'button',
  trigger_keywords: ['hi', 'hello'],
  menu_structure: { ... },
  is_active: true
})

// Update template
apiService.updateTemplate(id, {
  is_active: false,
  trigger_keywords: ['hi', 'hello', 'start']
})

// Delete template
apiService.deleteTemplate(id)

// Toggle active status
apiService.toggleTemplateStatus(id)
```

## Component Props

### TemplateManagement
No props required - self-contained component

### TemplateForm
```javascript
<TemplateForm
  template={templateObject}  // null for create, object for edit
  onClose={() => {}}         // Called when form is closed
  onSuccess={() => {}}       // Called after successful save
/>
```

## Styling

Uses the glassmorphism design system:

**CSS Classes:**
- `.glass-card` - Card containers
- `.btn-primary` - Primary action buttons
- `.input-field` - Form inputs
- `.text-gradient` - Gradient text headings

**Colors:**
- Blue: Button type templates
- Purple: List type templates  
- Green: Text type templates
- Active status: Green
- Inactive status: Gray
- Error: Red

## State Management

**TemplateManagement State:**
```javascript
templates        // Array of template objects
loading          // Boolean for loading state
error            // Error message string
searchTerm       // Search input value
filterType       // Current type filter
filterActive     // Current status filter
showForm         // Boolean for form modal
editingTemplate  // Template being edited or null
deleteConfirm    // Template ID for delete confirmation
```

**TemplateForm State:**
```javascript
formData        // Form field values
keywordInput    // Keyword input buffer
buttonInput     // Button input buffer
saving          // Boolean for save operation
error           // Error message string
```

## Error Handling

**Display Errors:**
- Network errors
- Validation errors
- API errors
- Form submission errors

**User Feedback:**
- Loading spinners during operations
- Success feedback on actions
- Error messages in red banners
- Disabled states for invalid forms

## Animation

Uses Framer Motion for smooth transitions:

**Animations:**
- Page enter/exit fade
- Card list items fade up
- Button hover scale (1.05x)
- Button tap scale (0.95x)
- Modal open/close scale + fade
- Delete confirmation modal

## Responsive Design

**Breakpoints:**
- Mobile: Single column layout
- Tablet: 2-column grid for filters
- Desktop: Full feature display

**Mobile Optimizations:**
- Touch-friendly button sizes
- Scrollable template list
- Simplified card layout
- Bottom sheet style modals

## Best Practices

### Template Naming
- Use snake_case: `main_menu`, `product_inquiry`
- Be descriptive: `welcome_new_customer`
- Avoid spaces and special characters

### Trigger Keywords
- Use lowercase
- Include common variations: `hi`, `hello`, `hey`
- Avoid overlapping keywords between templates
- Keep keywords simple and common

### Body Text
- Be clear and concise
- Use friendly, conversational tone
- Include call-to-action
- Keep under 1024 characters

### Buttons
- Maximum 3 buttons for button type
- Keep button text short (max 20 chars)
- Use action verbs: "Explore", "Talk", "Visit"
- Make options mutually exclusive

## Testing the UI

### Manual Testing Checklist

**List View:**
- [ ] Templates load correctly
- [ ] Search works
- [ ] Type filter works
- [ ] Status filter works
- [ ] Toggle status works
- [ ] Edit opens form
- [ ] Delete shows confirmation

**Create Form:**
- [ ] Form opens on "Create Template"
- [ ] All fields render
- [ ] Keywords can be added/removed
- [ ] Buttons can be added/removed (max 3)
- [ ] Validation prevents empty required fields
- [ ] Success creates template and closes form
- [ ] Errors display properly

**Edit Form:**
- [ ] Form loads with existing data
- [ ] Template name is disabled
- [ ] Changes save correctly
- [ ] Cancel discards changes

**Delete:**
- [ ] Confirmation modal appears
- [ ] Cancel keeps template
- [ ] Confirm removes template

## Troubleshooting

### Templates Not Loading
- Check API endpoint is accessible
- Verify backend is running
- Check browser console for errors
- Verify authentication token

### Form Not Submitting
- Check required fields are filled
- Verify template name is unique (create only)
- Check browser console for validation errors
- Verify API endpoint responds

### Buttons Not Adding
- Maximum 3 buttons allowed
- Button text must not be empty
- Check if button with same ID exists

### Keywords Not Adding
- Keyword must not be empty
- Keyword must be unique in list
- Check for whitespace issues

## Future Enhancements

Potential improvements:
- [ ] Drag-and-drop button reordering
- [ ] Template preview before save
- [ ] Duplicate template function
- [ ] Template export/import (JSON)
- [ ] Template version history
- [ ] Bulk operations (activate/deactivate multiple)
- [ ] Advanced menu builder with step flows
- [ ] Template analytics (usage stats)
- [ ] Template testing/preview mode

## Related Files

**Backend:**
- `backend/app/api/templates.py` - API endpoints
- `backend/app/models/conversation.py` - Data models
- `backend/app/services/message_handler.py` - Template usage

**Frontend:**
- `frontend/app/src/services/api.js` - API service
- `frontend/app/src/App.js` - Route definition
- `frontend/app/src/components/Layout.js` - Navigation

**Documentation:**
- `docs/TEMPLATE_MANAGEMENT_SYSTEM.md` - Full system docs
- `docs/COMPLETE_CONVERSATION_IMPLEMENTATION_GUIDE.md` - Usage guide

## Support

For issues or questions:
1. Check browser console for errors
2. Check backend logs for API errors
3. Verify database connectivity
4. Review this documentation
5. Check related code files

---

**Version:** 1.0.0  
**Last Updated:** January 2026  
**Author:** WhatsApp CRM Development Team
