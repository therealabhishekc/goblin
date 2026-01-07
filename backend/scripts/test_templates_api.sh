#!/bin/bash

# Test script for Workflow Templates API
# Usage: ./test_templates_api.sh

BASE_URL="https://2hdfnnus3x.us-east-1.awsapprunner.com"
API_URL="${BASE_URL}/api/templates"

echo "🧪 Testing Workflow Templates API"
echo "=================================="
echo ""

# Test 1: List all templates
echo "1️⃣ Testing GET /api/templates/"
echo "---"
curl -s "${API_URL}/" | python3 -m json.tool || echo "❌ Failed"
echo ""
echo ""

# Test 2: List active templates only
echo "2️⃣ Testing GET /api/templates/?active_only=true"
echo "---"
curl -s "${API_URL}/?active_only=true" | python3 -m json.tool || echo "❌ Failed"
echo ""
echo ""

# Test 3: Get template by name (main_menu should exist from previous setup)
echo "3️⃣ Testing GET /api/templates/by-name/main_menu"
echo "---"
curl -s "${API_URL}/by-name/main_menu" | python3 -m json.tool || echo "❌ Template not found or API error"
echo ""
echo ""

# Test 4: Create a new test template
echo "4️⃣ Testing POST /api/templates/ (Create)"
echo "---"
TEMPLATE_JSON='{
  "template_name": "test_template_'"$(date +%s)"'",
  "template_type": "button",
  "trigger_keywords": ["test", "demo"],
  "menu_structure": {
    "initial": {
      "message": "This is a test template",
      "type": "button",
      "buttons": [
        {"id": "opt1", "title": "Option 1"},
        {"id": "opt2", "title": "Option 2"}
      ],
      "next_steps": {
        "opt1": "step1",
        "opt2": "step2"
      }
    }
  },
  "is_active": true
}'

RESPONSE=$(curl -s -X POST "${API_URL}/" \
  -H "Content-Type: application/json" \
  -d "${TEMPLATE_JSON}")

echo "$RESPONSE" | python3 -m json.tool

# Extract template ID for further tests
TEMPLATE_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -z "$TEMPLATE_ID" ]; then
    echo "❌ Failed to create template or extract ID"
    echo ""
else
    echo "✅ Created template with ID: $TEMPLATE_ID"
    echo ""
    
    # Test 5: Get the created template by ID
    echo "5️⃣ Testing GET /api/templates/{template_id}"
    echo "---"
    curl -s "${API_URL}/${TEMPLATE_ID}" | python3 -m json.tool || echo "❌ Failed"
    echo ""
    echo ""
    
    # Test 6: Update the template
    echo "6️⃣ Testing PUT /api/templates/{template_id} (Update)"
    echo "---"
    curl -s -X PUT "${API_URL}/${TEMPLATE_ID}" \
      -H "Content-Type: application/json" \
      -d '{"is_active": false}' | python3 -m json.tool || echo "❌ Failed"
    echo ""
    echo ""
    
    # Test 7: Toggle template status
    echo "7️⃣ Testing POST /api/templates/{template_id}/toggle"
    echo "---"
    curl -s -X POST "${API_URL}/${TEMPLATE_ID}/toggle" | python3 -m json.tool || echo "❌ Failed"
    echo ""
    echo ""
    
    # Test 8: Delete the template
    echo "8️⃣ Testing DELETE /api/templates/{template_id}"
    echo "---"
    curl -s -X DELETE "${API_URL}/${TEMPLATE_ID}" | python3 -m json.tool || echo "❌ Failed"
    echo ""
fi

echo ""
echo "=================================="
echo "✅ API Tests Complete"
echo ""
echo "💡 For interactive testing, visit:"
echo "   ${BASE_URL}/docs"
echo ""
