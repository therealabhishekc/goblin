# Database Migrations

This directory contains SQL migration files for the WhatsApp Business API database.

## 📁 Files

### Combined Migration (USE THIS)
- **`complete_schema.sql`** - Complete database schema with all migrations combined
  - Creates all tables, columns, indexes, and constraints
  - Safe to run multiple times (uses IF NOT EXISTS)
  - Includes all historical migrations

### Individual Migration Files (LEGACY - for reference only)
These files have been combined into `complete_schema.sql`:
1. `00_init_schema.sql` - Initial schema (user_profiles, whatsapp_messages, message_queue)
2. `add_direction_column.sql` - Adds direction column to whatsapp_messages
3. `add_subscription_column.sql` - Adds subscription column to user_profiles
4. `add_business_metrics_table.sql` - Adds business_metrics and message_templates tables
5. `update_status_values.sql` - Updates status constraints

## 🚀 How to Run Migrations

### Option 1: Use the Complete Migration Script (RECOMMENDED)

From the project root directory:

```bash
# Make sure you have database credentials
export DB_MASTER_PASSWORD='your-master-password'

# Run the complete migration
./run_complete_migration.sh
```

The script will:
1. ✅ Load configuration from `.env` file
2. ✅ Test database connection
3. ✅ Create backup of current schema
4. ✅ Execute all migrations
5. ✅ Verify tables were created
6. ✅ Show summary

### Option 2: Run Manually with psql

```bash
# Set environment variables
export DB_HOST="whatsapp-postgres-development.cyd40iccy9uu.us-east-1.rds.amazonaws.com"
export DB_NAME="whatsapp_business_development"
export DB_MASTER_USER="postgres"
export DB_MASTER_PASSWORD="your-password"

# Run migration
PGPASSWORD="$DB_MASTER_PASSWORD" psql \
    -h "$DB_HOST" \
    -U "$DB_MASTER_USER" \
    -d "$DB_NAME" \
    -f backend/migrations/complete_schema.sql
```

## 📊 Database Schema

### Tables Created

1. **`user_profiles`** - Customer information
   - Stores WhatsApp customer data
   - Subscription status for template messages
   - Customer tier, tags, notes

2. **`whatsapp_messages`** - Message history
   - Both incoming and outgoing messages
   - Status tracking (processing, processed, failed, sent, delivered, read)
   - Direction (incoming, outgoing)

3. **`message_queue`** - SQS queue tracking
   - Tracks message processing through SQS
   - Status monitoring

4. **`business_metrics`** - Daily analytics
   - Messages received/sent counts
   - Unique users
   - Response time averages
   - Popular keywords

5. **`message_templates`** - Reusable templates
   - Template text and variables
   - Usage tracking
   - Category organization

## 🔍 Verification

After running migrations, verify with:

```sql
-- Show all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE';

-- Show row counts
SELECT 'user_profiles' as table_name, COUNT(*) FROM user_profiles
UNION ALL
SELECT 'whatsapp_messages', COUNT(*) FROM whatsapp_messages
UNION ALL
SELECT 'message_queue', COUNT(*) FROM message_queue
UNION ALL
SELECT 'business_metrics', COUNT(*) FROM business_metrics
UNION ALL
SELECT 'message_templates', COUNT(*) FROM message_templates;
```

## ⚠️ Important Notes

### Safe to Run Multiple Times
The `complete_schema.sql` file uses:
- `CREATE TABLE IF NOT EXISTS` - Won't fail if table exists
- `DO $$ BEGIN ... IF NOT EXISTS ... END $$` - Conditional column additions
- `DROP CONSTRAINT IF EXISTS` - Removes old constraints before adding new ones

### When to Run Migrations
Run migrations when:
- 🆕 Setting up a new database
- 📦 Deploying to a new environment
- 🔄 After pulling code with schema changes
- 🐛 Fixing missing tables/columns

### Permissions
The migration script:
- Requires **master PostgreSQL credentials** (not app_user)
- Creates tables with proper ownership
- Grants permissions to `app_user` automatically

## 🔐 Security

**Never commit credentials!**
- Use environment variables
- Use `.env` file (already in `.gitignore`)
- Rotate credentials regularly

## 📚 Adding New Migrations

When adding new tables/columns:

1. **Update `complete_schema.sql`**
   - Add your changes to the appropriate section
   - Use `IF NOT EXISTS` for safety
   - Add comments explaining the change

2. **Test locally first**
   ```bash
   # Test on local database
   ./run_complete_migration.sh
   ```

3. **Deploy to production**
   - Run migration script
   - Verify tables exist
   - Deploy application code

## 🆘 Troubleshooting

### Error: "relation already exists"
- ✅ This is OK! The migration handles existing tables
- The script uses `IF NOT EXISTS` to avoid errors

### Error: "column already exists"  
- ✅ This is OK! The migration checks before adding columns
- Uses conditional `DO $$ BEGIN ... END $$` blocks

### Error: "connection refused"
- Check VPN/network connection
- Verify security group rules
- Confirm database endpoint is correct

### Error: "authentication failed"
- Verify master password is correct
- Check username (should be `postgres`)
- Ensure credentials are set in environment

## 📞 Support

If you encounter issues:
1. Check CloudWatch logs for application errors
2. Verify database connection with `psql`
3. Review backup files if rollback needed
4. Check AWS RDS console for database status

---

**Last Updated:** 2025-10-03  
**Database:** AWS RDS PostgreSQL  
**Environment:** Development
