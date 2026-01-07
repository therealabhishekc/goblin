# Template App Configuration

## Overview
A configuration file has been created for the Template Management frontend app, following the same pattern as other frontend apps in the project.

## Files Created/Updated

### 1. **src/config.js** ✅
Main configuration file that manages API endpoints:

```javascript
const config = {
  LOCAL_API_URL: 'http://localhost:8000',
  PRODUCTION_API_URL: 'https://2hdfnnus3x.us-east-1.awsapprunner.com',
  API_URL: process.env.REACT_APP_API_URL || 'https://2hdfnnus3x.us-east-1.awsapprunner.com'
};
```

### 2. **.env.example** ✅
Example environment file for documentation:

```
REACT_APP_API_URL=https://2hdfnnus3x.us-east-1.awsapprunner.com
```

### 3. **src/api/templateApi.js** ✅
Updated to use the config file instead of hardcoded URL:

```javascript
import config from '../config';

const api = axios.create({
  baseURL: config.API_URL,
  // ...
});
```

## How It Works

### Environment-based Configuration
The app uses the following priority for API URL:

1. **Environment Variable**: `REACT_APP_API_URL` from `.env` file
2. **Default**: `https://2hdfnnus3x.us-east-1.awsapprunner.com` (production)

### Switching Environments

#### For Production (Current)
No changes needed. The app is already configured for production.

#### For Local Development
Update `.env` file:
```
REACT_APP_API_URL=http://localhost:8000
```

Or set when starting:
```bash
REACT_APP_API_URL=http://localhost:8000 npm start
```

## Usage

### Start the App
```bash
cd /Users/abskchsk/Documents/govindjis/wa-app/frontend/template
npm start
```

The app will:
- Read configuration from `config.js`
- Use API URL from `.env` or default to production
- Log the API URL in browser console: `🔗 API Base URL: https://...`

### Build for Production
```bash
npm run build
```

## Benefits

✅ **Centralized Configuration**: Single source of truth for API settings  
✅ **Environment Flexibility**: Easy switching between local/production  
✅ **Consistent Pattern**: Matches other frontend apps (campaign, adduser, templatesender)  
✅ **Environment Variables**: Uses standard React env var pattern  
✅ **Documentation**: .env.example for setup guidance  

## File Structure
```
frontend/template/
├── .env                    # Environment variables (gitignored)
├── .env.example           # Example environment file ✅ NEW
├── src/
│   ├── config.js          # Configuration file ✅ NEW
│   ├── api/
│   │   └── templateApi.js # Updated to use config ✅ UPDATED
│   ├── components/
│   │   ├── TemplateList.js
│   │   └── TemplateForm.js
│   ├── App.js
│   └── index.js
└── package.json
```

## Troubleshooting

### If templates are not loading:
1. Check browser console for API URL log
2. Verify `.env` file has correct URL
3. Check network tab in DevTools for API calls
4. Verify backend API is running at configured URL

### To change API URL:
1. Edit `.env` file
2. Restart the development server
3. Check console for new API URL

## Next Steps

The configuration is now complete and ready to use. The app will automatically:
- Connect to production API by default
- Allow easy switching to local development
- Maintain consistency with other frontend apps
