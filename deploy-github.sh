#!/bin/bash

# Deploy WhatsApp Business API from GitHub Repository
set -e

ENVIRONMENT=${1:-development}
AWS_REGION=${2:-us-east-1}
GITHUB_CONNECTION_ARN=${3}

if [ -z "$GITHUB_CONNECTION_ARN" ]; then
    echo "❌ Error: GitHub Connection ARN is required!"
    echo ""
    echo "Usage: $0 <environment> <aws-region> <github-connection-arn>"
    echo ""
    echo "To create a GitHub connection:"
    echo "1. Go to AWS App Runner Console"
    echo "2. Navigate to 'Connections'"
    echo "3. Create a new GitHub connection"
    echo "4. Copy the ARN and use it here"
    echo ""
    echo "Example:"
    echo "$0 development us-east-1 arn:aws:apprunner:us-east-1:123456789:connection/my-github-connection/abc123"
    exit 1
fi

echo "🚀 Deploying WhatsApp Business API from GitHub to $ENVIRONMENT"
echo "📍 Region: $AWS_REGION"
echo "🔗 GitHub Connection: $GITHUB_CONNECTION_ARN"

# Validate GitHub connection exists
echo "🔍 Validating GitHub connection..."
aws apprunner describe-connection \
    --connection-arn "$GITHUB_CONNECTION_ARN" \
    --region "$AWS_REGION" > /dev/null

if [ $? -ne 0 ]; then
    echo "❌ Error: Invalid GitHub Connection ARN or connection not found"
    exit 1
fi

echo "✅ GitHub connection validated"

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
    echo "2. Set up your WhatsApp webhook URL using the App Runner service URL above"
    echo "3. Run the database setup script: ./scripts/setup-iam-db-user.sh $ENVIRONMENT"
    echo "4. Monitor deployment in AWS App Runner Console"
else
    echo "❌ Deployment failed!"
    exit 1
fi