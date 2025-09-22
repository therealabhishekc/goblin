#!/bin/bash
# Post-deployment setup script

ENVIRONMENT=${1:-development}
AWS_REGION=${2:-us-east-1}

echo "🔧 Post-deployment setup for environment: $ENVIRONMENT"
echo ""

# Get database endpoint
DB_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name "whatsapp-api-$ENVIRONMENT" \
  --region "$AWS_REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='DatabaseEndpoint'].OutputValue" \
  --output text)

echo "💾 Database Endpoint: $DB_ENDPOINT"

# Get App Runner service URL
SERVICE_URL=$(aws cloudformation describe-stacks \
  --stack-name "whatsapp-api-$ENVIRONMENT" \
  --region "$AWS_REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='AppRunnerServiceUrl'].OutputValue" \
  --output text)

echo "🌐 App Runner URL: $SERVICE_URL"

echo ""
echo "✅ Next Steps:"
echo "1. Create IAM database user (if not exists):"
echo "   Connect to PostgreSQL and run:"
echo "   CREATE USER app_user;"
echo "   GRANT rds_iam TO app_user;"
echo "   GRANT CONNECT ON DATABASE whatsapp_business_$ENVIRONMENT TO app_user;"
echo ""
echo "2. Test health endpoint:"
echo "   curl $SERVICE_URL/health"
echo ""
echo "3. Test monitoring dashboard:"
echo "   curl $SERVICE_URL/monitoring/dashboard"
echo ""
echo "4. Set up WhatsApp webhook:"
echo "   Webhook URL: $SERVICE_URL/webhook"
echo "   Verify Token: (use your VERIFY_TOKEN)"
echo ""
echo "5. Monitor logs:"
echo "   aws logs tail /aws/apprunner/whatsapp-api-$ENVIRONMENT --region $AWS_REGION --follow"