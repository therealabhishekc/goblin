#!/bin/bash

# PostgreSQL Database Setup Script for WhatsApp Business App

echo "🗄️  Setting up PostgreSQL database for WhatsApp Business App..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    echo "   macOS: brew services start postgresql"
    echo "   Linux: sudo systemctl start postgresql"
    exit 1
fi

# Database configuration
DB_NAME="whatsapp_business"
DB_USER="postgres"

echo "📊 Creating database: $DB_NAME"

# Create database if it doesn't exist
psql -h localhost -U $DB_USER -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || psql -h localhost -U $DB_USER -c "CREATE DATABASE $DB_NAME"

if [ $? -eq 0 ]; then
    echo "✅ Database '$DB_NAME' created/verified successfully"
else
    echo "❌ Failed to create database"
    exit 1
fi

# Test connection
echo "🔗 Testing database connection..."
psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT version();" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Database connection successful"
    echo ""
    echo "🎉 PostgreSQL setup complete!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Update your .env file with: DATABASE_URL=postgresql://postgres:password@localhost:5432/whatsapp_business"
    echo "   2. Install Python dependencies: pip install -r requirements.txt"
    echo "   3. Start your application: uvicorn app.main:app --reload"
    echo "   4. Database tables will be created automatically on first run"
else
    echo "❌ Database connection failed"
    exit 1
fi
