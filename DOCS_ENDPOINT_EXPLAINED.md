# API Documentation Endpoint (/docs) - Complete Explanation

## 🔍 Where Is It?

The `/docs` endpoint is **AUTOMATICALLY CREATED** by FastAPI. It's **NOT explicitly coded** anywhere - FastAPI generates it automatically based on your `FastAPI()` configuration.

---

## 📍 Location in Code

### **File:** `/backend/app/main.py` (Lines 145-153)

```python
# Create FastAPI application
settings = get_settings()
app = FastAPI(
    title=settings.app_name,              # "WhatsApp Business API"
    description="Enterprise WhatsApp Business API with PostgreSQL integration",
    version=settings.app_version,         # API version
    debug=settings.debug,                 # Debug mode
    lifespan=lifespan                     # Startup/shutdown
)
```

This **single declaration** automatically creates **THREE endpoints**:

1. **`/docs`** - Swagger UI (interactive API documentation)
2. **`/redoc`** - ReDoc (alternative documentation view)
3. **`/openapi.json`** - OpenAPI schema (JSON format)

---

## 🌐 How to Access

### **Local Development:**
```
http://localhost:8000/docs          ← Swagger UI (recommended)
http://localhost:8000/redoc         ← ReDoc (alternative view)
http://localhost:8000/openapi.json  ← Raw OpenAPI spec
```

### **Production (AWS App Runner):**
```
https://hwwsxxpemc.us-east-1.awsapprunner.com/docs
https://hwwsxxpemc.us-east-1.awsapprunner.com/redoc
```

---

## 📚 What You'll See in /docs

FastAPI automatically generates **interactive documentation** for ALL your endpoints:

### **Live Documentation Example:**

```
╔══════════════════════════════════════════════════════════════╗
║  WhatsApp Business API                                       ║
║  Enterprise WhatsApp Business API with PostgreSQL integration
║  Version: 1.0.0                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🏥 Health & System (9 endpoints)                           ║
║    GET  /health/startup                                     ║
║    GET  /health/database                                    ║
║    GET  /health/ready                                       ║
║    GET  /health/live                                        ║
║    ...                                                      ║
║                                                              ║
║  👥 User Management (14 endpoints) ✨ NEW!                  ║
║    POST   /api/users              Create user               ║
║    GET    /api/users              List users (paginated)    ║
║    GET    /api/users/{phone}      Get user profile          ║
║    PUT    /api/users/{phone}      Update user               ║
║    DELETE /api/users/{phone}      Delete user               ║
║    POST   /api/users/bulk-import  Bulk import CSV           ║
║    GET    /api/users/search/query Search users              ║
║    GET    /api/users/{phone}/conversation                   ║
║    GET    /api/users/{phone}/stats                          ║
║    POST   /api/users/{phone}/tags                           ║
║    DELETE /api/users/{phone}/tags                           ║
║    POST   /api/users/{phone}/subscribe                      ║
║    POST   /api/users/{phone}/unsubscribe                    ║
║                                                              ║
║  📥 Webhook (7 endpoints)                                   ║
║    GET   /webhook/                Verify webhook            ║
║    POST  /webhook/                Receive messages          ║
║    POST  /webhook/test            Test webhook              ║
║    ...                                                      ║
║                                                              ║
║  📤 Messaging (9 endpoints)                                 ║
║    POST  /messaging/send          Send message              ║
║    POST  /messaging/text          Send text                 ║
║    POST  /messaging/image         Send image                ║
║    POST  /messaging/document      Send document             ║
║    ...                                                      ║
║                                                              ║
║  📈 Analytics & Messages (4 endpoints)                      ║
║    GET   /api/analytics/daily     Daily analytics           ║
║    GET   /api/analytics/summary   Overall summary           ║
║    GET   /api/messages/recent     Recent messages           ║
║    GET   /api/health/database     Database health           ║
║                                                              ║
║  📢 Marketing (10 endpoints)                                ║
║    POST  /marketing/campaigns     Create campaign           ║
║    GET   /marketing/campaigns     List campaigns            ║
║    ...                                                      ║
║                                                              ║
║  📊 Monitoring (5 endpoints)                                ║
║    GET   /monitoring/dashboard    Dashboard                 ║
║    GET   /monitoring/queues       Queue metrics             ║
║    ...                                                      ║
║                                                              ║
║  🔧 Admin (5 endpoints)                                     ║
║    POST  /api/admin/archival/trigger                        ║
║    ...                                                      ║
║                                                              ║
║  🗄️ Archive (5 endpoints)                                   ║
║    GET   /api/v1/archive/messages                           ║
║    ...                                                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Total: 64 endpoints across 8 modules!
```

---

## 🎨 How FastAPI Generates Documentation

FastAPI automatically reads your code and generates docs from:

### **1. Router Definitions**

```python
# api/users.py
router = APIRouter(prefix="/api/users", tags=["User Management"])
                                                ↑
                                    Shows in docs as section title
```

### **2. Endpoint Decorators & Docstrings**

```python
@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_database_session)
):
    """
    Create a new user manually
    
    Used by: AddUserForm.js
    
    Example:
    ```json
    {
        "whatsapp_phone": "+1234567890",
        "display_name": "John Doe"
    }
    ```
    """
    # Docstring shows as description in docs
```

### **3. Type Hints**

```python
async def create_user(
    user_data: UserCreate,  # ← Shows expected input schema
    db: Session = Depends(get_database_session)
) -> UserResponse:          # ← Shows response schema
    return UserResponse(...)
```

### **4. Pydantic Models**

```python
class UserCreate(BaseModel):
    whatsapp_phone: str
    display_name: Optional[str]
    business_name: Optional[str]
    # FastAPI shows this as input schema in docs
```

---

## 🎯 Where Documentation Info Comes From

### **App Title & Description** (main.py, lines 147-150)

```python
app = FastAPI(
    title=settings.app_name,              # → "WhatsApp Business API"
    description="Enterprise WhatsApp...", # → Shows as subtitle
    version=settings.app_version,         # → "Version: 1.0.0"
    debug=settings.debug
)
```

### **Section Names** (from `tags` parameter)

```python
# api/users.py
router = APIRouter(prefix="/api/users", tags=["User Management"])
# Creates section: "User Management"

# api/messaging.py
router = APIRouter(prefix="/messaging", tags=["messaging"])
# Creates section: "messaging"
```

### **Endpoint Descriptions** (from docstrings)

```python
@router.post("")
async def create_user(...):
    """Create a new user manually"""  # ← Shows in docs
    pass
```

---

## 🎮 Interactive Features in /docs

The `/docs` page is **fully interactive**! For each endpoint:

### **1. View Request Schema**
- See all required and optional parameters
- See data types
- See example values

### **2. Try It Out**
- Click "Try it out" button
- Fill in parameters
- Click "Execute"
- See real response from your API!

### **Example Workflow:**

```
1. Navigate to /docs
2. Find "User Management" section
3. Click on "POST /api/users"
4. Click "Try it out"
5. Enter JSON:
   {
     "whatsapp_phone": "+1234567890",
     "display_name": "Test User"
   }
6. Click "Execute"
7. See response:
   {
     "id": "uuid",
     "whatsapp_phone": "+1234567890",
     "display_name": "Test User",
     "created_at": "2024-01-15T10:30:00Z"
   }
```

---

## 🔧 Customizing the Docs

### **Change URLs**

```python
app = FastAPI(
    title="Your Custom Title",
    description="Your description",
    version="2.0.0",
    docs_url="/api-docs",      # Change /docs URL
    redoc_url="/api-redoc",    # Change /redoc URL
    openapi_url="/api.json"    # Change /openapi.json URL
)
```

### **Disable Docs (for production)**

```python
app = FastAPI(
    title="WhatsApp Business API",
    docs_url=None,    # Disables /docs
    redoc_url=None    # Disables /redoc
)
```

### **Add Custom Metadata**

```python
app = FastAPI(
    title="WhatsApp Business API",
    description="""
    ## Features
    * User Management
    * WhatsApp Messaging
    * Analytics Dashboard
    
    ## Support
    Email: support@example.com
    """,
    version="1.0.0",
    terms_of_service="https://example.com/terms",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }
)
```

---

## 📊 Your Current API Documentation

When you visit `http://localhost:8000/docs`, you'll see:

### **Total Endpoints: 64**

| Module | Endpoints | Description |
|--------|-----------|-------------|
| **Health & System** | 9 | Health checks, readiness, liveness |
| **User Management** ✨ | 14 | CRUD, search, bulk import, tags |
| **Webhook** | 7 | WhatsApp webhook handling |
| **Messaging** | 9 | Send messages (text, image, document) |
| **Analytics & Messages** | 4 | Analytics, recent messages |
| **Marketing** | 10 | Campaign management |
| **Monitoring** | 5 | Queue monitoring, dashboard |
| **Admin** | 5 | Admin operations, archival |
| **Archive** | 5 | Historical data retrieval |

---

## 🚀 How to Use

### **1. Start Backend**

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### **2. Open Docs in Browser**

```
http://localhost:8000/docs
```

### **3. Explore Endpoints**

- Click any endpoint to expand
- See request/response schemas
- Read descriptions
- View examples

### **4. Test Endpoints**

- Click "Try it out"
- Enter parameters
- Click "Execute"
- View response

---

## 🔍 Alternative: ReDoc

ReDoc provides a different documentation view:

```
http://localhost:8000/redoc
```

**Differences:**
- `/docs` (Swagger UI) - Interactive, can test endpoints
- `/redoc` (ReDoc) - Read-only, cleaner design, better for printing

---

## 🎓 Summary

### **The `/docs` endpoint:**

✅ **Automatically created** by FastAPI (no code needed)  
✅ **Fully interactive** - test endpoints directly in browser  
✅ **Auto-generated** from your code (decorators, type hints, docstrings)  
✅ **Shows all 64 endpoints** across 8 modules  
✅ **Includes your new "User Management" section** with 14 endpoints  
✅ **Updated in real-time** as you add/modify endpoints  
✅ **Production-ready** - can be disabled for security  

### **Access:**
- **Development:** `http://localhost:8000/docs`
- **Production:** `https://your-domain.com/docs`

### **Configuration:** 
- Located in `/backend/app/main.py` (lines 145-153)
- Customizable URLs, metadata, and features

---

## 💡 Pro Tips

1. **Write good docstrings** - They appear in the docs!
2. **Use Pydantic models** - FastAPI generates schemas automatically
3. **Add examples** - Help users understand your API
4. **Use tags wisely** - Organize endpoints into logical sections
5. **Test in /docs** - Quick way to verify endpoints work
6. **Share with team** - Everyone can see API without reading code

---

## 🎉 Try It Now!

```bash
# Start backend
cd backend
python -m uvicorn app.main:app --reload

# Open in browser
open http://localhost:8000/docs

# Look for "User Management" section ✨
# Try creating a user interactively!
```

Your API documentation is now professional, interactive, and automatically maintained! 🚀
