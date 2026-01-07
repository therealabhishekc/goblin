# API URL Configuration Changes

## Summary
Updated all frontend applications to use the new backend API URL.

### Old URL
```
https://g5yeutappx.us-east-1.awsapprunner.com
https://2mm6fm7ffm.us-east-1.awsapprunner.com
```

### New URL
```
https://2hdfnnus3x.us-east-1.awsapprunner.com
```

## Changed Files

| Application | File | Status |
|------------|------|--------|
| Main App | `frontend/app/src/config.js` | ✅ Updated |
| Main App | `frontend/app/.env.example` | ✅ Updated |
| Template Sender | `frontend/templatesender/src/config.js` | ✅ Updated |
| Add User | `frontend/adduser/src/config.js` | ✅ Updated |
| Campaign | `frontend/campaign/src/config.js` | ✅ Updated |

## Quick Test

To test if the configuration is working:

```bash
# 1. Start any frontend app
cd frontend/app
npm start

# 2. Open browser console and check
console.log(config.apiUrl)
# Should show: https://2hdfnnus3x.us-east-1.awsapprunner.com

# 3. Test API connection
curl https://2hdfnnus3x.us-east-1.awsapprunner.com/health
```

## Rollback (if needed)

If you need to rollback to localhost for development:

```bash
# Create .env file in any frontend app
cd frontend/app
echo "REACT_APP_API_URL=http://localhost:8000" > .env
echo "REACT_APP_WS_URL=ws://localhost:8000" >> .env
```

## Environment-Specific Configuration

All apps support environment variable override:

```bash
# Development
export REACT_APP_API_URL=http://localhost:8000

# Staging
export REACT_APP_API_URL=https://staging.example.com

# Production (default)
# Uses https://2hdfnnus3x.us-east-1.awsapprunner.com
```
