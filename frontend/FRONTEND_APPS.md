# Frontend Applications Overview

## Applications in /frontend/

### 1. 👤 AddUser App (`/frontend/adduser/`)
**Purpose:** User Management System

**Features:**
- ➕ Add new users to database
- 🔄 Update existing user information
- 📊 Bulk import users via CSV
- ✅ Form validation
- 🔍 Search and find users

**Used For:**
- Onboarding new customers
- Updating customer information
- Bulk user imports
- Managing user database

**Key Files:**
- `AddUserForm.js` - Add single user
- `UpdateUserForm.js` - Update user details
- `BulkImportUsers.js` - CSV bulk import

---

### 2. 📤 TemplateSender App (`/frontend/templatesender/`)
**Purpose:** Bulk Template Message Sender

**Features:**
- 📋 Load all users from database
- 🔍 Search and filter users
- ✅ Multi-select users
- 📝 Configure templates with parameters
- 📤 Batch send template messages
- 📊 Real-time feedback

**Used For:**
- Marketing campaigns
- Promotional messages
- Order confirmations
- Welcome messages
- Bulk notifications

**Key Files:**
- `TemplateSender.js` - Main component
- `TemplateSender.css` - Styling
- `config.js` - API configuration

---

## Comparison

| Feature | AddUser | TemplateSender |
|---------|---------|----------------|
| **Primary Function** | User Management | Message Sending |
| **Users** | Add/Update | View/Select |
| **Data Input** | Forms/CSV | Template Config |
| **Bulk Operations** | CSV Import | Message Sending |
| **Output** | Database Records | WhatsApp Messages |
| **User Selection** | N/A | Multi-select |
| **Search** | By phone | By name/phone |
| **Validation** | Form fields | Template params |

---

## Workflow

### Typical User Journey

```
1. AddUser App
   └─> Add users to database
   └─> Import bulk users via CSV
   └─> Update user details

2. TemplateSender App  
   └─> View all users
   └─> Select recipients
   └─> Send template messages
   └─> Track delivery
```

---

## When to Use Each App

### Use AddUser When:
- ✅ Onboarding new customers
- ✅ Updating customer information
- ✅ Importing customer lists
- ✅ Managing user database
- ✅ Data entry tasks

### Use TemplateSender When:
- ✅ Running marketing campaigns
- ✅ Sending promotional offers
- ✅ Broadcasting announcements
- ✅ Order/shipping confirmations
- ✅ Bulk notifications

---

## Port Configuration

Both apps run on different ports for development:

- **AddUser:** `http://localhost:3000` (when started first)
- **TemplateSender:** `http://localhost:3001` (auto-assigned if 3000 is busy)

Or configure different ports explicitly:
```bash
# Terminal 1
cd frontend/adduser
PORT=3000 npm start

# Terminal 2
cd frontend/templatesender
PORT=3001 npm start
```

---

## Shared Configuration

Both apps share the same API backend:

**Development:**
```javascript
API_URL: 'http://localhost:8000'
```

**Production:**
```javascript
API_URL: 'https://2mm6fm7ffm.us-east-1.awsapprunner.com'
```

---

## Running Both Apps Simultaneously

```bash
# Terminal 1 - Start AddUser
cd /Users/abskchsk/Documents/govindjis/wa-app/frontend/adduser
npm start

# Terminal 2 - Start TemplateSender
cd /Users/abskchsk/Documents/govindjis/wa-app/frontend/templatesender
npm start
```

---

## Production Deployment

### Build Both Apps
```bash
# Build AddUser
cd frontend/adduser
npm run build

# Build TemplateSender
cd frontend/templatesender
npm run build
```

### Deploy Separately
Each app can be deployed to:
- Different S3 buckets
- Different subdomains
- Different CloudFront distributions

Example:
- `https://users.yourdomain.com` → AddUser
- `https://templates.yourdomain.com` → TemplateSender

---

## API Endpoints Used

### AddUser App
- `POST /api/users` - Create user
- `GET /api/users/{phone}` - Get user
- `PUT /api/users/{phone}` - Update user
- `POST /api/bulk-import-users` - Bulk import

### TemplateSender App
- `GET /api/users` - List all users
- `POST /messaging/template` - Send template

---

## Future Enhancements

### AddUser
- [ ] Export users to CSV
- [ ] Advanced user search filters
- [ ] User activity logs
- [ ] Bulk update operations

### TemplateSender
- [ ] Schedule campaigns
- [ ] Template library
- [ ] Analytics dashboard
- [ ] User segmentation
- [ ] Campaign history
- [ ] A/B testing

---

## Development Stack

Both apps use:
- **Framework:** React 18+
- **Build Tool:** Create React App
- **Styling:** CSS3
- **HTTP:** Fetch API
- **State:** React Hooks (useState, useEffect)

---

## Maintenance

### Updating Dependencies
```bash
cd frontend/adduser && npm update
cd frontend/templatesender && npm update
```

### Security Audits
```bash
cd frontend/adduser && npm audit fix
cd frontend/templatesender && npm audit fix
```

---

## Summary

You now have **two complementary frontend applications**:

1. **AddUser** - For managing your user database
2. **TemplateSender** - For communicating with those users

Together they provide a complete user management and messaging solution! 🎉
