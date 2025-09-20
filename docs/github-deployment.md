# GitHub Deployment Setup Guide

## 🔗 Step 1: Create GitHub Connection (One-time setup)

1. **Go to AWS App Runner Console**
   - Navigate to https://console.aws.amazon.com/apprunner/
   - Choose your region (e.g., us-east-1)

2. **Create Connection**
   - Click "Connections" in the left sidebar
   - Click "Add connection"
   - Select "GitHub" as provider
   - Give it a name: `whatsapp-github-connection`
   - Click "Next"

3. **Authorize GitHub**
   - You'll be redirected to GitHub
   - Install the AWS Connector app on your account
   - Choose to install on all repositories or select specific ones
   - Return to AWS Console

4. **Copy Connection ARN**
   - Once created, click on the connection name
   - Copy the ARN (looks like: `arn:aws:apprunner:us-east-1:123456789:connection/whatsapp-github-connection/abc123`)

## 🚀 Step 2: Deploy Your Application

```bash
# Set your environment variables
export WHATSAPP_TOKEN="your_whatsapp_token"
export VERIFY_TOKEN="your_verify_token"

# Deploy to development
./deploy-github.sh development us-east-1 "arn:aws:apprunner:us-east-1:123456789:connection/whatsapp-github-connection/abc123"
```

## 🔄 Step 3: Automatic Deployments

After the initial deployment:
- Every `git push` to the `main` branch will trigger automatic deployment
- App Runner will pull the latest code, build it, and deploy automatically
- Monitor progress in the AWS App Runner Console

## 🎯 Benefits of GitHub Deployment

✅ **No Docker Required**: App Runner builds from source code directly
✅ **Automatic Deployments**: Push to trigger deployment
✅ **Source Control Integration**: Full GitHub integration
✅ **Build Logs**: View build progress in App Runner Console
✅ **Rollback Capability**: Easy rollback to previous deployments

## 📝 Configuration Files

Your repository needs these files for GitHub deployment:

- `apprunner.yaml` - App Runner build and run configuration ✅
- `backend/requirements.txt` - Python dependencies ✅
- `backend/app/main.py` - FastAPI application entry point ✅

## 🔧 Environment Variables

All environment variables are managed by CloudFormation:
- Database connection details
- WhatsApp API tokens
- AWS service configurations
- S3 bucket names

No need to manage environment variables manually!

## 🐛 Troubleshooting

If deployment fails:

1. **Check App Runner Logs**
   - Go to App Runner Console → Your service → Logs tab
   - Look for build or runtime errors

2. **Verify GitHub Connection**
   - Ensure the connection ARN is correct
   - Check that the repository URL is accessible

3. **Check apprunner.yaml**
   - Ensure the file is in your repository root
   - Verify build commands are correct

4. **Database Setup**
   - Remember to run `./scripts/setup-iam-db-user.sh` after deployment
   - This creates the IAM database user for your application