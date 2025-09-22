#!/bin/bash

# Deploy WhatsApp Business API from GitHub Repository
set -e

ENVIRONMENT=${1:-development}
AWS_REGION=${2:-us-east-1}
GITHUB_CONNECTION_ARN=${3}
DEFAULT_VPC_ID=${4}
ALLOWED_CIDR=${5:-"0.0.0.0/0"}

if [ -z "$GITHUB_CONNECTION_ARN" ]; then
    echo "❌ Error: GitHub Connection ARN is required!"
    echo ""
    echo "Usage: $0 <environment> <aws-region> <github-connection-arn> <default-vpc-id> [allowed-cidr]"
    echo ""
    echo "To create a GitHub connection:"
    echo "1. Go to AWS App Runner Console"
    echo "2. Navigate to 'Connections'"
    echo "3. Create a new GitHub connection"
    echo "4. Copy the ARN and use it here"
    echo ""
    echo "To find your Default VPC ID:"
    echo "1. Go to AWS VPC Console"
    echo "2. Look for VPC with 'Default VPC: Yes'"
    echo "3. Copy the VPC ID (vpc-xxxxxxxxx)"
    echo ""
    echo "Example:"
    echo "$0 development us-east-1 arn:aws:apprunner:us-east-1:123456789:connection/my-github-connection/abc123 vpc-12345678 203.0.113.0/24"
    exit 1
fi

if [ -z "$DEFAULT_VPC_ID" ]; then
    echo "❌ Error: Default VPC ID is required!"
    echo "Find it in AWS VPC Console (look for 'Default VPC: Yes')"
    exit 1
fi

echo "🚀 Deploying WhatsApp Business API from GitHub to $ENVIRONMENT"
echo "📍 Region: $AWS_REGION"
echo "🔗 GitHub Connection: $GITHUB_CONNECTION_ARN"
echo "🌐 Default VPC: $DEFAULT_VPC_ID"
echo "🔒 Allowed CIDR: $ALLOWED_CIDR"

# Validate required environment variables
if [ -z "$WHATSAPP_TOKEN" ] || [ -z "$VERIFY_TOKEN" ]; then
    echo "❌ Error: Required environment variables not set!"
    echo "Please set: WHATSAPP_TOKEN and VERIFY_TOKEN"
    echo ""
    echo "Example:"
    echo "export WHATSAPP_TOKEN='your_token_here'"
    echo "export VERIFY_TOKEN='your_verify_token_here'"
    echo "$0 $ENVIRONMENT $AWS_REGION $GITHUB_CONNECTION_ARN $DEFAULT_VPC_ID $ALLOWED_CIDR"
    exit 1
fi

# Validate GitHub connection exists
echo "🔍 Validating GitHub connection..."
aws apprunner list-connections \
    --region "$AWS_REGION" \
    --query "ConnectionSummaryList[?ConnectionArn=='$GITHUB_CONNECTION_ARN'].ConnectionArn" \
    --output text > /dev/null

if [ $? -ne 0 ]; then
    echo "❌ Error: Cannot validate GitHub Connection or AWS CLI error"
    echo "⚠️  Proceeding anyway - CloudFormation will validate the connection"
else
    echo "✅ GitHub connection validated"
fi

# Deploy CloudFormation stack
echo "☁️  Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file deploy/aws/cloudformation/infrastructure.yaml \
    --stack-name "whatsapp-api-$ENVIRONMENT" \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        GitHubConnectionArn="$GITHUB_CONNECTION_ARN" \
        GitHubRepositoryUrl="https://github.com/therealabhishekc/goblin" \
        GitHubBranch="main" \
        DefaultVPCId="$DEFAULT_VPC_ID" \
        AllowedCIDR="$ALLOWED_CIDR" \
        WhatsAppToken="$WHATSAPP_TOKEN" \
        VerifyToken="$VERIFY_TOKEN" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$AWS_REGION"

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    
    # Get outputs
    echo ""
    echo "📋 Deployment Information:"
    aws cloudformation describe-stacks \
        --stack-name "whatsapp-api-$ENVIRONMENT" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`AppRunnerServiceUrl`].OutputValue' \
        --output text
    
    echo ""
    echo "🎯 Next Steps:"
    echo "1. The App Runner service will automatically build and deploy from your GitHub repo"
    echo "2. Wait for deployment to complete (check AWS App Runner Console)"
    echo "3. Create the IAM database user:"
    echo "   ./scripts/create-iam-db-user.sh $ENVIRONMENT"
    echo "4. Set up your WhatsApp webhook URL using the App Runner service URL above"
    echo "5. Test the health endpoint: <service-url>/health"
    echo "6. Monitor logs in CloudWatch: /aws/apprunner/whatsapp-api-$ENVIRONMENT"
else
    echo "❌ Deployment failed!"
    exit 1
fi