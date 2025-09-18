#!/bin/bash

# Database IAM User Setup Script
# This script creates the necessary database user for IAM authentication

set -e

# Configuration
DB_HOST="${1:-localhost}"
DB_NAME="${2:-whatsapp_business_development}"
DB_MASTER_USER="${3:-postgres}"
DB_IAM_USER="${4:-app_user}"

echo "🔧 Setting up IAM database user..."
echo "Host: $DB_HOST"
echo "Database: $DB_NAME"
echo "IAM User: $DB_IAM_USER"

# Create the IAM user and grant permissions
psql -h "$DB_HOST" -U "$DB_MASTER_USER" -d "$DB_NAME" << EOF
-- Create IAM user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_IAM_USER') THEN
        CREATE USER $DB_IAM_USER;
        RAISE NOTICE 'User $DB_IAM_USER created';
    ELSE
        RAISE NOTICE 'User $DB_IAM_USER already exists';
    END IF;
END
\$\$;

-- Grant rds_iam role to enable IAM authentication
GRANT rds_iam TO $DB_IAM_USER;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE $DB_NAME TO $DB_IAM_USER;
GRANT USAGE ON SCHEMA public TO $DB_IAM_USER;
GRANT CREATE ON SCHEMA public TO $DB_IAM_USER;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO $DB_IAM_USER;
GRANT SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO $DB_IAM_USER;

-- Grant permissions on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $DB_IAM_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, UPDATE ON SEQUENCES TO $DB_IAM_USER;

\q
EOF

echo "✅ IAM database user setup completed successfully!"
echo ""
echo "🔐 Your application can now use IAM authentication with user: $DB_IAM_USER"
echo ""
echo "📋 Next steps:"
echo "1. Set USE_IAM_AUTH=true in your environment variables"
echo "2. Configure these environment variables:"
echo "   DB_HOST=$DB_HOST"
echo "   DB_NAME=$DB_NAME"
echo "   DB_USER=$DB_IAM_USER"
echo "   AWS_REGION=us-east-1"
echo "3. Deploy your application with the AppRunner IAM role"
