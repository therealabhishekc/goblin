#!/bin/bash

# Build and Deploy WhatsApp Business API
set -e

ENVIRONMENT=${1:-dev}
AWS_REGION=${2:-us-east-1}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🚀 Building and deploying WhatsApp Business API to $ENVIRONMENT"

# Step 1: Create ECR repository if it doesn't exist
echo "📦 Setting up ECR repository..."
aws ecr describe-repositories --repository-names whatsapp-api --region $AWS_REGION || \
aws ecr create-repository --repository-name whatsapp-api --region $AWS_REGION

# Step 2: Build and push Docker image
echo "🐳 Building Docker image..."
docker build -t whatsapp-api .

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag and push image
docker tag whatsapp-api:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/whatsapp-api:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/whatsapp-api:latest

# Step 3: Deploy CloudFormation stack
echo "☁️  Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file deploy/aws/cloudformation/infrastructure.yaml \
    --stack-name whatsapp-api-$ENVIRONMENT \
    --parameter-overrides file://deploy/aws/parameters/$ENVIRONMENT.json \
    --capabilities CAPABILITY_IAM \
    --region $AWS_REGION

echo "✅ Deployment complete!"

# Get outputs
echo "📋 Stack outputs:"
aws cloudformation describe-stacks \
    --stack-name whatsapp-api-$ENVIRONMENT \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs'
