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

# Install dependencies using Python 3.9 compatible binaries
# Use pip with target for Python 3.9 and manylinux platform
python3.9 -m pip install -r requirements.txt -t . --no-cache-dir 2>/dev/null || \
  pip3 install -r requirements.txt -t . --python-version 39 --platform manylinux2014_x86_64 --implementation cp --only-binary=:all: --no-cache-dir

# Create deployment package
echo "Creating deployment package..."
zip -r "$ZIP_FILE" . -x "*.pyc" -x "__pycache__/*" -x "*.dist-info/*"

# Get current Lambda configuration
echo "Updating Lambda function code..."
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file "fileb://$ZIP_FILE" \
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
