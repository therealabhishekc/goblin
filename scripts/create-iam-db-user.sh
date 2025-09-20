#!/bin/bash

# Create IAM Database User for WhatsApp Business API
set -e

ENVIRONMENT=${1:-development}
AWS_REGION=${2:-us-east-1}

echo "🔐 Creating IAM database user for environment: $ENVIRONMENT"

# Get database endpoint from CloudFormation
DB_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "whatsapp-api-$ENVIRONMENT" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
    --output text)

if [ -z "$DB_ENDPOINT" ]; then
    echo "❌ Error: Could not retrieve database endpoint from CloudFormation stack"
    exit 1
fi

echo "📊 Database endpoint: $DB_ENDPOINT"

# Get the RDS master credentials from Secrets Manager
echo "🔑 Retrieving database credentials..."
SECRET_ARN=$(aws rds describe-db-instances \
    --db-instance-identifier "whatsapp-postgres-$ENVIRONMENT" \
    --region "$AWS_REGION" \
    --query 'DBInstances[0].MasterUserSecret.SecretArn' \
    --output text)

if [ "$SECRET_ARN" = "None" ] || [ -z "$SECRET_ARN" ]; then
    echo "❌ Error: Could not retrieve secret ARN for database master user"
    exit 1
fi

# Get the master password
MASTER_CREDENTIALS=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_ARN" \
    --region "$AWS_REGION" \
    --query 'SecretString' \
    --output text)

MASTER_PASSWORD=$(echo "$MASTER_CREDENTIALS" | python3 -c "import sys, json; print(json.load(sys.stdin)['password'])")
MASTER_USER=$(echo "$MASTER_CREDENTIALS" | python3 -c "import sys, json; print(json.load(sys.stdin)['username'])")

echo "✅ Retrieved master credentials"

# Create IAM database user
echo "👤 Creating IAM database user 'app_user'..."

PGPASSWORD="$MASTER_PASSWORD" psql \
    -h "$DB_ENDPOINT" \
    -p 5432 \
    -U "$MASTER_USER" \
    -d "whatsapp_business_$ENVIRONMENT" \
    -c "CREATE USER app_user;" 2>/dev/null || echo "ℹ️  User app_user already exists"

PGPASSWORD="$MASTER_PASSWORD" psql \
    -h "$DB_ENDPOINT" \
    -p 5432 \
    -U "$MASTER_USER" \
    -d "whatsapp_business_$ENVIRONMENT" \
    -c "GRANT rds_iam TO app_user;"

PGPASSWORD="$MASTER_PASSWORD" psql \
    -h "$DB_ENDPOINT" \
    -p 5432 \
    -U "$MASTER_USER" \
    -d "whatsapp_business_$ENVIRONMENT" \
    -c "GRANT CONNECT ON DATABASE whatsapp_business_$ENVIRONMENT TO app_user;"

PGPASSWORD="$MASTER_PASSWORD" psql \
    -h "$DB_ENDPOINT" \
    -p 5432 \
    -U "$MASTER_USER" \
    -d "whatsapp_business_$ENVIRONMENT" \
    -c "GRANT USAGE ON SCHEMA public TO app_user;"

PGPASSWORD="$MASTER_PASSWORD" psql \
    -h "$DB_ENDPOINT" \
    -p 5432 \
    -U "$MASTER_USER" \
    -d "whatsapp_business_$ENVIRONMENT" \
    -c "GRANT CREATE ON SCHEMA public TO app_user;"

PGPASSWORD="$MASTER_PASSWORD" psql \
    -h "$DB_ENDPOINT" \
    -p 5432 \
    -U "$MASTER_USER" \
    -d "whatsapp_business_$ENVIRONMENT" \
    -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;"

PGPASSWORD="$MASTER_PASSWORD" psql \
    -h "$DB_ENDPOINT" \
    -p 5432 \
    -U "$MASTER_USER" \
    -d "whatsapp_business_$ENVIRONMENT" \
    -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_user;"

PGPASSWORD="$MASTER_PASSWORD" psql \
    -h "$DB_ENDPOINT" \
    -p 5432 \
    -U "$MASTER_USER" \
    -d "whatsapp_business_$ENVIRONMENT" \
    -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO app_user;"

PGPASSWORD="$MASTER_PASSWORD" psql \
    -h "$DB_ENDPOINT" \
    -p 5432 \
    -U "$MASTER_USER" \
    -d "whatsapp_business_$ENVIRONMENT" \
    -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO app_user;"

echo "✅ IAM database user 'app_user' created successfully with proper permissions"
echo ""
echo "🎉 Database setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Your App Runner service should now be able to connect to the database"
echo "   2. Check the App Runner service logs for any connection issues"
echo "   3. Test the health endpoint: <app-runner-url>/health/database"