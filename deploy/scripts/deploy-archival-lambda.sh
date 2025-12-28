#!/bin/bash

set -e

echo "=========================================="
echo "Deploying Media Archival Lambda Function"
echo "=========================================="

# Configuration
FUNCTION_NAME="development-whatsapp-media-archival"
LAMBDA_DIR="deploy/lambda/media-archival"
BUILD_DIR="/tmp/lambda-media-archival-build"
ZIP_FILE="media-archival-lambda.zip"

# Clean up previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "Building Lambda package..."

# Copy Lambda code
cp "$LAMBDA_DIR/handler.py" "$BUILD_DIR/"
cp "$LAMBDA_DIR/requirements.txt" "$BUILD_DIR/"

# Install dependencies
echo "Installing Python dependencies..."
cd "$BUILD_DIR"

# Use a clean approach: Install everything with the right platform
# First remove psycopg2-binary from requirements temporarily and install others
grep -v "psycopg2-binary" requirements.txt > requirements_temp.txt || true

# Install non-psycopg2 dependencies normally
if [ -s requirements_temp.txt ]; then
  pip3 install -r requirements_temp.txt -t .
fi

# Install psycopg2-binary specifically for manylinux (Amazon Linux 2 compatible)
pip3 install psycopg2-binary==2.9.10 -t . \
  --platform manylinux2014_x86_64 \
  --only-binary=:all: \
  --python-version 39 \
  --implementation cp \
  --no-deps

rm -f requirements_temp.txt

# Create deployment package
echo "Creating deployment package..."
zip -r "$ZIP_FILE" . -x "*.pyc" -x "__pycache__/*" -x "*.dist-info/*"

# Get current Lambda configuration
echo "Updating Lambda function code..."

# Set AWS CLI to use longer timeout
export AWS_CLI_AUTO_PROMPT=off
export AWS_MAX_ATTEMPTS=3
export AWS_RETRY_MODE=adaptive

# Upload via S3 for larger packages (more reliable)
S3_BUCKET="whatsapp-data-development-205924461245"
S3_KEY="lambda-deployments/$ZIP_FILE"

echo "Uploading to S3..."
aws s3 cp "$ZIP_FILE" "s3://$S3_BUCKET/$S3_KEY"

echo "Updating Lambda function from S3..."
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --s3-bucket "$S3_BUCKET" \
    --s3-key "$S3_KEY" \
    --no-cli-pager

echo "Waiting for Lambda update to complete..."
aws lambda wait function-updated --function-name "$FUNCTION_NAME"

echo "✅ Lambda function deployed successfully!"

# Test the function
echo ""
echo "Testing Lambda function..."
aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --payload '{}' \
    --cli-binary-format raw-in-base64-out \
    /tmp/lambda-response.json

echo ""
echo "Lambda response:"
cat /tmp/lambda-response.json
echo ""

# Clean up
rm -rf "$BUILD_DIR"

echo "✅ Deployment complete!"
