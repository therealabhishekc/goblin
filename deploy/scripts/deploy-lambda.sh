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
    local LAMBDA_TYPE=$1  # media-archival or message-archival
    local FUNCTION_NAME="${ENVIRONMENT}-whatsapp-${LAMBDA_TYPE}"
    local SOURCE_DIR="deploy/lambda/${LAMBDA_TYPE}"
    local BUILD_PATH="${BUILD_DIR}/${LAMBDA_TYPE}"
    local ZIP_FILE="${LAMBDA_TYPE}-lambda.zip"
    local S3_KEY="lambda-deployments/${ZIP_FILE}"

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Deploying ${LAMBDA_TYPE} Lambda Function${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Clean and create build directory
    echo -e "${YELLOW}📦 Building Lambda package...${NC}"
    rm -rf "$BUILD_PATH"
    mkdir -p "$BUILD_PATH"
    cd "$BUILD_PATH"

    # Install dependencies
    echo -e "${YELLOW}📥 Installing Python dependencies...${NC}"
    
    # Copy requirements and install non-boto3 dependencies
    grep -v "^boto3" "$OLDPWD/$SOURCE_DIR/requirements.txt" > requirements_temp.txt || true
    
    if [ -s requirements_temp.txt ]; then
        pip3 install -r requirements_temp.txt -t . --platform manylinux2014_x86_64 --python-version 3.9 --only-binary=:all: --upgrade
    fi

    # Copy Lambda handler
    cp "$OLDPWD/$SOURCE_DIR/handler.py" .

    # Create deployment package
    echo -e "${YELLOW}📦 Creating deployment package...${NC}"
    zip -r "$ZIP_FILE" . -q

    # Upload to S3
    echo -e "${YELLOW}☁️  Uploading to S3...${NC}"
    aws s3 cp "$ZIP_FILE" "s3://$S3_BUCKET/$S3_KEY"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to upload to S3${NC}"
        return 1
    fi

    # Update Lambda function
    echo -e "${YELLOW}🚀 Updating Lambda function from S3...${NC}"
    UPDATE_OUTPUT=$(aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --s3-bucket "$S3_BUCKET" \
        --s3-key "$S3_KEY" \
        --no-cli-pager 2>&1)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to update Lambda function${NC}"
        echo "$UPDATE_OUTPUT"
        return 1
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
elif [ "$1" == "both" ] || [ -z "$1" ]; then
    # Deploy both
    deploy_lambda "media-archival"
    echo ""
    deploy_lambda "message-archival"
else
    echo -e "${RED}❌ Invalid argument. Use: media, message, both, or no argument (deploys both)${NC}"
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
