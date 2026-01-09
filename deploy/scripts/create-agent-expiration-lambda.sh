#!/bin/bash

# Create Agent Expiration Lambda Function
# This script creates the Lambda function for agent session expiration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Creating Agent Expiration Lambda Function${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Configuration
ENVIRONMENT="development"
FUNCTION_NAME="${ENVIRONMENT}-whatsapp-agent-expiration"
ROLE_NAME="${ENVIRONMENT}-whatsapp-lambda-archival-role"
REGION="us-east-1"

# Get the Lambda IAM role ARN
echo -e "${YELLOW}📋 Getting IAM role ARN...${NC}"
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)

if [ -z "$ROLE_ARN" ]; then
    echo -e "${RED}❌ IAM role not found: $ROLE_NAME${NC}"
    echo -e "${YELLOW}Please create the role first or check the role name${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found IAM role: $ROLE_ARN${NC}"
echo ""

# Create a minimal Lambda package (we'll update it later with the deploy script)
echo -e "${YELLOW}📦 Creating initial Lambda package...${NC}"
BUILD_DIR="/tmp/agent-expiration-init"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

cat > "$BUILD_DIR/lambda_function.py" << 'EOF'
def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Initial deployment - will be updated'
    }
EOF

cd "$BUILD_DIR"
zip -q lambda.zip lambda_function.py

echo -e "${GREEN}✅ Package created${NC}"
echo ""

# Create the Lambda function
echo -e "${YELLOW}🚀 Creating Lambda function...${NC}"
aws lambda create-function \
    --function-name "$FUNCTION_NAME" \
    --runtime python3.9 \
    --role "$ROLE_ARN" \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda.zip \
    --timeout 300 \
    --memory-size 512 \
    --environment Variables='{
        DB_HOST=whatsapp-postgres-development.cibi66cyqd2r.us-east-1.rds.amazonaws.com,
        DB_PORT=5432,
        DB_NAME=whatsapp_business_development,
        DB_USER=postgres,
        DB_PASSWORD=,
        WHATSAPP_API_URL=https://byqpifhtjq.us-east-1.awsapprunner.com
    }' \
    --description "Expires agent chat sessions after 22 hours" \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Lambda function created successfully!${NC}"
    echo ""
else
    echo -e "${RED}❌ Failed to create Lambda function${NC}"
    exit 1
fi

# Cleanup
rm -rf "$BUILD_DIR"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Agent Expiration Lambda Created!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Set the DB_PASSWORD environment variable${NC}"
echo -e "${YELLOW}Run: aws lambda update-function-configuration --function-name $FUNCTION_NAME --environment 'Variables={DB_HOST=whatsapp-postgres-development.cibi66cyqd2r.us-east-1.rds.amazonaws.com,DB_PORT=5432,DB_NAME=whatsapp_business_development,DB_USER=postgres,DB_PASSWORD=YOUR_PASSWORD,WHATSAPP_API_URL=https://byqpifhtjq.us-east-1.awsapprunner.com}'${NC}"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo -e "   1. Set DB_PASSWORD environment variable (see above)"
echo -e "   2. Deploy the actual code: ./deploy/scripts/deploy-lambda.sh agent"
echo -e "   3. Create EventBridge rule to trigger every 5 minutes"
echo ""
