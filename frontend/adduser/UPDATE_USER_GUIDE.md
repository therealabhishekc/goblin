# Update User Component Guide

## 🎯 Overview

The **UpdateUserForm** component allows you to search for existing users and update their information through a beautiful, intuitive interface.

## ✨ Features

### Search Functionality
- 🔍 Search users by phone number
- ✅ Real-time validation
- 📱 Phone number format support (+1234567890)
- 🎯 Instant user lookup

### User Information Display
- 📋 Shows complete user profile
- 📊 Displays current tier (Regular/Premium/VIP)
- ✅ Active/Inactive status indicator
- 📈 Total messages count
- 📅 Account creation date

### Update Capabilities
- ✏️ Update all user fields
- 🏷️ Tag management (add/remove)
- 🎯 Customer tier change
- ⚡ Soft delete (deactivate users)
- 💾 Real-time updates
- ✅ Success/Error feedback

## 🚀 How to Use

### Step 1: Search for User
1. Enter phone number with country code (e.g., +1234567890)
2. Click "🔍 Search" button
3. User information will be displayed if found

### Step 2: View Current Information
After search, you'll see:
- Current phone number
- Display name
- Business name
- Email
- Customer tier (badge)
- Active status (badge)
- Total messages
- Creation date

### Step 3: Modify Information
Update any of these fields:
- **Display Name** - User's name
- **Business Name** - Their business
- **Email** - Contact email
- **Customer Tier** - Regular/Premium/VIP
- **Tags** - Add tags by typing and pressing Enter
- **Notes** - Additional information
- **Active Status** - Check/uncheck to activate/deactivate

### Step 4: Save Changes
1. Click "✅ Update User" button
2. Wait for confirmation
3. Success message will appear
4. User info refreshes with new data

### Step 5: Search Another User
Click "🔄 Reset" to clear the form and search for another user

## 📋 Field Details

### Updatable Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Display Name | Text | No | User's display name |
| Business Name | Text | No | Business name |
| Email | Email | No | Email address |
| Customer Tier | Select | Yes | Regular/Premium/VIP |
| Tags | Array | No | Multiple tags |
| Notes | Text Area | No | Additional notes |
| Active Status | Checkbox | Yes | User active/inactive |

### Read-Only Information

- **Phone Number** - Cannot be changed (unique identifier)
- **Total Messages** - System calculated
- **Created At** - Historical timestamp
- **ID** - Primary key

## 🎨 UI Elements

### Color Coding

**Customer Tiers:**
- 🔵 **Regular** - Blue badge
- 🟠 **Premium** - Orange badge
- 🟣 **VIP** - Purple badge

**Status:**
- ✅ **Active** - Green badge
- ❌ **Inactive** - Red badge

### Buttons

- **🔍 Search** - Green button to find user
- **✅ Update User** - Purple gradient to save changes
- **🔄 Reset** - Gray button to clear form

## 💡 Common Use Cases

### 1. Upgrade Customer Tier
```
Search: +1234567890
Change: Customer Tier → VIP
Add Tag: "high-value"
Update: Click "Update User"
```

### 2. Deactivate User (Soft Delete)
```
Search: +1234567890
Uncheck: "Active User" checkbox
Update: Click "Update User"
```

### 3. Update Contact Information
```
Search: +1234567890
Change: Email → newemail@example.com
Change: Business Name → New Business LLC
Update: Click "Update User"
```

### 4. Add Tags for Segmentation
```
Search: +1234567890
Add Tag: "vip" (press Enter)
Add Tag: "premium" (press Enter)
Add Tag: "high-spender" (press Enter)
Update: Click "Update User"
```

### 5. Update Notes
```
Search: +1234567890
Add Notes: "Customer requested premium features"
Update: Click "Update User"
```

## 🔧 Technical Details

### API Calls

**Search User:**
```
GET http://localhost:8000/api/users/{phone_number}
```

**Update User:**
```
PUT http://localhost:8000/api/users/{phone_number}
Content-Type: application/json

{
  "display_name": "John Updated",
  "business_name": "New Business",
  "email": "john@example.com",
  "customer_tier": "vip",
  "tags": ["vip", "premium"],
  "notes": "Updated customer",
  "is_active": true
}
```

### Component Files

- **UpdateUserForm.js** - Main component logic
- **UpdateUserForm.css** - Styling and animations

### State Management

```javascript
const [searchPhone, setSearchPhone] = useState('');      // Search input
const [user, setUser] = useState(null);                  // Found user
const [formData, setFormData] = useState({...});         // Form fields
const [loading, setLoading] = useState(false);           // Loading state
const [alert, setAlert] = useState(null);                // Alert messages
```

## 🎯 Navigation

The app now has **two tabs**:

1. **➕ Add User** - Create new users
2. **🔄 Update User** - Search and update existing users

Switch between tabs by clicking on them at the top of the page.

## ⚠️ Important Notes

### Phone Number
- Must include country code
- Cannot be updated (it's the unique identifier)
- Format: +1234567890

### Soft Delete
- Unchecking "Active User" marks user as inactive
- User data is preserved
- Can be reactivated by checking the box again
- Recommended over hard delete

### Tags
- Press **Enter** to add a tag
- Click **×** to remove a tag
- Tags help with customer segmentation
- Useful for filtering and targeting

### Validation
- Email must be valid format
- Phone number must exist in database
- Fields are trimmed automatically

## 🐛 Troubleshooting

### "User not found"
- Check phone number format (+1234567890)
- Verify user exists in database
- Ensure backend is running

### "Network Error"
- Backend must be running on port 8000
- Check CORS configuration
- Verify API endpoint is accessible

### Update Not Working
- Check browser console for errors
- Verify all required fields are filled
- Ensure backend is responding

### Tags Not Adding
- Press **Enter** after typing tag
- Don't click outside the input
- Tag must not already exist in list

## 📱 Responsive Design

- ✅ Works on desktop (900px+ width)
- ✅ Adapts to tablets (768px-899px)
- ✅ Mobile friendly (under 768px)
- ✅ Touch-friendly interface

## 🔐 Security

- Uses existing authentication (if configured)
- CORS enabled for localhost:3000
- Input sanitization
- No sensitive data exposed

## 📊 Example Workflow

```
1. User opens app
2. Clicks "🔄 Update User" tab
3. Enters phone: +1234567890
4. Clicks "🔍 Search"
5. Reviews current information
6. Updates customer_tier to "vip"
7. Adds tag "premium-customer"
8. Updates notes
9. Clicks "✅ Update User"
10. Sees success message
11. User information refreshes
12. Can make more changes or search another user
```

## 🎓 Best Practices

1. **Always search first** - Don't assume phone number
2. **Use soft delete** - Uncheck active instead of deleting
3. **Add meaningful tags** - Help with customer segmentation
4. **Update notes** - Keep track of important information
5. **Verify changes** - Check updated info after saving
6. **Use tier wisely** - Regular → Premium → VIP progression

## 🆘 Need Help?

If you encounter issues:
1. Check backend logs
2. Check browser console (F12)
3. Verify API is running: `curl http://localhost:8000/health`
4. Check user exists: `curl http://localhost:8000/api/users/{phone}`

## ✅ Summary

The Update User component provides a complete interface to:
- 🔍 Search users by phone
- 👀 View current information
- ✏️ Update all fields
- 🏷️ Manage tags
- ⚡ Soft delete (deactivate)
- ✅ See real-time updates

**Happy updating! 🎉**
