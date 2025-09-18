#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ROLE_NAME="AppRunnerDynamoDBRole"
POLICY_NAME="AppRunnerDynamoDBPolicy"
TABLE_NAME="ttest"
AWS_REGION="us-east-1"

echo -e "${YELLOW}Setting up AWS resources for App Runner + DynamoDB integration...${NC}"

# 1. Create DynamoDB table
echo -e "\n${YELLOW}1. Creating DynamoDB table: ${TABLE_NAME}${NC}"
aws dynamodb create-table \
    --table-name ${TABLE_NAME} \
    --attribute-definitions \
        AttributeName=message_id,AttributeType=S \
    --key-schema \
        AttributeName=message_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ${AWS_REGION} \
    --time-to-live-specification \
        AttributeName=ttl,Enabled=true \
    2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ DynamoDB table created successfully${NC}"
else
    echo -e "${YELLOW}⚠ Table might already exist, checking...${NC}"
    aws dynamodb describe-table --table-name ${TABLE_NAME} --region ${AWS_REGION} >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ DynamoDB table already exists${NC}"
    else
        echo -e "${RED}✗ Failed to create or find DynamoDB table${NC}"
        exit 1
    fi
fi

# 2. Create IAM policy
echo -e "\n${YELLOW}2. Creating IAM policy: ${POLICY_NAME}${NC}"
POLICY_ARN=$(aws iam create-policy \
    --policy-name ${POLICY_NAME} \
    --policy-document file://aws/dynamodb-policy.json \
    --query 'Policy.Arn' \
    --output text 2>/dev/null)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ IAM policy created successfully${NC}"
    echo -e "Policy ARN: ${POLICY_ARN}"
else
    echo -e "${YELLOW}⚠ Policy might already exist, getting ARN...${NC}"
    POLICY_ARN=$(aws iam list-policies \
        --query "Policies[?PolicyName=='${POLICY_NAME}'].Arn" \
        --output text)
    if [ -n "$POLICY_ARN" ]; then
        echo -e "${GREEN}✓ Found existing policy${NC}"
        echo -e "Policy ARN: ${POLICY_ARN}"
    else
        echo -e "${RED}✗ Failed to create or find IAM policy${NC}"
        exit 1
    fi
fi

# 3. Create IAM role
echo -e "\n${YELLOW}3. Creating IAM role: ${ROLE_NAME}${NC}"
aws iam create-role \
    --role-name ${ROLE_NAME} \
    --assume-role-policy-document file://aws/trust-policy.json \
    >/dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ IAM role created successfully${NC}"
else
    echo -e "${YELLOW}⚠ Role might already exist${NC}"
    aws iam get-role --role-name ${ROLE_NAME} >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ IAM role already exists${NC}"
    else
        echo -e "${RED}✗ Failed to create or find IAM role${NC}"
        exit 1
    fi
fi

# 4. Attach policy to role
echo -e "\n${YELLOW}4. Attaching policy to role${NC}"
aws iam attach-role-policy \
    --role-name ${ROLE_NAME} \
    --policy-arn ${POLICY_ARN}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Policy attached to role successfully${NC}"
else
    echo -e "${RED}✗ Failed to attach policy to role${NC}"
    exit 1
fi

# 5. Get role ARN
ROLE_ARN=$(aws iam get-role --role-name ${ROLE_NAME} --query 'Role.Arn' --output text)

echo -e "\n${GREEN}🎉 Setup completed successfully!${NC}"
echo -e "\n${YELLOW}Next steps for App Runner:${NC}"
echo -e "1. When creating your App Runner service, use this Instance Role ARN:"
echo -e "   ${GREEN}${ROLE_ARN}${NC}"
echo -e "\n2. Set these environment variables in your App Runner service:"
echo -e "   ${GREEN}DYNAMODB_TABLE_NAME=${TABLE_NAME}${NC}"
echo -e "   ${GREEN}AWS_REGION=${AWS_REGION}${NC}"
echo -e "\n3. Your application is already configured to use DynamoDB!"

# Optional: Enable TTL on the table (if not already enabled)
echo -e "\n${YELLOW}Enabling TTL on DynamoDB table...${NC}"
aws dynamodb update-time-to-live \
    --table-name ${TABLE_NAME} \
    --time-to-live-specification AttributeName=ttl,Enabled=true \
    --region ${AWS_REGION} \
    >/dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ TTL enabled on DynamoDB table${NC}"
else
    echo -e "${YELLOW}⚠ TTL might already be enabled${NC}"
fi

echo -e "\n${GREEN}All done! Your AWS resources are ready for App Runner + DynamoDB integration.${NC}"
