#!/bin/bash

# Quick fix script for IAM authentication issue
# This script enables IAM authentication for the app_user

set -e

echo "=================================================="
echo "  RDS IAM Authentication Fix"
echo "=================================================="
echo ""

ENVIRONMENT=${1:-development}
AWS_REGION=${2:-us-east-1}

echo "🔧 Environment: $ENVIRONMENT"
echo "🌍 Region: $AWS_REGION"
echo ""

# Check if we have AWS credentials
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ Error: AWS credentials not configured"
    echo "   Please run: aws configure"
    exit 1
fi

echo "✅ AWS credentials configured"
echo ""

# Run the IAM user setup script
echo "🚀 Running IAM database user setup..."
echo "------------------------------------------------"
./scripts/create-iam-db-user.sh "$ENVIRONMENT" "$AWS_REGION"

echo ""
echo "=================================================="
echo "  ✅ IAM Authentication Fix Complete!"
echo "=================================================="
echo ""
echo "📋 Next Steps:"
echo "   1. Wait 30 seconds for App Runner to reconnect"
echo "   2. Check App Runner logs for success messages"
echo "   3. Test your WhatsApp webhook"
echo ""
echo "🔍 To monitor App Runner logs:"
echo "   aws logs tail /aws/apprunner/whatsapp-api-${ENVIRONMENT}/application --follow --region ${AWS_REGION}"
echo ""
