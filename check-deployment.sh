#!/bin/bash

# Check if templates API is deployed
echo "🔍 Checking if templates API is deployed..."
echo ""

BACKEND_URL="https://2hdfnnus3x.us-east-1.awsapprunner.com"
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS..."
    
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/templates")
    
    if [ "$RESPONSE" == "200" ]; then
        echo "✅ Templates API is live!"
        echo ""
        echo "Testing endpoint..."
        curl -s "$BACKEND_URL/api/templates" | python3 -m json.tool || echo "Response received"
        echo ""
        echo "🎉 Deployment successful! You can now use the frontend."
        exit 0
    elif [ "$RESPONSE" == "404" ]; then
        echo "   ⏳ Still deploying... (HTTP 404)"
    else
        echo "   ⏳ Status: HTTP $RESPONSE"
    fi
    
    if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
        sleep 20
    fi
done

echo ""
echo "⚠️  Deployment check timed out after $((MAX_ATTEMPTS * 20 / 60)) minutes"
echo "   The deployment might still be in progress."
echo "   You can check manually:"
echo "   curl $BACKEND_URL/api/templates"
exit 1
