# Template Management System - Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                   (React Frontend - Port 3000)                   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ HTTP Requests
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND COMPONENTS                         │
│  ┌──────────────────────┐  ┌──────────────────────────────┐   │
│  │ TemplateManagement   │  │     TemplateForm             │   │
│  │                      │  │                              │   │
│  │ • List templates     │  │ • Create new template        │   │
│  │ • Search & filter    │  │ • Edit existing template     │   │
│  │ • Toggle status      │  │ • Validate input             │   │
│  │ • Delete template    │  │ • Submit to API              │   │
│  └──────────────────────┘  └──────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API Service (services/api.js)               │  │
│  │                                                          │  │
│  │  getTemplates()      createTemplate()     updateTemplate() │
│  │  getTemplateById()   deleteTemplate()     toggleStatus()   │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ REST API Calls
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API SERVER                            │
│                   (FastAPI - Port 8000)                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           API Router (api/templates.py)                  │  │
│  │                                                          │  │
│  │  GET    /templates              List all templates      │  │
│  │  GET    /templates/{id}         Get by ID              │  │
│  │  GET    /templates/name/{name}  Get by name            │  │
│  │  POST   /templates              Create template         │  │
│  │  PUT    /templates/{id}         Update template         │  │
│  │  DELETE /templates/{id}         Delete template         │  │
│  │  POST   /templates/{id}/toggle  Toggle status          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                 │                                │
│                                 │ Database Operations            │
│                                 ▼                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │      Data Models (models/conversation.py)                │  │
│  │                                                          │  │
│  │  • WorkflowTemplateDB      (SQLAlchemy Model)          │  │
│  │  • WorkflowTemplateCreate  (Pydantic Request)          │  │
│  │  • WorkflowTemplateUpdate  (Pydantic Request)          │  │
│  │  • WorkflowTemplateResponse (Pydantic Response)        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ SQL Queries
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATABASE LAYER                             │
│                     (PostgreSQL RDS)                             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           workflow_templates TABLE                       │  │
│  │                                                          │  │
│  │  id               UUID (PK)                             │  │
│  │  template_name    VARCHAR(100) UNIQUE                   │  │
│  │  template_type    VARCHAR(20)                           │  │
│  │  trigger_keywords TEXT[]                                │  │
│  │  menu_structure   JSONB                                 │  │
│  │  is_active        BOOLEAN                               │  │
│  │  created_at       TIMESTAMP                             │  │
│  │  updated_at       TIMESTAMP                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ Used By
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CONVERSATION HANDLER                           │
│            (services/message_handler.py)                         │
│                                                                  │
│  1. User sends message with trigger keyword                     │
│  2. Handler queries active templates                            │
│  3. Matches keyword to template                                 │
│  4. Creates conversation state                                  │
│  5. Sends interactive menu to user                              │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Creating a Template

```
User (Browser)
    │
    ├─► Click "Create Template"
    │
    ├─► Fill Form
    │   • Template Name
    │   • Template Type
    │   • Keywords
    │   • Menu Structure
    │
    ├─► Click "Create"
    │
    ▼
Frontend (React)
    │
    ├─► Validate Form
    │
    ├─► apiService.createTemplate(data)
    │
    ▼
Backend API (FastAPI)
    │
    ├─► POST /templates
    │
    ├─► Validate with Pydantic
    │
    ├─► Check uniqueness
    │
    ├─► Create WorkflowTemplateDB object
    │
    ├─► db.add(template)
    ├─► db.commit()
    │
    ▼
Database (PostgreSQL)
    │
    ├─► INSERT INTO workflow_templates
    │
    ├─► Return created record
    │
    ▼
Response Flow
    │
    ├─► Database → Backend (template object)
    ├─► Backend → Frontend (JSON response)
    ├─► Frontend → User (success message, refresh list)
    │
    ✓ Template Created!
```

### Using a Template in Conversation

```
WhatsApp User
    │
    ├─► Sends "hi"
    │
    ▼
WhatsApp API
    │
    ├─► Webhook to Backend
    │
    ▼
Message Handler
    │
    ├─► Query: SELECT * FROM workflow_templates
    │           WHERE 'hi' = ANY(trigger_keywords)
    │           AND is_active = true
    │
    ├─► Template found: "main_menu"
    │
    ├─► Read menu_structure JSON
    │
    ├─► Create conversation_state record
    │
    ├─► Build interactive message
    │   {
    │     "type": "interactive",
    │     "interactive": {
    │       "type": "button",
    │       "body": { "text": "Welcome..." },
    │       "action": {
    │         "buttons": [...]
    │       }
    │     }
    │   }
    │
    ▼
WhatsApp API
    │
    ├─► Send interactive message
    │
    ▼
WhatsApp User
    │
    ✓ Receives menu with buttons!
```

## Component Relationships

```
┌────────────────────────────────────────────────────────┐
│                    App.js                              │
│  (Main application with routing)                       │
└────────────────────────────────────────────────────────┘
                        │
                        ├─► Route: /templates
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│                   Layout.js                            │
│  • Navigation menu                                     │
│  • "Templates" menu item                               │
└────────────────────────────────────────────────────────┘
                        │
                        │ Wraps
                        ▼
┌────────────────────────────────────────────────────────┐
│            TemplateManagement.js                       │
│  ┌──────────────────────────────────────────────┐     │
│  │ State:                                       │     │
│  │  • templates[]                               │     │
│  │  • loading, error                            │     │
│  │  • searchTerm, filters                       │     │
│  │  • showForm, editingTemplate                 │     │
│  └──────────────────────────────────────────────┘     │
│                        │                               │
│  ┌──────────────────────────────────────────────┐     │
│  │ UI Elements:                                 │     │
│  │  • Search bar                                │     │
│  │  • Filter dropdowns                          │     │
│  │  • Template cards grid                       │     │
│  │  • Action buttons                            │     │
│  └──────────────────────────────────────────────┘     │
│                        │                               │
│                        │ Opens on Create/Edit          │
│                        ▼                               │
│  ┌────────────────────────────────────────────────┐   │
│  │          TemplateForm.js (Modal)               │   │
│  │  ┌──────────────────────────────────────┐     │   │
│  │  │ Form Fields:                         │     │   │
│  │  │  • Template Name                     │     │   │
│  │  │  • Template Type                     │     │   │
│  │  │  • Keywords (array)                  │     │   │
│  │  │  • Menu Structure                    │     │   │
│  │  │    - Body                            │     │   │
│  │  │    - Footer                          │     │   │
│  │  │    - Buttons                         │     │   │
│  │  └──────────────────────────────────────┘     │   │
│  └────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

## API Request/Response Flow

### Example: List Templates

```
Request:
┌─────────────────────────────────────────┐
│ GET /templates?is_active=true          │
│                                         │
│ Headers:                                │
│   Content-Type: application/json       │
└─────────────────────────────────────────┘
                  │
                  ▼
        Backend Processing
                  │
                  ▼
Response:
┌─────────────────────────────────────────┐
│ Status: 200 OK                          │
│                                         │
│ Body: [                                 │
│   {                                     │
│     "id": "uuid-here",                  │
│     "template_name": "main_menu",       │
│     "template_type": "button",          │
│     "trigger_keywords": ["hi","hello"], │
│     "menu_structure": {...},            │
│     "is_active": true,                  │
│     "created_at": "2026-01-07...",      │
│     "updated_at": "2026-01-07..."       │
│   }                                     │
│ ]                                       │
└─────────────────────────────────────────┘
```

### Example: Create Template

```
Request:
┌─────────────────────────────────────────┐
│ POST /templates                         │
│                                         │
│ Body: {                                 │
│   "template_name": "new_menu",          │
│   "template_type": "button",            │
│   "trigger_keywords": ["start"],        │
│   "menu_structure": {                   │
│     "body": "Welcome!",                 │
│     "steps": {                          │
│       "initial": {                      │
│         "type": "button",               │
│         "buttons": [...],               │
│         "next_steps": {}                │
│       }                                 │
│     }                                   │
│   },                                    │
│   "is_active": true                     │
│ }                                       │
└─────────────────────────────────────────┘
                  │
                  ▼
        Validation & Storage
                  │
                  ▼
Response:
┌─────────────────────────────────────────┐
│ Status: 201 Created                     │
│                                         │
│ Body: {                                 │
│   "id": "new-uuid",                     │
│   "template_name": "new_menu",          │
│   ... (full template object)            │
│ }                                       │
└─────────────────────────────────────────┘
```

## State Management Flow

```
User Action → Component State → API Call → Backend → Database
                    ↑                                      │
                    │                                      │
                    └──────── Response Flow ───────────────┘
```

### State in TemplateManagement.js

```javascript
State Updates:

Initial Load:
  loading = true → API call → loading = false, templates = data

Search:
  searchTerm changed → re-render with filtered templates

Filter:
  filterType/filterActive changed → API call with params

Create:
  showForm = true → Form shown
  Form submitted → API call → Refresh list → showForm = false

Edit:
  editingTemplate = template → showForm = true → Form shown
  Form submitted → API call → Refresh list → Close form

Delete:
  deleteConfirm = id → Confirmation shown
  Confirmed → API call → Refresh list → deleteConfirm = null

Toggle:
  API call → Refresh list
```

## File Structure

```
wa-app/
├── backend/
│   └── app/
│       ├── api/
│       │   └── templates.py          ← API Endpoints
│       ├── models/
│       │   └── conversation.py       ← Data Models
│       ├── services/
│       │   └── message_handler.py    ← Uses Templates
│       └── main.py                   ← Registers Router
│
├── frontend/
│   └── app/
│       └── src/
│           ├── pages/
│           │   └── templates/
│           │       ├── TemplateManagement.js  ← Main UI
│           │       ├── TemplateForm.js        ← Form Modal
│           │       ├── index.js               ← Exports
│           │       └── README.md              ← UI Docs
│           ├── services/
│           │   └── api.js            ← API Service
│           ├── components/
│           │   └── Layout.js         ← Navigation
│           └── App.js                ← Routing
│
└── docs/
    ├── TEMPLATE_MANAGEMENT_SYSTEM.md        ← System Overview
    ├── TEMPLATE_SYSTEM_ARCHITECTURE.md      ← This File
    └── COMPLETE_CONVERSATION_IMPLEMENTATION_GUIDE.md
```

## Technology Stack

```
┌─────────────────────────────────┐
│         Frontend Stack          │
├─────────────────────────────────┤
│ • React 18.2                    │
│ • React Router 6.20             │
│ • Axios 1.6                     │
│ • Framer Motion 10.16           │
│ • React Icons 4.12              │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│         Backend Stack           │
├─────────────────────────────────┤
│ • FastAPI                       │
│ • Pydantic (validation)         │
│ • SQLAlchemy (ORM)              │
│ • PostgreSQL (database)         │
│ • Python 3.8+                   │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│      Database Schema            │
├─────────────────────────────────┤
│ • workflow_templates            │
│ • conversation_state            │
│ • whatsapp_messages             │
└─────────────────────────────────┘
```

## Security Architecture

```
┌────────────────────────────────────────────────┐
│              Frontend Security                 │
├────────────────────────────────────────────────┤
│ • React auto-escapes XSS                      │
│ • Form validation before submit               │
│ • HTTPS in production                         │
│ • CORS configured                             │
└────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────┐
│              Backend Security                  │
├────────────────────────────────────────────────┤
│ • Pydantic input validation                   │
│ • SQLAlchemy ORM (SQL injection protection)   │
│ • Type checking                               │
│ • Error handling (no data exposure)           │
└────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────┐
│             Database Security                  │
├────────────────────────────────────────────────┤
│ • SSL/TLS connection                          │
│ • Parameterized queries only                  │
│ • Role-based access control                   │
│ • Encrypted at rest                           │
└────────────────────────────────────────────────┘
```

## Integration Points

```
Template System
      │
      ├─► Message Handler (uses templates)
      │
      ├─► Conversation State (tracks progress)
      │
      ├─► WhatsApp API (sends menus)
      │
      └─► Auto-reply Rules (fallback)
```

---

This architecture provides a complete, scalable, and maintainable template management system that integrates seamlessly with your WhatsApp automation workflow.
