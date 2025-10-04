# RDS IAM Authentication Issue - Analysis & Solution

## 🔍 Current Problem

**Error**: `PAM authentication failed for user "app_user"`

**Root Cause**: The database user `app_user` exists in PostgreSQL but is **NOT configured for IAM authentication**. It was created as a regular password-based user.

---

## 🧩 Current Setup

### What's Configured Correctly ✅
1. **App Runner IAM Role** has the `rds-db:connect` permission
2. **CloudFormation** sets `USE_IAM_AUTH=true` 
3. **Code** (`database.py`) has IAM token generation logic
4. **DATABASE_URL** is set without password: `postgresql://app_user@<host>:5432/whatsapp_business_development?sslmode=require`

### What's Missing ❌
1. **Database user `app_user`** was NOT granted `rds_iam` role
2. The script `create-iam-db-user.sh` exists but was never executed
3. Connection fails because PostgreSQL doesn't allow IAM authentication for this user

---

## 📊 Why This Happened

When the RDS database was initially created:
1. CloudFormation created the RDS instance
2. The setup scripts (`setup-postgresql.sh`) created the `app_user` with **password authentication**
3. The IAM setup script (`create-iam-db-user.sh`) was **never run** to convert it to IAM auth

---

## 🛠️ Solution Options

### **Option 1: Disable IAM Auth (Quick Fix - NOT RECOMMENDED)**
- Set `USE_IAM_AUTH=false` in CloudFormation
- Add `DB_PASSWORD` to environment variables
- Update `DATABASE_URL` to include password
- **Downside**: Less secure, password management overhead

### **Option 2: Enable IAM Auth Properly (RECOMMENDED)** ⭐

This is the secure, AWS best-practice approach.

#### Steps Required:

1. **Run the IAM user setup script** (from local machine):
   ```bash
   cd /Users/abskchsk/Documents/govindjis/wa-app
   ./scripts/create-iam-db-user.sh development us-east-1
   ```

2. **What this script does**:
   - Connects to RDS using **master credentials** (from Secrets Manager)
   - Creates/updates `app_user` 
   - Grants `rds_iam` role: `GRANT rds_iam TO app_user;`
   - Grants all necessary table/schema permissions

3. **Verify the fix**:
   - App Runner will automatically reconnect
   - Check logs for: `✅ IAM database token generated successfully`
   - Test health endpoint: `https://<app-runner-url>/health`

---

## 🔐 How IAM Authentication Works

```
┌──────────────┐         ┌─────────────┐         ┌──────────────┐
│              │  1. Get  │             │ 2. Auth │              │
│  App Runner  │  Token   │  RDS IAM    │  Token  │   RDS        │
│  (app_user)  ├─────────→│  Service    ├────────→│  PostgreSQL  │
│              │          │             │         │              │
└──────────────┘          └─────────────┘         └──────────────┘
      ↓                                                  ↓
      └──────────────────────────────────────────────────┘
              3. Connect with token as password
```

**Key Points**:
- Token is valid for 15 minutes
- Generated using AWS SDK: `rds_client.generate_db_auth_token()`
- Requires IAM permission: `rds-db:connect`
- Database user must have `rds_iam` role

---

## 🎯 Recommended Action

**Execute Option 2** - Run the IAM setup script:

```bash
# From your local machine (ensure AWS credentials are configured)
cd /Users/abskchsk/Documents/govindjis/wa-app
chmod +x scripts/create-iam-db-user.sh
./scripts/create-iam-db-user.sh development us-east-1
```

**Expected Output**:
```
🔐 Creating IAM database user for environment: development
📊 Database endpoint: whatsapp-postgres-development.cyd40iccy9uu.us-east-1.rds.amazonaws.com
🔑 Retrieving database credentials...
✅ Retrieved master credentials
👤 Creating IAM database user 'app_user'...
ℹ️  User app_user already exists
✅ IAM database user 'app_user' created successfully with proper permissions
🎉 Database setup complete!
```

**After running this**:
- App will automatically start working
- No code changes needed
- Secure IAM-based authentication enabled

---

## 📝 Additional Notes

### If Script Fails with Connection Error:
- Check your security group allows your IP (AllowedCIDR parameter)
- Ensure AWS credentials have `secretsmanager:GetSecretValue` permission
- Verify you can reach the RDS endpoint from your machine

### If You Prefer Password Auth Instead:
1. Update CloudFormation parameter `USE_IAM_AUTH` to `false`
2. Add `DB_PASSWORD` parameter to CloudFormation
3. Update App Runner environment variables with password
4. Redeploy the stack

---

## 🚨 Current State

**Status**: ❌ IAM auth enabled in code, but database user not configured for IAM
**Impact**: All database operations failing
**Urgency**: HIGH - App is currently non-functional
**Fix Time**: ~5 minutes (run one script)

---

## ✅ Verification Checklist

After running the script, verify:
- [ ] Script completes without errors
- [ ] App Runner logs show: "✅ Database connection initialized successfully"
- [ ] No more "PAM authentication failed" errors
- [ ] Messages are being processed
- [ ] Health endpoint returns 200 OK
