# Testing Checklist - Address Fields Update

## Pre-Deployment Testing

### ✅ Build & Compilation
- [x] Frontend builds without errors
- [x] No breaking changes in dependencies
- [x] Build size is reasonable (~51KB)
- [x] All business_name references removed

## Post-Deployment Testing

### 🧪 Test Scenarios

#### 1. Add User Form - Full Address
**Steps:**
1. Navigate to "Add User" page
2. Fill in:
   - Phone: +15551234567
   - Display Name: Test User Full
   - Address Line 1: 123 Main Street
   - Address Line 2: Apt 4B
   - City: New York
   - State: NY
   - Zip Code: 10001
   - Email: test@example.com
   - Customer Tier: Premium
3. Click "Add User"

**Expected Result:**
- ✅ Success message appears
- ✅ Form resets after 2 seconds
- ✅ User created in database with all address fields

**Status:** [ ] Pass [ ] Fail

---

#### 2. Add User Form - Minimal Data
**Steps:**
1. Navigate to "Add User" page
2. Fill in ONLY:
   - Phone: +15557654321
   - Display Name: Minimal Test
3. Leave all address fields empty
4. Click "Add User"

**Expected Result:**
- ✅ Success message appears
- ✅ User created with NULL address fields
- ✅ No validation errors

**Status:** [ ] Pass [ ] Fail

---

#### 3. Add User Form - Partial Address
**Steps:**
1. Navigate to "Add User" page
2. Fill in:
   - Phone: +15559876543
   - Display Name: Partial Address
   - Address Line 1: 456 Oak Avenue
   - City: Boston
   - Zip Code: 02101
3. Leave Address Line 2 and State empty
4. Click "Add User"

**Expected Result:**
- ✅ Success message appears
- ✅ User created with partial address data
- ✅ Empty fields stored as NULL

**Status:** [ ] Pass [ ] Fail

---

#### 4. Update User - View Existing User
**Steps:**
1. Navigate to "Update User" page
2. Search for: +15551234567 (created in test #1)
3. Review displayed information

**Expected Result:**
- ✅ User found successfully
- ✅ All address fields display correctly:
  - Address 1: 123 Main Street
  - Address 2: Apt 4B
  - City: New York
  - State: NY
  - Zip Code: 10001

**Status:** [ ] Pass [ ] Fail

---

#### 5. Update User - View Old User (No Address)
**Steps:**
1. Navigate to "Update User" page
2. Search for a user created BEFORE this update
3. Review displayed information

**Expected Result:**
- ✅ User found successfully
- ✅ Address fields show "N/A"
- ✅ No errors or broken UI
- ✅ Can still view other user information

**Status:** [ ] Pass [ ] Fail

---

#### 6. Update User - Add Address to Old User
**Steps:**
1. Navigate to "Update User" page
2. Search for user from test #5
3. Fill in address fields:
   - Address Line 1: 789 Pine Road
   - City: Chicago
   - State: IL
   - Zip Code: 60601
4. Click "Update User"

**Expected Result:**
- ✅ Success message appears
- ✅ Address information updated
- ✅ Updated values display immediately
- ✅ No "N/A" shown for filled fields

**Status:** [ ] Pass [ ] Fail

---

#### 7. Update User - Modify Existing Address
**Steps:**
1. Navigate to "Update User" page
2. Search for: +15551234567
3. Change:
   - City: New York → Brooklyn
   - State: NY → NY (keep same)
   - Address Line 2: Apt 4B → Suite 100
4. Click "Update User"

**Expected Result:**
- ✅ Success message appears
- ✅ Only changed fields updated
- ✅ Other fields remain unchanged
- ✅ Updated data displays correctly

**Status:** [ ] Pass [ ] Fail

---

#### 8. Update User - Clear Address Data
**Steps:**
1. Navigate to "Update User" page
2. Search for user with address data
3. Clear all address fields (delete text)
4. Click "Update User"

**Expected Result:**
- ✅ Success message appears
- ✅ Address fields set to NULL
- ✅ Display shows "N/A" for cleared fields
- ✅ Other data (name, email, etc.) unchanged

**Status:** [ ] Pass [ ] Fail

---

#### 9. Bulk Import - Download Template
**Steps:**
1. Navigate to "Bulk Import Users" page
2. Click "Download CSV Template"
3. Open downloaded file

**Expected Result:**
- ✅ File downloads successfully
- ✅ File named: bulk_import_template.csv
- ✅ Header row contains:
  - whatsapp_phone,display_name,address1,address2,city,state,zipcode,email,customer_tier,tags,notes
- ✅ Sample data includes address fields
- ✅ No business_name column

**Status:** [ ] Pass [ ] Fail

---

#### 10. Bulk Import - Full CSV
**Steps:**
1. Create CSV file with 3 users, all with full addresses:
```csv
whatsapp_phone,display_name,address1,address2,city,state,zipcode,email,customer_tier,tags,notes
+15551111111,Bulk User 1,111 First St,Unit A,Dallas,TX,75201,bulk1@example.com,regular,"test",Bulk import test
+15552222222,Bulk User 2,222 Second Ave,Floor 2,Austin,TX,78701,bulk2@example.com,premium,"test",Bulk import test
+15553333333,Bulk User 3,333 Third Blvd,,Houston,TX,77001,bulk3@example.com,vip,"test",Bulk import test
```
2. Navigate to "Bulk Import Users"
3. Upload the CSV file
4. Click "Upload & Import"

**Expected Result:**
- ✅ Success message: "All 3 users imported successfully!"
- ✅ Results show: 3 total, 3 success, 0 skipped, 0 failed
- ✅ All users created with address data
- ✅ User 3 has empty address2 (NULL)

**Status:** [ ] Pass [ ] Fail

---

#### 11. Bulk Import - Partial Addresses
**Steps:**
1. Create CSV with varying address completeness:
```csv
whatsapp_phone,display_name,address1,address2,city,state,zipcode,email,customer_tier,tags,notes
+15554444444,Partial 1,444 Fourth St,,,TX,75202,partial1@example.com,regular,,Test
+15555555555,Partial 2,,,Los Angeles,CA,90001,partial2@example.com,regular,,Test
+15556666666,Minimal,,,,,,minimal@example.com,regular,,Test
```
2. Upload and import

**Expected Result:**
- ✅ All 3 users imported successfully
- ✅ Partial address data stored correctly
- ✅ Empty fields stored as NULL
- ✅ No validation errors for optional fields

**Status:** [ ] Pass [ ] Fail

---

#### 12. Bulk Import - Old Format (Should Fail)
**Steps:**
1. Create CSV with OLD format (business_name):
```csv
whatsapp_phone,display_name,business_name,email,customer_tier,tags,notes
+15557777777,Old Format,Old Business,old@example.com,regular,,Test
```
2. Upload and import

**Expected Result:**
- ⚠️ Import processes but business_name ignored
- ✅ User created without address fields
- ✅ Error/warning about unrecognized column (optional)

**Status:** [ ] Pass [ ] Fail

---

### 🔍 Cross-Browser Testing

Test in multiple browsers:

#### Chrome
- [ ] Add User form works
- [ ] Update User form works
- [ ] Bulk Import works
- [ ] No console errors

#### Firefox
- [ ] Add User form works
- [ ] Update User form works
- [ ] Bulk Import works
- [ ] No console errors

#### Safari
- [ ] Add User form works
- [ ] Update User form works
- [ ] Bulk Import works
- [ ] No console errors

#### Edge
- [ ] Add User form works
- [ ] Update User form works
- [ ] Bulk Import works
- [ ] No console errors

---

### 📱 Mobile/Responsive Testing

#### Mobile (iPhone/Android)
- [ ] Forms display correctly
- [ ] Address fields are readable
- [ ] Can input data easily
- [ ] Submit buttons work
- [ ] No horizontal scrolling

#### Tablet (iPad)
- [ ] Forms display correctly
- [ ] Multi-column layout works
- [ ] Touch interactions work
- [ ] No UI issues

---

### 🔧 Edge Cases

#### Special Characters in Addresses
- [ ] Unicode characters (é, ñ, etc.)
- [ ] Apostrophes in street names (O'Connor St)
- [ ] Hyphens (123-A Main St)
- [ ] Commas in address (123 Main, Suite A)

#### Long Text
- [ ] Very long street address (100+ chars)
- [ ] Very long city name
- [ ] International addresses
- [ ] PO Box addresses

#### Invalid Data
- [ ] Phone number required validation
- [ ] Invalid email format
- [ ] Special characters in zip code
- [ ] Numbers in state field

---

### 🌐 API Testing

#### Add User Endpoint
```bash
curl -X POST https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "whatsapp_phone": "+15558888888",
    "display_name": "API Test",
    "address1": "123 API Street",
    "city": "API City",
    "state": "CA",
    "zipcode": "90001",
    "email": "api@example.com",
    "customer_tier": "regular"
  }'
```
**Expected:** 201 Created, user data returned with address fields

#### Update User Endpoint
```bash
curl -X PUT https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/+15558888888 \
  -H "Content-Type: application/json" \
  -d '{
    "address1": "456 Updated Street",
    "city": "New City"
  }'
```
**Expected:** 200 OK, updated user data returned

#### Get User Endpoint
```bash
curl https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/+15558888888
```
**Expected:** 200 OK, user data includes address fields (or NULL)

---

### ✅ Performance Testing

- [ ] Page load time < 2 seconds
- [ ] Form submission < 1 second
- [ ] CSV import (100 users) < 10 seconds
- [ ] No memory leaks on form reset
- [ ] Smooth scrolling and interactions

---

### 🔒 Security Testing

- [ ] No sensitive data in browser console
- [ ] No SQL injection via address fields
- [ ] XSS protection (script tags in address)
- [ ] CSRF protection on forms
- [ ] HTTPS only (no mixed content)

---

## Test Summary

### Overview
- Total Tests: 12 main scenarios + 30+ additional checks
- Passed: _____
- Failed: _____
- Blocked: _____

### Critical Issues Found
1. 
2. 
3. 

### Minor Issues Found
1. 
2. 
3. 

### Notes
- 
- 
- 

---

## Sign-Off

- [ ] All critical tests passed
- [ ] All minor issues documented
- [ ] Ready for production deployment

**Tested By:** ___________________
**Date:** ___________________
**Environment:** ___________________
**Browser Versions:** ___________________
