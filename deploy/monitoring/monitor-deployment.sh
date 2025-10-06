#!/bin/bash
# Monitor deployment status

ENVIRONMENT=${1:-development}
AWS_REGION=${2:-us-east-1}

echo "🔍 Monitoring deployment status for environment: $ENVIRONMENT"
echo ""

# Check CloudFormation stack status
echo "📋 CloudFormation Stack Status:"
aws cloudformation describe-stacks \
  --stack-name "whatsapp-api-$ENVIRONMENT" \
  --region "$AWS_REGION" \
  --query "Stacks[0].StackStatus" \
  --output text

echo ""

# Check App Runner service status
echo "🏃 App Runner Service Status:"
SERVICE_ARN=$(aws cloudformation describe-stacks \
  --stack-name "whatsapp-api-$ENVIRONMENT" \
  --region "$AWS_REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='AppRunnerServiceArn'].OutputValue" \
  --output text)

if [ -n "$SERVICE_ARN" ]; then
  aws apprunner describe-service \
    --service-arn "$SERVICE_ARN" \
    --region "$AWS_REGION" \
    --query "Service.Status" \
    --output text
  
  echo ""
  echo "📱 Service URL:"
  aws apprunner describe-service \
    --service-arn "$SERVICE_ARN" \
    --region "$AWS_REGION" \
    --query "Service.ServiceUrl" \
    --output text
else
  echo "Service not found or still creating..."
fi

echo ""
echo "📊 Recent CloudFormation Events:"
aws cloudformation describe-stack-events \
  --stack-name "whatsapp-api-$ENVIRONMENT" \
  --region "$AWS_REGION" \
  --query "StackEvents[0:5].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]" \
  --output table