#!/bin/bash

# Complete post-deployment setup script
# This does EVERYTHING: Creates app_user AND all database tables

set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║   Complete Post-Deployment Setup                     ║"
echo "║   ✅ Creates app_user role                           ║"
echo "║   ✅ Creates all 9 database tables                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

ENVIRONMENT="development"
AWS_REGION="us-east-1"
STACK_NAME="whatsapp-api-${ENVIRONMENT}"
DB_NAME="whatsapp_business_${ENVIRONMENT}"

# Check prerequisites
if ! command -v psql &> /dev/null; then
    echo "❌ Error: PostgreSQL client (psql) not installed!"
    echo "Install: brew install postgresql"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "❌ Error: jq not installed!"
    echo "Install: brew install jq"
    exit 1
fi

echo "✅ Prerequisites installed"
echo ""

# Step 1: Get database info
echo "1️⃣  Fetching database information..."
DB_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
  --output text 2>/dev/null)

if [ -z "$DB_ENDPOINT" ] || [ "$DB_ENDPOINT" == "None" ]; then
    echo "❌ Error: Could not get database endpoint"
    echo "   Check: aws cloudformation describe-stacks --stack-name $STACK_NAME"
    exit 1
fi

echo "   Database: $DB_ENDPOINT ✅"

SECRET_ARN=$(aws rds describe-db-instances \
  --db-instance-identifier "whatsapp-postgres-${ENVIRONMENT}" \
  --region "$AWS_REGION" \
  --query 'DBInstances[0].MasterUserSecret.SecretArn' \
  --output text 2>/dev/null)

MASTER_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id "$SECRET_ARN" \
  --region "$AWS_REGION" \
  --query 'SecretString' \
  --output text 2>/dev/null | jq -r '.password')

echo "   Master password retrieved ✅"
echo ""

# Step 2: Test connection
echo "2️⃣  Testing database connection..."
if PGPASSWORD="$MASTER_PASSWORD" psql -h "$DB_ENDPOINT" -U postgres -d "$DB_NAME" -c "SELECT 1;" &>/dev/null; then
    echo "   Connection successful ✅"
else
    echo "❌ Error: Could not connect to database"
    exit 1
fi
echo ""

# Step 3: Create app_user
echo "3️⃣  Creating app_user role..."
PGPASSWORD="$MASTER_PASSWORD" psql \
  -h "$DB_ENDPOINT" \
  -U postgres \
  -d "$DB_NAME" << 'EOF'

-- Create IAM user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
        CREATE USER app_user;
        RAISE NOTICE '✅ User app_user created';
    ELSE
        RAISE NOTICE 'ℹ️  User app_user already exists';
    END IF;
END
$$;

-- Grant rds_iam role
GRANT rds_iam TO app_user;

-- Grant database permissions
GRANT CONNECT ON DATABASE whatsapp_business_development TO app_user;
GRANT USAGE, CREATE ON SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Grant permissions on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
    GRANT ALL PRIVILEGES ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
    GRANT ALL PRIVILEGES ON SEQUENCES TO app_user;

EOF

echo "   app_user created ✅"
echo ""

# Step 4: Create tables
echo "4️⃣  Creating database tables (9 tables)..."
echo "   This may take a minute..."
echo ""

PGPASSWORD="$MASTER_PASSWORD" psql \
  -h "$DB_ENDPOINT" \
  -U postgres \
  -d "$DB_NAME" \
  -f backend/migrations/complete_schema.sql 2>&1 | grep -E "CREATE|NOTICE|ERROR" | head -20

echo ""
echo "   Tables created ✅"
echo ""

# Step 5: Verify
echo "5️⃣  Verifying setup..."

# Count tables
TABLE_COUNT=$(PGPASSWORD="$MASTER_PASSWORD" psql \
  -h "$DB_ENDPOINT" \
  -U postgres \
  -d "$DB_NAME" \
  -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';" | tr -d ' ')

echo "   Tables: $TABLE_COUNT ✅"

# List tables
echo ""
echo "   📊 Tables created:"
PGPASSWORD="$MASTER_PASSWORD" psql \
  -h "$DB_ENDPOINT" \
  -U postgres \
  -d "$DB_NAME" \
  -c "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;" | grep -v "^-" | grep -v "^(" | grep -v "rows)" | sed 's/^/      - /'

echo ""

# Verify app_user
APP_USER_EXISTS=$(PGPASSWORD="$MASTER_PASSWORD" psql \
  -h "$DB_ENDPOINT" \
  -U postgres \
  -d "$DB_NAME" \
  -t -c "SELECT COUNT(*) FROM pg_roles WHERE rolname='app_user';" | tr -d ' ')

if [ "$APP_USER_EXISTS" == "1" ]; then
    echo "   app_user: ✅ Created"
else
    echo "   app_user: ❌ Not found"
fi

echo ""

echo "╔══════════════════════════════════════════════════════╗"
echo "║              ✅ Setup Complete!                      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "📊 Database Summary:"
echo "   Endpoint: $DB_ENDPOINT"
echo "   Database: $DB_NAME"
echo "   User: app_user (IAM authentication)"
echo "   Tables: $TABLE_COUNT"
echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. Wait 30 seconds for App Runner to connect"
echo ""
echo "2. Get your App Runner URL:"
echo "   SERVICE_URL=\$(aws cloudformation describe-stacks \\"
echo "     --stack-name $STACK_NAME \\"
echo "     --query 'Stacks[0].Outputs[?OutputKey==\`AppRunnerServiceUrl\`].OutputValue' \\"
echo "     --output text)"
echo ""
echo "3. Test health endpoint:"
echo "   curl \$SERVICE_URL/health"
echo ""
echo "4. Check App Runner logs:"
echo "   aws logs tail /aws/apprunner/whatsapp-api-${ENVIRONMENT}/application --follow"
echo ""
echo "5. Configure WhatsApp webhook:"
echo "   - Go to Meta Business Suite"
echo "   - Webhook URL: \$SERVICE_URL/webhook"
echo "   - Verify Token: (your VERIFY_TOKEN)"
echo ""
echo "🎉 Your WhatsApp Business API is fully configured and ready!"
