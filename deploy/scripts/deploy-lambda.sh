#!/bin/bash

# Unified Lambda Deployment Script
# Deploys both media-archival and message-archival Lambda functions via S3

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="development"
S3_BUCKET="whatsapp-data-development-205924461245"
BUILD_DIR="/tmp/lambda-build"

# Function to deploy a Lambda
deploy_lambda() {
    local LAMBDA_TYPE=$1  # media-archival, message-archival, or agent-expiration
    local FUNCTION_NAME="${ENVIRONMENT}-whatsapp-${LAMBDA_TYPE}"
    local SOURCE_DIR="deploy/lambda/${LAMBDA_TYPE}"
    
    # Determine handler file based on lambda type
    if [ "$LAMBDA_TYPE" == "agent-expiration" ]; then
        local HANDLER_FILE="lambda_function.py"
    else
        local HANDLER_FILE="handler.py"
    fi
    
    local BUILD_PATH="${BUILD_DIR}/${LAMBDA_TYPE}"
    local ZIP_FILE="${LAMBDA_TYPE}-lambda.zip"
    local S3_KEY="lambda-deployments/${ZIP_FILE}"

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Deploying ${LAMBDA_TYPE} Lambda Function${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Save original directory
    local ORIGINAL_DIR=$(pwd)

    # Clean and create build directory
    echo -e "${YELLOW}📦 Building Lambda package...${NC}"
    rm -rf "$BUILD_PATH"
    mkdir -p "$BUILD_PATH"
    cd "$BUILD_PATH"

    # Install dependencies
    echo -e "${YELLOW}📥 Installing Python dependencies...${NC}"
    
    # Copy requirements and install non-boto3 dependencies
    grep -v "^boto3" "$ORIGINAL_DIR/$SOURCE_DIR/requirements.txt" > requirements_temp.txt || true
    
    if [ -s requirements_temp.txt ]; then
        echo -e "${YELLOW}📦 Installing packages for Lambda (manylinux2014_x86_64)...${NC}"
        
        # Install packages targeting Lambda's platform
        # psycopg2-binary should work with the correct platform specification
        pip3 install -r requirements_temp.txt \
            --target . \
            --platform manylinux2014_x86_64 \
            --implementation cp \
            --python-version 3.9 \
            --only-binary=:all: \
            --upgrade \
            --no-compile 2>&1 | grep -v "Requirement already satisfied" || true
        
        # Clean up unnecessary files to reduce package size
        find . -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
    fi

    # Copy Lambda handler
    cp "$ORIGINAL_DIR/$SOURCE_DIR/$HANDLER_FILE" .

    # Create deployment package
    echo -e "${YELLOW}📦 Creating deployment package...${NC}"
    zip -r "$ZIP_FILE" . -q

    # Upload to S3
    echo -e "${YELLOW}☁️  Uploading to S3...${NC}"
    aws s3 cp "$ZIP_FILE" "s3://$S3_BUCKET/$S3_KEY"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to upload to S3${NC}"
        cd "$ORIGINAL_DIR"
        return 1
    fi

    # Check if Lambda function exists
    echo -e "${YELLOW}🔍 Checking if Lambda function exists...${NC}"
    aws lambda get-function --function-name "$FUNCTION_NAME" > /dev/null 2>&1
    LAMBDA_EXISTS=$?
    
    if [ $LAMBDA_EXISTS -ne 0 ]; then
        # Lambda doesn't exist, create it
        echo -e "${YELLOW}📝 Lambda function doesn't exist, creating it...${NC}"
        
        # Get IAM role ARN
        ROLE_NAME="${ENVIRONMENT}-whatsapp-lambda-archival-role"
        ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null)
        
        if [ -z "$ROLE_ARN" ]; then
            echo -e "${RED}❌ IAM role not found: $ROLE_NAME${NC}"
            echo -e "${YELLOW}Please create the IAM role first${NC}"
            cd "$ORIGINAL_DIR"
            return 1
        fi
        
        # Determine handler based on file name
        if [ "$HANDLER_FILE" == "lambda_function.py" ]; then
            HANDLER_NAME="lambda_function.lambda_handler"
        else
            HANDLER_NAME="handler.lambda_handler"
        fi
        
        # Create Lambda function
        aws lambda create-function \
            --function-name "$FUNCTION_NAME" \
            --runtime python3.9 \
            --role "$ROLE_ARN" \
            --handler "$HANDLER_NAME" \
            --s3-bucket "$S3_BUCKET" \
            --s3-key "$S3_KEY" \
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
            --description "WhatsApp ${LAMBDA_TYPE} function" \
            --no-cli-pager > /dev/null 2>&1
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to create Lambda function${NC}"
            cd "$ORIGINAL_DIR"
            return 1
        fi
        
        echo -e "${GREEN}✅ Lambda function created${NC}"
        echo -e "${YELLOW}⚠️  Note: DB_PASSWORD is empty, please set it manually${NC}"
    else
        # Lambda exists, update it
        echo -e "${YELLOW}🚀 Updating Lambda function from S3...${NC}"
        UPDATE_OUTPUT=$(aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --s3-bucket "$S3_BUCKET" \
            --s3-key "$S3_KEY" \
            --no-cli-pager 2>&1)
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to update Lambda function${NC}"
            echo "$UPDATE_OUTPUT"
            cd "$ORIGINAL_DIR"
            return 1
        fi
    fi

    # Wait for update to complete
    echo -e "${YELLOW}⏳ Waiting for Lambda update to complete...${NC}"
    aws lambda wait function-updated --function-name "$FUNCTION_NAME"
    
    echo -e "${GREEN}✅ ${LAMBDA_TYPE} Lambda deployed successfully!${NC}"
    echo ""

    # Test the function
    echo -e "${YELLOW}🧪 Testing Lambda function...${NC}"
    TEST_OUTPUT=$(aws lambda invoke \
        --function-name "$FUNCTION_NAME" \
        --invocation-type RequestResponse \
        --no-cli-pager \
        /dev/stdout 2>&1 | head -2)
    
    echo "$TEST_OUTPUT"
    echo ""
    echo -e "${GREEN}✅ ${LAMBDA_TYPE} deployment complete!${NC}"
    echo ""

    # Get function info
    FUNCTION_INFO=$(aws lambda get-function --function-name "$FUNCTION_NAME" --query 'Configuration.[CodeSize,LastModified]' --output text)
    CODE_SIZE=$(echo "$FUNCTION_INFO" | awk '{print $1}')
    LAST_MODIFIED=$(echo "$FUNCTION_INFO" | awk '{print $2}')
    CODE_SIZE_MB=$(echo "scale=2; $CODE_SIZE / 1024 / 1024" | bc)
    
    echo -e "${BLUE}📊 Function Stats:${NC}"
    echo -e "   Size: ${CODE_SIZE_MB} MB"
    echo -e "   Updated: ${LAST_MODIFIED}"
    echo ""
    
    # Return to original directory
    cd "$ORIGINAL_DIR"
}

# Main execution
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}                 ${GREEN}Lambda Deployment Script (S3 Upload)${NC}                       ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if specific lambda is requested
if [ "$1" == "media" ] || [ "$1" == "media-archival" ]; then
    deploy_lambda "media-archival"
elif [ "$1" == "message" ] || [ "$1" == "message-archival" ]; then
    deploy_lambda "message-archival"
elif [ "$1" == "agent" ] || [ "$1" == "agent-expiration" ]; then
    deploy_lambda "agent-expiration"
elif [ "$1" == "all" ] || [ -z "$1" ]; then
    # Deploy all three
    deploy_lambda "media-archival"
    echo ""
    deploy_lambda "message-archival"
    echo ""
    deploy_lambda "agent-expiration"
else
    echo -e "${RED}❌ Invalid argument. Use: media, message, agent, all, or no argument (deploys all)${NC}"
    exit 1
fi

# Cleanup
echo -e "${YELLOW}🧹 Cleaning up build files...${NC}"
rm -rf "$BUILD_DIR"

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}                   ${GREEN}🎉 All Deployments Complete! 🎉${NC}                           ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
