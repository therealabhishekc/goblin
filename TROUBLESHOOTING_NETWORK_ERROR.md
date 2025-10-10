# Troubleshooting: "Failed to fetch" Network Error

## 🔴 Error Message
```
❌ Network Error: Failed to fetch
```

This error occurs when trying to update user information in the UpdateUserForm.

---

## 🔍 Root Causes & Solutions

### **1. CORS (Cross-Origin Resource Sharing) Issue** ⭐ Most Likely

#### **Symptoms:**
- Search works (GET request)
- Update fails (PUT request)
- Browser console shows CORS error

#### **Why it happens:**
Your frontend runs on a different origin (e.g., `http://localhost:3000`) than your backend (`https://hwwsxxpemc.us-east-1.awsapprunner.com`), and the browser blocks the PUT request due to CORS policy.

#### **Check in Browser:**
1. Open Developer Tools (F12)
2. Go to Console tab
3. Look for error like:
   ```
   Access to fetch at 'https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/...'
   from origin 'http://localhost:3000' has been blocked by CORS policy:
   Response to preflight request doesn't pass access control check
   ```

#### **Solution: Fix Backend CORS Configuration**

**File:** `backend/app/main.py`

Add or update CORS middleware:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ⭐ ADD THIS CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Local development
        "http://localhost:3001",      # Alternative port
        "http://127.0.0.1:3000",      # Alternative localhost
        "*"                            # Allow all (for testing only!)
    ],
    allow_credentials=True,
    allow_methods=["*"],              # Allow all methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],              # Allow all headers
)
```

**For Production (more secure):**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-production-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)
```

---

### **2. Backend Not Running**

#### **Check if backend is accessible:**
```bash
# Test backend health
curl https://hwwsxxpemc.us-east-1.awsapprunner.com/api/health/database

# Expected: HTTP 200 with JSON response
```

#### **Solution:**
Start your backend server:
```bash
cd backend
python -m uvicorn app.main:app --reload
```

---

### **3. URL Endpoint Issues**

#### **Current URLs in your code:**
- **Search (GET):** `https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/{phone}`
- **Update (PUT):** `https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/{phone}`

Both are using the same base URL, which is correct.

#### **Verify endpoint exists:**
```bash
# Check if PUT endpoint is available
curl -X PUT https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/test \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Test"}'
```

---

### **4. Request Payload Issues**

#### **Check what's being sent:**

Add console logging to see the request:

```javascript
// In UpdateUserForm.js, line 96
console.log('🔵 Updating user:', user.whatsapp_phone);
console.log('📦 Update data:', updateData);

try {
  const response = await fetch(
    `https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/${encodeURIComponent(user.whatsapp_phone)}`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updateData)
    }
  );
  
  console.log('📡 Response status:', response.status);
  // ... rest of code
```

---

### **5. Network/Firewall Blocking**

#### **Test direct API access:**

Open a new browser tab and paste:
```
https://hwwsxxpemc.us-east-1.awsapprunner.com/api/health/database
```

If this works, the endpoint is accessible.

#### **Test with cURL:**
```bash
curl -X PUT https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/+1234567890 \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Test User",
    "email": "test@example.com",
    "customer_tier": "regular",
    "tags": [],
    "notes": "",
    "subscription": "subscribed"
  }'
```

---

## 🔧 Quick Fixes (Try in Order)

### **Fix 1: Add Better Error Logging**

Update `UpdateUserForm.js` to show more details:

```javascript
} catch (error) {
  console.error('❌ Full error:', error);
  console.error('❌ Error name:', error.name);
  console.error('❌ Error message:', error.message);
  
  setAlert({ 
    type: 'error', 
    message: `❌ Network Error: ${error.message}. Check browser console for details.` 
  });
}
```

### **Fix 2: Add CORS Headers to Backend**

If you control the backend, ensure CORS is properly configured in `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For testing - allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **Fix 3: Use Proxy (Development Only)**

Add proxy to `frontend/adduser/package.json`:

```json
{
  "name": "adduser",
  "version": "0.1.0",
  "proxy": "https://hwwsxxpemc.us-east-1.awsapprunner.com",
  ...
}
```

Then change fetch URLs to relative:
```javascript
// Instead of full URL
const response = await fetch(`/api/users/${phone}`, {
  method: 'PUT',
  ...
});
```

### **Fix 4: Try with Axios Instead of Fetch**

Install axios:
```bash
cd frontend/adduser
npm install axios
```

Update code:
```javascript
import axios from 'axios';

// In handleUpdate
try {
  const response = await axios.put(
    `https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/${user.whatsapp_phone}`,
    updateData,
    {
      headers: {
        'Content-Type': 'application/json',
      }
    }
  );
  
  const result = response.data;
  // ... handle success
} catch (error) {
  if (error.response) {
    // Server responded with error
    console.error('Server error:', error.response.status, error.response.data);
    setAlert({ 
      type: 'error', 
      message: `❌ Update failed: ${error.response.data.detail}` 
    });
  } else if (error.request) {
    // Request made but no response
    console.error('No response:', error.request);
    setAlert({ 
      type: 'error', 
      message: '❌ Network Error: No response from server. Check CORS configuration.' 
    });
  } else {
    // Error setting up request
    console.error('Error:', error.message);
    setAlert({ 
      type: 'error', 
      message: `❌ Error: ${error.message}` 
    });
  }
}
```

---

## 🐛 Debugging Steps

### **Step 1: Check Browser Console**
1. Open DevTools (F12)
2. Go to Console tab
3. Try to update a user
4. Look for red error messages
5. Share the exact error message

### **Step 2: Check Network Tab**
1. Open DevTools (F12)
2. Go to Network tab
3. Try to update a user
4. Click on the failed request
5. Check:
   - Request URL
   - Request Method (should be PUT)
   - Request Headers
   - Response Headers
   - Response (if any)

### **Step 3: Test Backend Directly**

```bash
# Test GET (should work)
curl https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/+1234567890

# Test PUT (check if it works)
curl -X PUT https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/+1234567890 \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Test","email":"test@test.com","customer_tier":"regular","tags":[],"notes":"","subscription":"subscribed"}' \
  -v
```

Look for:
- HTTP status code
- Response headers (especially `Access-Control-Allow-*`)
- Response body

---

## 📋 Checklist

- [ ] Checked browser console for error messages
- [ ] Verified backend is running and accessible
- [ ] Confirmed CORS headers are present in backend
- [ ] Tested endpoint with cURL
- [ ] Added console.log to see request details
- [ ] Checked Network tab in DevTools
- [ ] Verified request payload is correct
- [ ] Tried with different browser
- [ ] Disabled browser extensions (ad blockers)
- [ ] Checked if firewall/antivirus is blocking

---

## 🎯 Most Likely Solution

**The issue is CORS.** Add this to your backend `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],              # Allow all for testing
    allow_credentials=True,
    allow_methods=["*"],              # Allow all HTTP methods
    allow_headers=["*"],              # Allow all headers
)
```

Restart your backend and try again.

---

## 📞 Need More Help?

Share the following information:
1. **Browser Console Error** (screenshot or copy exact error)
2. **Network Tab Details** (request/response headers)
3. **Backend CORS Configuration** (current setup)
4. **cURL Test Results** (does PUT work outside browser?)

This will help identify the exact issue!
