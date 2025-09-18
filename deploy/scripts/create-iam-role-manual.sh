#!/bin/bash

# Script to create IAM role using standalone policy files
# Alternative to CloudFormation inline policies

set -e

ROLE_NAME="AppRunnerWhatsAppRole-manual"
REGION="us-east-1"

echo "🔧 Creating IAM role using standalone policy files..."

# 1. Create the role with trust policy
aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document file://deploy/aws/iam/trust-policy.json \
    --description "App Runner role for WhatsApp Business API (manual setup)"

echo "✅ IAM role created: $ROLE_NAME"

# 2. Attach DynamoDB policy
aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name DynamoDBAccess \
    --policy-document file://deploy/aws/iam/dynamodb-policy.json

echo "✅ DynamoDB policy attached"

# 3. Attach RDS IAM policy  
aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name RDSIAMAccess \
    --policy-document file://deploy/aws/iam/rds-iam-policy.json

echo "✅ RDS IAM policy attached"

# 4. Get role ARN
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)

echo ""
echo "🎉 Setup completed!"
echo "Role ARN: $ROLE_ARN"
echo ""
echo "💡 Use this ARN in your App Runner service configuration"
