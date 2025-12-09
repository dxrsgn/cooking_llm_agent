#!/bin/bash

BASE_URL="http://localhost:8000"
AUTH_TOKEN="test-token-123"
THREAD_ID="test-thread-$(date +%s)"

echo "Testing FastAPI Backend"
echo "======================"
echo ""

echo "1. Testing POST /graph endpoint..."
curl -X POST "${BASE_URL}/graph" \
  -H "Content-Type: application/json" \
  -H "Authorization: ${AUTH_TOKEN}" \
  -d "{\"thread_id\": \"${THREAD_ID}\", \"message\": \"I want to make something for dinner\"}" \
  -w "\n"

echo ""
echo "2. Testing with follow-up message (same thread_id)..."
curl -X POST "${BASE_URL}/graph" \
  -H "Content-Type: application/json" \
  -H "Authorization: ${AUTH_TOKEN}" \
  -d "{\"thread_id\": \"${THREAD_ID}\", \"message\": \"Something vegetarian please\"}" \
  -w "\n"

echo ""
echo "3. Testing without message (should fail)..."
curl -X POST "${BASE_URL}/graph" \
  -H "Content-Type: application/json" \
  -H "Authorization: ${AUTH_TOKEN}" \
  -d "{\"thread_id\": \"${THREAD_ID}\"}" \
  -w "\n"

echo ""
echo "4. Testing without Authorization header (should fail)..."
curl -X POST "${BASE_URL}/graph" \
  -H "Content-Type: application/json" \
  -d "{\"thread_id\": \"${THREAD_ID}\", \"message\": \"test message\"}" \
  -w "\n"

echo ""
echo "Done!"
