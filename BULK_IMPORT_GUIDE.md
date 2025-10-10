# Bulk User Import Guide

## 📊 Overview

The Bulk Import feature allows you to add multiple users at once using a CSV file. This is perfect for:
- Initial data migration
- Importing customer lists from other systems
- Adding large numbers of users efficiently
- Batch updates from spreadsheets

---

## 🚀 Quick Start

### Step 1: Access Bulk Import
Navigate to the Bulk Import page in your application.

### Step 2: Download Template
Click the "📥 Download CSV Template" button to get a pre-formatted CSV file.

### Step 3: Fill in Your Data
Open the template in Excel, Google Sheets, or any CSV editor and add your users.

### Step 4: Upload
Drag & drop the file or click to browse, then click "📤 Upload & Import".

### Step 5: Review Results
Check the results summary to see which users were successfully imported.

---

## 📄 CSV Format

### Required Columns

**Only `whatsapp_phone` is required**. All other columns are optional.

```csv
whatsapp_phone,display_name,business_name,email,customer_tier,tags,notes
```

### Column Details

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| **whatsapp_phone** | String | ✅ Yes | Phone number with country code | +1234567890 |
| **display_name** | String | ❌ No | User's display name | John Doe |
| **business_name** | String | ❌ No | Business or company name | Doe's Store |
| **email** | String | ❌ No | Email address | john@example.com |
| **customer_tier** | String | ❌ No | Customer tier: regular, premium, or vip | premium |
| **tags** | String | ❌ No | Comma-separated tags in quotes | "vip,loyal,new" |
| **notes** | String | ❌ No | Additional notes | Great customer |

---

## 📝 Example CSV File

```csv
whatsapp_phone,display_name,business_name,email,customer_tier,tags,notes
+1234567890,John Doe,Doe's Store,john@example.com,premium,"vip,regular",Great customer
+0987654321,Jane Smith,Smith Co,jane@example.com,regular,"new",First time buyer
+1122334455,Bob Johnson,Bob's Shop,bob@example.com,vip,"vip,loyal",Top customer
+5544332211,Alice Brown,Alice Inc,alice@example.com,regular,"",New lead
+9988776655,Charlie Davis,,charlie@example.com,premium,"vip",Premium member
```

---

## 💡 Best Practices

### Phone Number Format
- ✅ **Always include country code**: +1234567890
- ✅ **Use + prefix**: +44 for UK, +91 for India, etc.
- ❌ **Don't use**: Spaces, dashes, or parentheses

### Tags Format
- ✅ **Use quotes**: "tag1,tag2,tag3"
- ✅ **Comma-separated**: No spaces after commas
- ✅ **Can be empty**: Leave blank if no tags
- ❌ **Don't use**: Special characters in tag names

### Customer Tier Values
- `regular` - Default tier
- `premium` - Premium customers
- `vip` - VIP customers
- If left empty, defaults to `regular`

### Data Quality
- Remove duplicate phone numbers before uploading
- Validate email addresses
- Keep notes concise
- Use consistent naming conventions

---

## 🔧 Features

### Duplicate Detection
- Users with existing phone numbers are **automatically skipped**
- You'll see a report of skipped users
- No data is overwritten

### Error Handling
- Invalid rows are reported with row numbers
- The rest of the file continues to process
- Detailed error messages help you fix issues

### Progress Tracking
- See real-time import status
- Summary shows: Total, Created, Skipped, Failed
- Detailed list of successful and failed imports

### Validation
- Phone number format validation
- Email format validation
- Customer tier validation
- UTF-8 encoding support

---

## 📊 Import Results

After uploading, you'll see a detailed summary:

### Summary Stats
- **Total Rows**: Total number of data rows processed
- **✅ Created**: Successfully imported users
- **⏭️ Skipped**: Users that already exist
- **❌ Failed**: Rows with errors

### Detailed Lists
- **Successfully Created Users**: List with row numbers and phone numbers
- **Errors & Skipped**: Detailed error messages for troubleshooting

---

## ❌ Common Errors & Solutions

### Error: "Missing required field: whatsapp_phone"
**Solution**: Ensure every row has a phone number in the first column.

### Error: "User already exists"
**Solution**: This user is already in your database. This is normal and safe to ignore.

### Error: "Invalid phone number format"
**Solution**: Make sure phone includes country code with + prefix (e.g., +1234567890).

### Error: "Invalid email format"
**Solution**: Check the email address is valid (e.g., user@domain.com).

### Error: "Invalid customer_tier"
**Solution**: Use only: regular, premium, or vip.

### Error: "Failed to parse CSV"
**Solution**: 
- Make sure file is saved as CSV (not Excel)
- Check for special characters
- Ensure proper UTF-8 encoding

---

## 🎯 Tips for Large Imports

### File Size Limits
- **Recommended**: Up to 1,000 users per file
- **Maximum**: 10,000 users per file
- For larger imports, split into multiple files

### Performance
- Imports process at ~100 users per second
- Large files may take a few minutes
- Don't close the browser during import

### Data Preparation
1. **Clean your data** in Excel/Google Sheets first
2. **Remove duplicates** before uploading
3. **Validate** phone numbers and emails
4. **Test** with a small file first (10-20 rows)
5. **Save as CSV** (not Excel format)

---

## 📋 Step-by-Step Tutorial

### Using Excel

1. **Open Template**
   - Download the CSV template
   - Open in Microsoft Excel

2. **Add Your Data**
   - Fill in each row with user information
   - Use Tab key to move between cells
   - Phone numbers: Type ' before number to prevent formatting

3. **Save as CSV**
   - File → Save As
   - Choose "CSV UTF-8 (Comma delimited) (*.csv)"
   - Click Save

4. **Upload**
   - Drag the CSV file to the import page
   - Or click to browse and select

### Using Google Sheets

1. **Open Template**
   - Download the CSV template
   - Import to Google Sheets (File → Import)

2. **Add Your Data**
   - Fill in each row
   - Use format: Plain text for phone numbers

3. **Download as CSV**
   - File → Download → Comma Separated Values (.csv)

4. **Upload**
   - Use the downloaded file for import

---

## 🔐 Security & Privacy

### Data Handling
- ✅ Files are processed server-side
- ✅ No data is stored on our servers after processing
- ✅ Files are not cached or logged
- ✅ Secure HTTPS transmission

### Data Validation
- ✅ All data is validated before import
- ✅ Invalid data is rejected with clear messages
- ✅ Existing users are protected from overwrites
- ✅ Atomic operations ensure data consistency

---

## 🐛 Troubleshooting

### Import Not Starting
1. Check file is CSV format
2. Ensure file name ends with .csv
3. Try a smaller test file first
4. Check browser console for errors

### Some Rows Failed
1. Check the error messages in results
2. Common issues:
   - Missing phone number
   - Invalid email format
   - Duplicate phone numbers in file
3. Fix errors and re-upload

### All Rows Skipped
- This means all users already exist in your database
- Check if you've already imported this file
- Use Update feature instead for existing users

### Slow Import
- Large files (>1000 rows) take time
- Don't refresh or close the browser
- Wait for the progress indicator
- Consider splitting into smaller files

---

## 🔗 API Reference

### Endpoint
```
POST /api/users/bulk-import
```

### Request
```bash
curl -X POST https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/bulk-import \
  -H "Content-Type: multipart/form-data" \
  -F "file=@users.csv"
```

### Response
```json
{
  "status": "completed",
  "message": "Processed 100 rows: 95 created, 3 skipped, 2 failed",
  "total": 100,
  "success": 95,
  "failed": 2,
  "skipped": 3,
  "errors": [
    {
      "row": 5,
      "phone": "+1234567890",
      "error": "User already exists"
    }
  ],
  "created_users": [
    {
      "row": 2,
      "phone": "+0987654321",
      "name": "John Doe"
    }
  ]
}
```

---

## 📚 Additional Resources

### Template Files
- **CSV Template**: Download from the import page
- **Sample Data**: Included in template with examples

### Related Features
- **Add Single User**: For adding one user at a time
- **Update User**: For modifying existing users
- **User Management**: View and manage all users

### Support
- Check error messages in import results
- Review this guide for solutions
- Test with small files first
- Verify CSV format matches template

---

## ✅ Checklist Before Import

Before uploading your CSV file, verify:

- [ ] File is saved as CSV format
- [ ] All phone numbers include country code with +
- [ ] No duplicate phone numbers in the file
- [ ] Email addresses are valid
- [ ] Customer tiers are: regular, premium, or vip
- [ ] Tags are in quotes if using commas
- [ ] File size is reasonable (<1000 rows for best performance)
- [ ] Tested with a small sample first
- [ ] Backup of original data exists

---

## 🎉 Success!

Once imported:
- Users appear immediately in your database
- They can start receiving messages
- You can update their information individually
- Search and filter work on imported users
- All features work as expected

Bulk import makes it easy to get started with hundreds or thousands of users in minutes!
