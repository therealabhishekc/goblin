#!/bin/bash

# Script to run database migration on AWS RDS
# Usage: ./run_migration_on_rds.sh

set -e

echo "🔄 Running whatsapp_messages timestamp migration on AWS RDS..."

# Get DATABASE_URL from AWS Secrets Manager or environment
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    echo "Please set DATABASE_URL to your RDS connection string"
    exit 1
fi

# Check if migration file exists
MIGRATION_FILE="backend/migrations/add_whatsapp_messages_timestamps.sql"
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ ERROR: Migration file not found: $MIGRATION_FILE"
    exit 1
fi

echo "📝 Migration file: $MIGRATION_FILE"
echo "🔗 Database: $(echo $DATABASE_URL | grep -o '@[^:]*:' | sed 's/@//;s/://')"

# Run migration
echo "🚀 Executing migration..."
psql "$DATABASE_URL" -f "$MIGRATION_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully!"
    echo ""
    echo "Verifying changes..."
    psql "$DATABASE_URL" -c "\d whatsapp_messages" | grep -E "(sent_at|delivered_at|read_at|failed)"
else
    echo "❌ Migration failed!"
    exit 1
fi

echo ""
echo "✨ All done! The whatsapp_messages table now has timestamp columns."
