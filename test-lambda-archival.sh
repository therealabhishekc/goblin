#!/bin/bash

set -e

# Test script for Lambda archival functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="${ENVIRONMENT:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"

echo "🧪 Testing Lambda archival functions for environment: $ENVIRONMENT"
echo "ℹ️  Note: Lambda functions are now deployed as part of deploy-github.sh"

# Get stack outputs
MAIN_STACK_NAME="whatsapp-api-${ENVIRONMENT}"
ARCHIVAL_STACK_NAME="whatsapp-archival-lambda-${ENVIRONMENT}"

# Check if archival functions are enabled in main stack
ARCHIVAL_ENABLED=$(aws cloudformation describe-stacks \
    --stack-name "$MAIN_STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ArchivalScheduleEnabled`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ "$ARCHIVAL_ENABLED" != "true" ]; then
    echo "❌ Archival functions are not enabled in the main stack"
    echo "   Deploy with EnableArchival=true or check deployment configuration"
    exit 1
fi

echo "✅ Archival functions are enabled in infrastructure"

# Get service URL for admin API testing
SERVICE_URL=$(aws cloudformation describe-stacks \
    --stack-name "$MAIN_STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`AppRunnerServiceUrl`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -z "$SERVICE_URL" ]; then
    echo "⚠️  Warning: Could not get service URL from main stack"
    echo "   Admin API tests will be skipped"
else
    echo "🌐 Service URL: $SERVICE_URL"
fi

# Test 1: Validate Lambda functions exist
echo ""
echo "📋 Test 1: Validating Lambda functions exist..."

MESSAGE_FUNCTION_NAME="${ENVIRONMENT}-whatsapp-message-archival"
MEDIA_FUNCTION_NAME="${ENVIRONMENT}-whatsapp-media-archival"

if aws lambda get-function --function-name "$MESSAGE_FUNCTION_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "✅ Message archival function exists: $MESSAGE_FUNCTION_NAME"
else
    echo "❌ Message archival function not found: $MESSAGE_FUNCTION_NAME"
    exit 1
fi

if aws lambda get-function --function-name "$MEDIA_FUNCTION_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "✅ Media archival function exists: $MEDIA_FUNCTION_NAME"
else
    echo "❌ Media archival function not found: $MEDIA_FUNCTION_NAME"
    exit 1
fi

# Test 2: Dry run invocations
echo ""
echo "📋 Test 2: Testing dry run invocations..."

echo "   Testing message archival (dry run)..."
MESSAGE_RESPONSE=$(aws lambda invoke \
    --function-name "$MESSAGE_FUNCTION_NAME" \
    --payload '{"test": true, "dry_run": true}' \
    --region "$AWS_REGION" \
    /tmp/message-test-response.json \
    --query 'StatusCode' \
    --output text 2>/dev/null || echo "500")

if [ "$MESSAGE_RESPONSE" = "200" ]; then
    echo "✅ Message archival dry run successful"
    if [ -f "/tmp/message-test-response.json" ]; then
        RESPONSE_BODY=$(cat /tmp/message-test-response.json)
        if echo "$RESPONSE_BODY" | grep -q "dry_run.*true"; then
            echo "   ✅ Dry run flag acknowledged"
        fi
    fi
else
    echo "❌ Message archival dry run failed (Status: $MESSAGE_RESPONSE)"
    if [ -f "/tmp/message-test-response.json" ]; then
        echo "   Response: $(cat /tmp/message-test-response.json)"
    fi
fi

echo "   Testing media archival (dry run)..."
MEDIA_RESPONSE=$(aws lambda invoke \
    --function-name "$MEDIA_FUNCTION_NAME" \
    --payload '{"test": true, "dry_run": true}' \
    --region "$AWS_REGION" \
    /tmp/media-test-response.json \
    --query 'StatusCode' \
    --output text 2>/dev/null || echo "500")

if [ "$MEDIA_RESPONSE" = "200" ]; then
    echo "✅ Media archival dry run successful"
    if [ -f "/tmp/media-test-response.json" ]; then
        RESPONSE_BODY=$(cat /tmp/media-test-response.json)
        if echo "$RESPONSE_BODY" | grep -q "dry_run.*true"; then
            echo "   ✅ Dry run flag acknowledged"
        fi
    fi
else
    echo "❌ Media archival dry run failed (Status: $MEDIA_RESPONSE)"
    if [ -f "/tmp/media-test-response.json" ]; then
        echo "   Response: $(cat /tmp/media-test-response.json)"
    fi
fi

# Test 3: EventBridge rules
echo ""
echo "📋 Test 3: Validating EventBridge scheduling..."

MESSAGE_RULE_NAME="${ENVIRONMENT}-whatsapp-message-archival-schedule"
MEDIA_RULE_NAME="${ENVIRONMENT}-whatsapp-media-archival-schedule"

if aws events describe-rule --name "$MESSAGE_RULE_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
    RULE_STATE=$(aws events describe-rule --name "$MESSAGE_RULE_NAME" --region "$AWS_REGION" --query 'State' --output text)
    echo "✅ Message archival schedule rule exists (State: $RULE_STATE)"
else
    echo "❌ Message archival schedule rule not found"
fi

if aws events describe-rule --name "$MEDIA_RULE_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
    RULE_STATE=$(aws events describe-rule --name "$MEDIA_RULE_NAME" --region "$AWS_REGION" --query 'State' --output text)
    echo "✅ Media archival schedule rule exists (State: $RULE_STATE)"
else
    echo "❌ Media archival schedule rule not found"
fi

# Test 4: Admin API (if service is available)
if [ -n "$SERVICE_URL" ]; then
    echo ""
    echo "📋 Test 4: Testing Admin API endpoints..."
    
    # Wait for service to be ready
    echo "   Waiting for service to be ready..."
    RETRY_COUNT=0
    MAX_RETRIES=10
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -s -f "${SERVICE_URL}/health" >/dev/null 2>&1; then
            echo "   ✅ Service is ready"
            break
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "   ⏳ Waiting... (attempt $RETRY_COUNT/$MAX_RETRIES)"
        sleep 10
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "   ⚠️  Service not ready after $MAX_RETRIES attempts - skipping API tests"
    else
        # Test admin endpoints
        echo "   Testing archival status endpoint..."
        if curl -s -f "${SERVICE_URL}/api/admin/archival/status" >/dev/null 2>&1; then
            echo "   ✅ Admin status endpoint accessible"
        else
            echo "   ❌ Admin status endpoint failed"
        fi
        
        echo "   Testing dry run trigger..."
        if curl -s -f -X POST "${SERVICE_URL}/api/admin/archival/trigger?job_type=both&dry_run=true" >/dev/null 2>&1; then
            echo "   ✅ Admin trigger endpoint accessible"
        else
            echo "   ❌ Admin trigger endpoint failed"
        fi
    fi
fi

# Test 5: CloudWatch logs
echo ""
echo "📋 Test 5: Validating CloudWatch log groups..."

MESSAGE_LOG_GROUP="/aws/lambda/${MESSAGE_FUNCTION_NAME}"
MEDIA_LOG_GROUP="/aws/lambda/${MEDIA_FUNCTION_NAME}"

if aws logs describe-log-groups --log-group-name-prefix "$MESSAGE_LOG_GROUP" --region "$AWS_REGION" --query 'logGroups[0].logGroupName' --output text | grep -q "$MESSAGE_LOG_GROUP"; then
    echo "✅ Message archival log group exists"
else
    echo "❌ Message archival log group not found"
fi

if aws logs describe-log-groups --log-group-name-prefix "$MEDIA_LOG_GROUP" --region "$AWS_REGION" --query 'logGroups[0].logGroupName' --output text | grep -q "$MEDIA_LOG_GROUP"; then
    echo "✅ Media archival log group exists"
else
    echo "❌ Media archival log group not found"
fi

# Cleanup test files
rm -f /tmp/message-test-response.json /tmp/media-test-response.json

echo ""
echo "🎉 Lambda archival testing completed!"
echo ""
echo "📊 Monitoring Commands:"
echo "   View logs: aws logs tail $MESSAGE_LOG_GROUP --region $AWS_REGION --follow"
echo "   Check metrics: aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Invocations --dimensions Name=FunctionName,Value=$MESSAGE_FUNCTION_NAME --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 300 --statistics Sum --region $AWS_REGION"
echo ""
if [ -n "$SERVICE_URL" ]; then
    echo "🔧 Admin Commands:"
    echo "   Manual trigger: curl -X POST '${SERVICE_URL}/api/admin/archival/trigger?job_type=both&dry_run=true'"
    echo "   Check status: curl '${SERVICE_URL}/api/admin/archival/status'"
    echo "   View metrics: curl '${SERVICE_URL}/api/admin/archival/metrics'"
fi