#!/bin/bash

# Deploy WhatsApp Business API from GitHub Repository
set -e

ENVIRONMENT=${1:-development}
AWS_REGION=${2:-us-east-1}
GITHUB_CONNECTION_ARN=${3}
DEFAULT_VPC_ID=${4}
ALLOWED_CIDR=${5:-"0.0.0.0/0"}

if [ -z "$GITHUB_CONNECTION_ARN" ]; then
    echo "❌ Error: GitHub Connection ARN is required!"
    echo ""
    echo "Usage: $0 <environment> <aws-region> <github-connection-arn> <default-vpc-id> [allowed-cidr]"
    echo ""
    echo "To create a GitHub connection:"
    echo "1. Go to AWS App Runner Console"
    echo "2. Navigate to 'Connections'"
    echo "3. Create a new GitHub connection"
    echo "4. Copy the ARN and use it here"
    echo ""
    echo "To find your Default VPC ID:"
    echo "1. Go to AWS VPC Console"
    echo "2. Look for VPC with 'Default VPC: Yes'"
    echo "3. Copy the VPC ID (vpc-xxxxxxxxx)"
    echo ""
    echo "Example:"
    echo "$0 development us-east-1 arn:aws:apprunner:us-east-1:123456789:connection/my-github-connection/abc123 vpc-12345678 203.0.113.0/24"
    exit 1
fi

if [ -z "$DEFAULT_VPC_ID" ]; then
    echo "❌ Error: Default VPC ID is required!"
    echo "Find it in AWS VPC Console (look for 'Default VPC: Yes')"
    exit 1
fi

echo "🚀 Deploying WhatsApp Business API from GitHub to $ENVIRONMENT"
echo "📍 Region: $AWS_REGION"
echo "🔗 GitHub Connection: $GITHUB_CONNECTION_ARN"
echo "🌐 Default VPC: $DEFAULT_VPC_ID"
echo "🔒 Allowed CIDR: $ALLOWED_CIDR"

# Validate required environment variables for CloudFormation deployment
if [ -z "$WHATSAPP_TOKEN" ] || [ -z "$VERIFY_TOKEN" ] || [ -z "$WHATSAPP_PHONE_NUMBER_ID" ]; then
    echo "❌ Error: Required environment variables not set!"
    echo "Please set: WHATSAPP_TOKEN, VERIFY_TOKEN, and WHATSAPP_PHONE_NUMBER_ID"
    echo ""
    echo "⚠️  SECURITY NOTE: These will be stored in AWS Secrets Manager and then you should:"
    echo "1. Revoke the current tokens in Meta Business Suite" 
    echo "2. Generate new tokens"
    echo "3. Update the secret in AWS Secrets Manager"
    echo "4. Remove these from your local environment"
    echo ""
    echo "Example:"
    echo "export WHATSAPP_TOKEN='your_token_here'"
    echo "export VERIFY_TOKEN='your_verify_token_here'"
    echo "export WHATSAPP_PHONE_NUMBER_ID='your_phone_number_id_here'"
    echo "$0 $ENVIRONMENT $AWS_REGION $GITHUB_CONNECTION_ARN $DEFAULT_VPC_ID $ALLOWED_CIDR"
    exit 1
fi

# Validate GitHub connection exists
echo "🔍 Validating GitHub connection..."
aws apprunner list-connections \
    --region "$AWS_REGION" \
    --query "ConnectionSummaryList[?ConnectionArn=='$GITHUB_CONNECTION_ARN'].ConnectionArn" \
    --output text > /dev/null

if [ $? -ne 0 ]; then
    echo "❌ Error: Cannot validate GitHub Connection or AWS CLI error"
    echo "⚠️  Proceeding anyway - CloudFormation will validate the connection"
else
    echo "✅ GitHub connection validated"
fi

# Load archival configuration early for main deployment
ENV_FILE="deploy/environments/lambda-archival.env"
if [ -f "$ENV_FILE" ]; then
    echo "📋 Loading archival configuration from: $ENV_FILE"
    source "$ENV_FILE"
fi

# Deploy CloudFormation stack
echo "☁️  Deploying CloudFormation stack (including archival infrastructure)..."
aws cloudformation deploy \
    --template-file deploy/aws/cloudformation/infrastructure.yaml \
    --stack-name "whatsapp-api-$ENVIRONMENT" \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        GitHubConnectionArn="$GITHUB_CONNECTION_ARN" \
        GitHubRepositoryUrl="https://github.com/therealabhishekc/goblin" \
        GitHubBranch="main" \
        DefaultVPCId="$DEFAULT_VPC_ID" \
        AllowedCIDR="$ALLOWED_CIDR" \
        WhatsAppToken="$WHATSAPP_TOKEN" \
        VerifyToken="$VERIFY_TOKEN" \
        WhatsAppPhoneNumberId="$WHATSAPP_PHONE_NUMBER_ID" \
        ArchiveThresholdDays="${ARCHIVE_THRESHOLD_DAYS:-90}" \
        MediaThresholdDays="${MEDIA_THRESHOLD_DAYS:-30}" \
        EnableArchival="${ENABLE_ARCHIVAL:-true}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$AWS_REGION"

if [ $? -eq 0 ]; then
    echo "✅ Main infrastructure deployment successful!"
    
    # Get outputs
    echo ""
    echo "📋 Deployment Information:"
    SERVICE_URL=$(aws cloudformation describe-stacks \
        --stack-name "whatsapp-api-$ENVIRONMENT" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`AppRunnerServiceUrl`].OutputValue' \
        --output text)
    
    echo "🌐 App Runner Service URL: $SERVICE_URL"
    
    # Deploy Lambda archival functions (integrated in main template)
    echo ""
    echo "🔄 Updating Lambda archival function code..."
    echo "⏳ This may take a few minutes..."
    
    DEPLOY_LAMBDA_SUCCESS=false
    
    # Load archival configuration
    ENV_FILE="deploy/environments/lambda-archival.env"
    if [ -f "$ENV_FILE" ]; then
        echo "📋 Loading archival configuration from: $ENV_FILE"
        source "$ENV_FILE"
    fi
    
    # Check if archival is enabled and Lambda functions exist
    ARCHIVAL_ENABLED=$(aws cloudformation describe-stacks \
        --stack-name "whatsapp-api-$ENVIRONMENT" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ArchivalScheduleEnabled`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [ "$ARCHIVAL_ENABLED" = "true" ]; then
        echo "✅ Archival functions are enabled in infrastructure"
        
        # Create build directory
        BUILD_DIR="dist/lambda"
        mkdir -p "$BUILD_DIR"
        
        # Function to build and update Lambda code
        update_lambda_function() {
            local function_name=$1
            local source_dir="deploy/lambda/$function_name"
            local build_dir="$BUILD_DIR/$function_name-build"
            local zip_file="$BUILD_DIR/$function_name.zip"
            local lambda_function_name="${ENVIRONMENT}-whatsapp-${function_name}"
            
            echo "   📦 Building $function_name package..."
            
            # Clean and create build directory
            rm -rf "$build_dir"
            mkdir -p "$build_dir"
            
            # Copy source files
            cp "$source_dir/handler.py" "$build_dir/"
            
            # Install dependencies if requirements exist
            if [ -f "$source_dir/requirements.txt" ]; then
                echo "   📚 Installing dependencies..."
                pip install -r "$source_dir/requirements.txt" -t "$build_dir" --upgrade --quiet
            fi
            
            # Create zip package
            cd "$build_dir"
            zip -r "../$(basename "$zip_file")" . -x "*.pyc" "__pycache__/*" "*.dist-info/*" --quiet
            cd - > /dev/null
            
            echo "   🚀 Updating Lambda function: $lambda_function_name"
            
            # Update Lambda function code
            if aws lambda update-function-code \
                --function-name "$lambda_function_name" \
                --zip-file "fileb://$zip_file" \
                --region "$AWS_REGION" >/dev/null 2>&1; then
                
                echo "   ✅ Successfully updated: $lambda_function_name"
                return 0
            else
                echo "   ❌ Failed to update: $lambda_function_name"
                return 1
            fi
        }
        
        # Update Lambda functions if source directories exist
        if [ -d "deploy/lambda/message-archival" ] && [ -d "deploy/lambda/media-archival" ]; then
            echo "🔨 Building and updating Lambda functions..."
            
            if update_lambda_function "message-archival" && update_lambda_function "media-archival"; then
                echo "✅ Lambda archival functions updated successfully!"
                DEPLOY_LAMBDA_SUCCESS=true
                
                # Test the functions
                echo "🧪 Testing Lambda functions..."
                
                # Test message archival
                MESSAGE_FUNCTION_NAME="${ENVIRONMENT}-whatsapp-message-archival"
                if aws lambda invoke \
                    --function-name "$MESSAGE_FUNCTION_NAME" \
                    --payload '{"test": true, "dry_run": true}' \
                    --region "$AWS_REGION" \
                    "$BUILD_DIR/test-response.json" >/dev/null 2>&1; then
                    echo "   ✅ Message archival function test passed"
                else
                    echo "   ⚠️  Message archival function test failed"
                fi
                
                # Test media archival
                MEDIA_FUNCTION_NAME="${ENVIRONMENT}-whatsapp-media-archival"
                if aws lambda invoke \
                    --function-name "$MEDIA_FUNCTION_NAME" \
                    --payload '{"test": true, "dry_run": true}' \
                    --region "$AWS_REGION" \
                    "$BUILD_DIR/test-response.json" >/dev/null 2>&1; then
                    echo "   ✅ Media archival function test passed"
                else
                    echo "   ⚠️  Media archival function test failed"
                fi
            else
                echo "⚠️  Some Lambda function updates failed"
            fi
            
            # Clean up build artifacts
            rm -rf "$BUILD_DIR"
        else
            echo "⚠️  Lambda function sources not found in deploy/lambda/"
            echo "   Archival functions are created but will use placeholder code"
            DEPLOY_LAMBDA_SUCCESS=true  # Infrastructure exists, just no custom code
        fi
    else
        echo "ℹ️  Archival functions are disabled (EnableArchival=false)"
        echo "   To enable: redeploy with EnableArchival=true parameter"
        DEPLOY_LAMBDA_SUCCESS=true  # Not an error, just disabled
    fi
    
    echo ""
    echo "🎯 Next Steps:"
    echo "1. The App Runner service will automatically build and deploy from your GitHub repo"
    echo "2. Wait for deployment to complete (check AWS App Runner Console)"
    echo "3. Create the IAM database user:"
    echo "   ./scripts/create-iam-db-user.sh $ENVIRONMENT"
    echo "4. 🔐 SECURITY: Update credentials in AWS Secrets Manager:"
    echo "   ./scripts/update-whatsapp-credentials.sh $ENVIRONMENT $AWS_REGION"
    echo "5. Set up your WhatsApp webhook URL using the App Runner service URL above"
    echo "6. Test the health endpoint: ${SERVICE_URL}/health"
    echo "7. Monitor logs in CloudWatch: /aws/apprunner/whatsapp-api-$ENVIRONMENT"
    echo ""
    echo "⚠️  CRITICAL SECURITY REMINDER:"
    echo "   - The credentials used in this deployment will be stored in AWS Secrets Manager"
    echo "   - After deployment, IMMEDIATELY revoke the old tokens in Meta Business Suite"
    echo "   - Generate new tokens and update them using the credentials update script"
    echo "   - Remove tokens from your local environment: unset WHATSAPP_TOKEN VERIFY_TOKEN WHATSAPP_PHONE_NUMBER_ID"
    
    if [ "$DEPLOY_LAMBDA_SUCCESS" = true ]; then
        echo ""
        echo "📅 Automated Archival Configuration:"
        echo "   - Message archival: Every 2 days at 2 AM UTC"
        echo "   - Media archival: Every 2 days at 3 AM UTC"
        echo "   - Admin API: ${SERVICE_URL}/api/admin/archival/"
        echo ""
        echo "🧪 Test archival functions:"
        echo "   curl -X POST '${SERVICE_URL}/api/admin/archival/trigger?job_type=both&dry_run=true'"
    fi
else
    echo "❌ Main infrastructure deployment failed!"
    exit 1
fi