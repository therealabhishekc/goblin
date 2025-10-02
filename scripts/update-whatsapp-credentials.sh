#!/bin/bash

# Update WhatsApp credentials in AWS Secrets Manager
# This script should be used after revoking the old tokens and generating new ones

set -e

ENVIRONMENT=${1:-development}
AWS_REGION=${2:-us-east-1}

echo "🔐 WhatsApp Credentials Update Script"
echo "📍 Environment: $ENVIRONMENT"
echo "📍 Region: $AWS_REGION"
echo ""

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is not installed"
    echo "Please install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS credentials not configured"
    echo "Please run: aws configure"
    exit 1
fi

SECRET_NAME="whatsapp-credentials-$ENVIRONMENT"

echo "🔍 Checking if secret exists..."
if ! aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region "$AWS_REGION" &> /dev/null; then
    echo "❌ Error: Secret '$SECRET_NAME' not found in region '$AWS_REGION'"
    echo "Please deploy the infrastructure first using deploy-github.sh"
    exit 1
fi

echo "✅ Secret found: $SECRET_NAME"
echo ""

# Function to prompt for secure input
secure_read() {
    local prompt="$1"
    local var_name="$2"
    
    echo -n "$prompt"
    read -s value
    echo ""
    
    if [ -z "$value" ]; then
        echo "❌ Error: Value cannot be empty"
        exit 1
    fi
    
    eval "$var_name='$value'"
}

# Get new credentials from user
echo "📝 Please provide the NEW WhatsApp credentials:"
echo "⚠️  Make sure you have revoked the old tokens in Meta Business Suite first!"
echo ""

secure_read "Enter new WhatsApp Token: " NEW_WHATSAPP_TOKEN
secure_read "Enter new Verify Token: " NEW_VERIFY_TOKEN  
secure_read "Enter new Phone Number ID: " NEW_PHONE_NUMBER_ID

echo ""
echo "🔄 Updating secret in AWS Secrets Manager..."

# Create the new secret JSON
SECRET_JSON=$(cat <<EOF
{
  "WHATSAPP_TOKEN": "$NEW_WHATSAPP_TOKEN",
  "VERIFY_TOKEN": "$NEW_VERIFY_TOKEN", 
  "PHONE_NUMBER_ID": "$NEW_PHONE_NUMBER_ID"
}
EOF
)

# Update the secret
if aws secretsmanager update-secret \
    --secret-id "$SECRET_NAME" \
    --secret-string "$SECRET_JSON" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    
    echo "✅ Secret updated successfully!"
    echo ""
    echo "🔄 The App Runner service will automatically use the new credentials"
    echo "📋 No restart required - changes take effect within a few minutes"
    echo ""
    echo "🧪 Test the updated credentials:"
    
    # Get the App Runner service URL
    SERVICE_URL=$(aws cloudformation describe-stacks \
        --stack-name "whatsapp-api-$ENVIRONMENT" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`AppRunnerServiceUrl`].OutputValue' \
        --output text 2>/dev/null)
    
    if [ -n "$SERVICE_URL" ]; then
        echo "   Health check: curl $SERVICE_URL/health"
        echo "   WebHook test: Use $SERVICE_URL/webhook in Meta Developer Console"
    fi
    
    echo ""
    echo "🔒 Security recommendations:"
    echo "1. ✅ Old tokens revoked in Meta Business Suite"  
    echo "2. ✅ New tokens stored securely in AWS Secrets Manager"
    echo "3. 🔄 Remove tokens from your local environment:"
    echo "   unset WHATSAPP_TOKEN VERIFY_TOKEN WHATSAPP_PHONE_NUMBER_ID"
    echo "4. 🔄 Update your local .env file to use placeholder values"
    
else
    echo "❌ Error: Failed to update secret"
    echo "Please check your AWS permissions and try again"
    exit 1
fi