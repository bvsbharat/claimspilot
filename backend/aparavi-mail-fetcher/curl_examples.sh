#!/bin/bash

# Aparavi Gmail Fetcher - cURL Examples
# These are dummy placeholder endpoints for demonstration purposes

BASE_URL="http://localhost:5001"

echo "=========================================="
echo "Aparavi Gmail Fetcher - cURL Examples"
echo "=========================================="
echo ""

# 1. Health Check
echo "1. Health Check"
echo "Command:"
echo "curl -X GET ${BASE_URL}/aparavi/health"
echo ""
echo "Response:"
curl -X GET ${BASE_URL}/aparavi/health
echo -e "\n\n"

# 2. Validate Pipeline
echo "2. Validate Pipeline Configuration"
echo "Command:"
echo "curl -X POST ${BASE_URL}/aparavi/pipeline/validate"
echo ""
echo "Response:"
curl -X POST ${BASE_URL}/aparavi/pipeline/validate
echo -e "\n\n"

# 3. Fetch Gmail via Aparavi Pipeline
echo "3. Fetch Gmail Data via Aparavi Pipeline"
echo "Command:"
cat << 'EOF'
curl -X POST http://localhost:5001/aparavi/gmail/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "email_filters": {
      "from": "claims@insurance.com",
      "subject": "claim",
      "after": "2024-01-01",
      "before": "2024-12-31"
    },
    "max_results": 5
  }'
EOF
echo ""
echo "Response:"
curl -X POST ${BASE_URL}/aparavi/gmail/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "email_filters": {
      "from": "claims@insurance.com",
      "subject": "claim",
      "after": "2024-01-01",
      "before": "2024-12-31"
    },
    "max_results": 5
  }'
echo -e "\n\n"

# 4. Execute Pipeline
echo "4. Execute Pipeline Workflow"
echo "Command:"
cat << 'EOF'
curl -X POST http://localhost:5001/aparavi/pipeline/execute \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_config": "./aparavi-project-export-new-project-2025-10-04T17-32.json",
    "input_params": {
      "gmail_filters": {
        "from": "claims@insurance.com"
      }
    }
  }'
EOF
echo ""
echo "Response:"
EXECUTE_RESPONSE=$(curl -s -X POST ${BASE_URL}/aparavi/pipeline/execute \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_config": "./aparavi-project-export-new-project-2025-10-04T17-32.json",
    "input_params": {
      "gmail_filters": {
        "from": "claims@insurance.com"
      }
    }
  }')
echo $EXECUTE_RESPONSE
echo -e "\n"

# Extract token from response (if jq is available)
if command -v jq &> /dev/null; then
    TOKEN=$(echo $EXECUTE_RESPONSE | jq -r '.data.token')
    echo "Extracted Token: $TOKEN"
else
    TOKEN="task_token_1234567890.123"
    echo "Note: Install 'jq' to extract token automatically. Using dummy token: $TOKEN"
fi
echo -e "\n"

# 5. Get Pipeline Status
echo "5. Get Pipeline Status"
echo "Command:"
echo "curl -X GET ${BASE_URL}/aparavi/pipeline/status/${TOKEN}"
echo ""
echo "Response:"
curl -X GET ${BASE_URL}/aparavi/pipeline/status/${TOKEN}
echo -e "\n\n"

# 6. Teardown Pipeline
echo "6. Teardown Pipeline Resources"
echo "Command:"
echo "curl -X DELETE ${BASE_URL}/aparavi/pipeline/teardown/${TOKEN}"
echo ""
echo "Response:"
curl -X DELETE ${BASE_URL}/aparavi/pipeline/teardown/${TOKEN}
echo -e "\n\n"

# 7. Fetch Gmail with Different Filters
echo "7. Fetch Gmail with Subject Filter"
echo "Command:"
cat << 'EOF'
curl -X POST http://localhost:5001/aparavi/gmail/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "email_filters": {
      "subject": "insurance claim",
      "after": "2024-09-01"
    },
    "max_results": 10
  }'
EOF
echo ""
echo "Response:"
curl -X POST ${BASE_URL}/aparavi/gmail/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "email_filters": {
      "subject": "insurance claim",
      "after": "2024-09-01"
    },
    "max_results": 10
  }'
echo -e "\n\n"

echo "=========================================="
echo "All cURL examples completed!"
echo "=========================================="
