# Deployment Guide - Address Fields Update

## Overview
This guide covers deploying the updated frontend with address fields replacing business_name.

## Changes Summary
- ❌ Removed: `business_name` field
- ✅ Added: `address1`, `address2`, `city`, `state`, `zipcode` fields

## Prerequisites

### Backend Requirements (Must be deployed first)
- [ ] Database schema updated with new address columns
- [ ] API endpoints updated to accept/return address fields
- [ ] Backend deployed and accessible at: `https://hwwsxxpemc.us-east-1.awsapprunner.com`

### Frontend Requirements
- [x] Build completed successfully (✅ Done)
- [x] No breaking errors in build
- [x] Build artifacts ready in `frontend/adduser/build/`

## Deployment Steps

### Option 1: AWS S3 + CloudFront

If you're using S3 for static hosting:

```bash
cd /Users/abskchsk/Documents/govindjis/wa-app/frontend/adduser

# 1. Build the app (already done)
npm run build

# 2. Sync to S3 bucket (replace with your bucket name)
aws s3 sync build/ s3://your-bucket-name/ --delete

# 3. Invalidate CloudFront cache (replace with your distribution ID)
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Option 2: Manual Upload

1. Build is already created at: `/Users/abskchsk/Documents/govindjis/wa-app/frontend/adduser/build/`
2. Upload entire `build/` directory contents to your web server
3. Ensure server is configured to serve `index.html` for all routes (SPA routing)

### Option 3: Netlify/Vercel

```bash
cd /Users/abskchsk/Documents/govindjis/wa-app/frontend/adduser

# Netlify
netlify deploy --prod --dir=build

# Vercel
vercel --prod
```

## Post-Deployment Testing

### Critical Tests (Must Pass)

1. **Add User Form**
```
Test Case: Add user with full address
- Navigate to Add User page
- Fill in phone: +1234567890
- Fill in display name: Test User
- Fill in address1: 123 Main St
- Fill in address2: Apt 4B
- Fill in city: New York
- Fill in state: NY
- Fill in zipcode: 10001
- Fill in email: test@example.com
- Submit form
Expected: ✅ Success message, user created
```

2. **Update User Form**
```
Test Case: Update existing user address
- Navigate to Update User page
- Search phone: +1234567890
- Verify address fields display (may show N/A for old users)
- Update address fields
- Submit form
Expected: ✅ Success message, address updated
```

3. **Bulk Import**
```
Test Case: Import users with new CSV format
- Navigate to Bulk Import page
- Click "Download CSV Template"
- Verify template has new columns:
  whatsapp_phone,display_name,address1,address2,city,state,zipcode,email,customer_tier,tags,notes
- Upload sample CSV
Expected: ✅ Users imported successfully
```

### Edge Case Tests (Should Handle Gracefully)

4. **Existing Users Without Addresses**
```
Test Case: View old user data
- Search for user created before this update
- Check address fields
Expected: Shows "N/A" for null address fields
```

5. **Partial Address Data**
```
Test Case: Add user with only address1
- Add user with only address1 filled
- Leave address2, city, state, zipcode empty
Expected: ✅ User created successfully
```

## Rollback Plan

If issues are discovered after deployment:

### Quick Rollback (Emergency)
```bash
# If using S3/CloudFront, revert to previous version
aws s3 sync s3://your-bucket-name-backup/ s3://your-bucket-name/ --delete
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Issues and Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| API returns business_name | Frontend can't find business_name field | Backend not deployed yet - deploy backend first |
| Address fields not saving | API error 400/422 | Check backend schema and API endpoint updates |
| Old users show errors | Error loading user details | Add null checks in frontend (already done) |
| CSV import fails | Wrong format error | Users need new template - update documentation |

## Verification Checklist

After deployment, verify:

- [ ] Home page loads
- [ ] Add User form displays new address fields
- [ ] Add User form submits successfully
- [ ] Update User search works
- [ ] Update User displays address fields
- [ ] Update User saves address changes
- [ ] Bulk Import downloads new CSV template
- [ ] Bulk Import accepts new CSV format
- [ ] Existing users (without addresses) display correctly
- [ ] No console errors in browser
- [ ] API calls use correct endpoints
- [ ] CORS issues resolved (if applicable)

## Monitoring

### Things to Watch

1. **API Error Rate**: Check for increased 400/422 errors
2. **Frontend Errors**: Monitor browser console logs
3. **User Reports**: Watch for user complaints about missing fields
4. **CSV Import Success Rate**: Track bulk import success/failure ratio

### Expected Metrics After Deployment

- Build Size: ~51.25 KB (gzipped)
- Load Time: <2 seconds
- API Response Time: <500ms
- Error Rate: <1%

## Communication

### User Notification (Sample)

```
Subject: New Address Fields Available

We've updated the user management system with detailed address fields.

What's New:
- Address Line 1 & 2
- City, State, Zip Code
- Removed: Business Name field

What You Need to Do:
1. Update existing user records with address information
2. Use new CSV template for bulk imports
3. Download updated template from Bulk Import page

Questions? Contact: [your-email]
```

### Documentation Updates Needed

- [ ] Update user manual with new field descriptions
- [ ] Update CSV import guide with new template
- [ ] Update API documentation (if public)
- [ ] Update training materials

## CloudFormation Stack Redeployment

If redeploying entire stack:

### Before Destroying Stack
```bash
# Backup database (if needed)
# Document current environment variables
# Save any custom configurations
```

### Deploy New Stack
```bash
cd /Users/abskchsk/Documents/govindjis/wa-app

# Ensure all backend changes are committed
git status

# Deploy backend with new schema
# (Follow your existing CloudFormation deployment process)

# After backend is deployed, deploy frontend
cd frontend/adduser
npm run build
# Upload to S3 or your hosting service
```

### Post-Stack-Deployment
- [ ] Verify database schema includes new columns
- [ ] Test API endpoints return new fields
- [ ] Deploy frontend build
- [ ] Run full test suite
- [ ] Verify end-to-end functionality

## Troubleshooting

### Frontend won't build
```bash
cd frontend/adduser
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Changes not showing after deployment
- Clear browser cache (Cmd+Shift+R or Ctrl+Shift+R)
- Check CloudFront invalidation completed
- Verify correct files uploaded to S3
- Check browser console for cached resources

### API errors after deployment
- Verify backend is deployed first
- Check API endpoint URL is correct
- Test API directly with curl/Postman
- Check CORS headers if cross-origin

## Success Criteria

Deployment is successful when:
- ✅ All frontend forms display new address fields
- ✅ Users can add/update address information
- ✅ CSV template downloads with new format
- ✅ Bulk import works with new CSV format
- ✅ Existing users without addresses display correctly
- ✅ No JavaScript errors in browser console
- ✅ API calls succeed (200/201 responses)
- ✅ User experience is smooth and intuitive

## Contact & Support

For issues or questions:
- Check logs in browser console (F12)
- Review API responses in Network tab
- Check backend logs for API errors
- Review this deployment guide

---

**Build Information**
- Build Date: 2024-01-XX
- Frontend Version: 0.1.0
- React Version: 18.x
- Build Tool: react-scripts
- Build Size: 51.25 KB (gzipped)
- Build Location: `/Users/abskchsk/Documents/govindjis/wa-app/frontend/adduser/build/`
