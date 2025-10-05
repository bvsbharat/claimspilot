#!/bin/bash
# Test RAG functionality

BASE_URL="http://localhost:8080"

echo "🧪 Testing Real-time RAG System"
echo "================================"
echo ""

# Test 1: Check RAG stats
echo "📊 Test 1: Checking RAG statistics..."
curl -s "$BASE_URL/api/chat/stats" | python3 -m json.tool
echo ""
echo ""

# Test 2: Query RAG (general)
echo "💬 Test 2: Asking general question..."
curl -s -X POST "$BASE_URL/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What claims do you have information about?"}' \
  | python3 -m json.tool
echo ""
echo ""

# Test 3: Query RAG (specific)
echo "💬 Test 3: Asking specific question..."
curl -s -X POST "$BASE_URL/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the total claim amount across all claims?"}' \
  | python3 -m json.tool
echo ""
echo ""

# Test 4: Upload a new file
echo "📤 Test 4: Uploading test claim..."
if [ -f "dummy-claims/sample_injury_claim.pdf" ]; then
    UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/claims/upload" \
      -F "file=@dummy-claims/sample_injury_claim.pdf")
    echo "$UPLOAD_RESPONSE" | python3 -m json.tool
    echo ""

    echo "⏳ Waiting 15 seconds for processing..."
    sleep 15
    echo ""

    # Test 5: Query the new claim
    echo "💬 Test 5: Querying newly uploaded claim..."
    curl -s -X POST "$BASE_URL/api/chat/query" \
      -H "Content-Type: application/json" \
      -d '{"query": "What information do you have about the injury claim that was just uploaded?"}' \
      | python3 -m json.tool
    echo ""
else
    echo "⚠️  No test file found at dummy-claims/sample_injury_claim.pdf"
    echo "   Skipping upload test"
fi

echo ""
echo "✅ RAG tests complete!"
echo ""
echo "To test manually:"
echo "  curl -X POST $BASE_URL/api/chat/query \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"query\": \"Your question here\"}'"
