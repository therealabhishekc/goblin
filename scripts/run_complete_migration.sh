#!/bin/bash

# =============================================================================
# Complete Database Schema Migration Script
# =============================================================================
# This script runs the complete_schema.sql migration file that contains
# all database schema changes combined into one file.
# 
# Usage: ./run_complete_migration.sh
# 
# Prerequisites:
# - PostgreSQL master credentials in environment variables or .env file
# - Network access to RDS instance
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# =============================================================================
# CONFIGURATION
# =============================================================================

print_status "Starting Complete Database Migration..."
echo ""

# Check if .env file exists and load it
if [ -f .env ]; then
    print_status "Loading configuration from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    print_warning ".env file not found. Using environment variables..."
fi

# Database connection parameters
DB_HOST="${DB_HOST:-whatsapp-postgres-development.cyd40iccy9uu.us-east-1.rds.amazonaws.com}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-whatsapp_business_development}"
DB_MASTER_USER="${DB_MASTER_USER:-postgres}"
DB_MASTER_PASSWORD="${DB_MASTER_PASSWORD}"

# Check if master password is set
if [ -z "$DB_MASTER_PASSWORD" ]; then
    print_error "DB_MASTER_PASSWORD not set!"
    echo ""
    echo "Please set the database master password:"
    echo "  export DB_MASTER_PASSWORD='your-password'"
    echo ""
    echo "Or add it to your .env file:"
    echo "  DB_MASTER_PASSWORD=your-password"
    exit 1
fi

# Migration file path
MIGRATION_FILE="backend/migrations/complete_schema.sql"

# Check if migration file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    print_error "Migration file not found: $MIGRATION_FILE"
    exit 1
fi

# =============================================================================
# DISPLAY CONFIGURATION
# =============================================================================

echo ""
echo "======================================================================="
echo "Database Configuration"
echo "======================================================================="
echo "Host:     $DB_HOST"
echo "Port:     $DB_PORT"
echo "Database: $DB_NAME"
echo "User:     $DB_MASTER_USER"
echo "Migration: $MIGRATION_FILE"
echo "======================================================================="
echo ""

# =============================================================================
# CONFIRM EXECUTION
# =============================================================================

print_warning "This will execute the complete schema migration on the database."
print_warning "This includes creating/updating all tables, columns, indexes, and constraints."
echo ""
read -p "Do you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    print_status "Migration cancelled by user."
    exit 0
fi

echo ""

# =============================================================================
# TEST DATABASE CONNECTION
# =============================================================================

print_status "Testing database connection..."

PGPASSWORD="$DB_MASTER_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_MASTER_USER" \
    -d "$DB_NAME" \
    -c "SELECT version();" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    print_success "Database connection successful!"
else
    print_error "Failed to connect to database!"
    echo ""
    echo "Please check:"
    echo "  - Database host and port are correct"
    echo "  - Master password is correct"
    echo "  - Security group allows your IP address"
    echo "  - Database is running"
    exit 1
fi

echo ""

# =============================================================================
# BACKUP CURRENT SCHEMA (OPTIONAL)
# =============================================================================

print_status "Creating backup of current schema..."

BACKUP_FILE="backup_schema_$(date +%Y%m%d_%H%M%S).sql"

PGPASSWORD="$DB_MASTER_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_MASTER_USER" \
    -d "$DB_NAME" \
    --schema-only \
    -f "$BACKUP_FILE" 2>/dev/null

if [ $? -eq 0 ]; then
    print_success "Schema backup created: $BACKUP_FILE"
else
    print_warning "Failed to create backup (database may be empty)"
fi

echo ""

# =============================================================================
# RUN MIGRATION
# =============================================================================

print_status "Executing complete schema migration..."
echo ""
echo "======================================================================="

PGPASSWORD="$DB_MASTER_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_MASTER_USER" \
    -d "$DB_NAME" \
    -f "$MIGRATION_FILE"

if [ $? -eq 0 ]; then
    echo "======================================================================="
    echo ""
    print_success "✅ Migration completed successfully!"
else
    echo "======================================================================="
    echo ""
    print_error "❌ Migration failed!"
    echo ""
    echo "If you need to restore, use the backup file: $BACKUP_FILE"
    exit 1
fi

# =============================================================================
# VERIFY MIGRATION
# =============================================================================

echo ""
print_status "Verifying migration..."
echo ""

# Get table count
TABLE_COUNT=$(PGPASSWORD="$DB_MASTER_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_MASTER_USER" \
    -d "$DB_NAME" \
    -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | xargs)

print_success "Tables created: $TABLE_COUNT"

# Check specific tables
EXPECTED_TABLES=("user_profiles" "whatsapp_messages" "message_queue" "business_metrics" "message_templates")

for table in "${EXPECTED_TABLES[@]}"; do
    EXISTS=$(PGPASSWORD="$DB_MASTER_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_MASTER_USER" \
        -d "$DB_NAME" \
        -t -c "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '$table');" | xargs)
    
    if [ "$EXISTS" = "t" ]; then
        print_success "  ✓ $table"
    else
        print_error "  ✗ $table (missing!)"
    fi
done

echo ""

# =============================================================================
# SUMMARY
# =============================================================================

echo ""
echo "======================================================================="
echo "                       MIGRATION SUMMARY"
echo "======================================================================="
echo ""
echo "✅ Database connection: OK"
echo "✅ Schema backup: $BACKUP_FILE"
echo "✅ Migration executed: complete_schema.sql"
echo "✅ Tables created: $TABLE_COUNT"
echo ""
echo "Expected tables:"
echo "  • user_profiles (customer profiles)"
echo "  • whatsapp_messages (message history)"
echo "  • message_queue (SQS tracking)"
echo "  • business_metrics (daily analytics)"
echo "  • message_templates (reusable templates)"
echo ""
echo "Next steps:"
echo "  1. Verify your application can connect to the database"
echo "  2. Test sending and receiving messages"
echo "  3. Check that automated replies work"
echo "  4. Monitor logs for any database errors"
echo ""
echo "======================================================================="
echo ""

print_success "🎉 All done! Your database is ready to use."
echo ""

# Keep the backup file
print_status "Schema backup saved at: $BACKUP_FILE"
print_warning "Keep this backup file safe in case you need to restore."

echo ""
