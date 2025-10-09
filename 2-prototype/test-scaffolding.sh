#!/bin/bash

# Test Script for Scaffolding and Teach-Back Features
# Tests the enhanced workflow-production-ready.json

# Configuration
WEBHOOK_URL="${N8N_WEBHOOK_URL:-http://localhost:5678/webhook/tutor/message}"
SESSION_ID="test_scaffold_$(date +%s)"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Testing Scaffolding and Teach-Back System"
echo "========================================="
echo ""
echo "Webhook URL: $WEBHOOK_URL"
echo "Session ID: $SESSION_ID"
echo ""

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local student_message="$2"
    local expected_category="$3"
    local turn_number="$4"

    TESTS_RUN=$((TESTS_RUN + 1))

    echo -e "${YELLOW}Test $TESTS_RUN: $test_name${NC}"
    echo "  Message: \"$student_message\""
    echo "  Expected: $expected_category"

    response=$(curl -s -X POST "$WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"student_id\": \"test_student\",
            \"session_id\": \"$SESSION_ID\",
            \"message\": \"$student_message\",
            \"current_problem\": {
                \"id\": \"neg_add_1\",
                \"text\": \"What is -3 + 5?\",
                \"correct_answer\": \"2\"
            }
        }")

    if [ $? -ne 0 ]; then
        echo -e "  ${RED}✗ FAILED: Could not connect to webhook${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    # Extract category from metadata if response is JSON
    category=$(echo "$response" | grep -o '"category":"[^"]*"' | head -1 | cut -d'"' -f4)

    if [ -z "$category" ]; then
        echo -e "  ${RED}✗ FAILED: Could not parse response${NC}"
        echo "  Response: $response"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    echo "  Got: $category"

    if [ "$category" = "$expected_category" ]; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}✗ FAILED: Expected $expected_category, got $category${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Show response excerpt
    tutor_response=$(echo "$response" | grep -o '"output":"[^"]*"' | head -1 | cut -d'"' -f4 | sed 's/\\n/ /g' | cut -c1-100)
    if [ -n "$tutor_response" ]; then
        echo "  Response: \"$tutor_response...\""
    fi

    echo ""

    # Small delay between requests
    sleep 2
}

echo "========================================="
echo "TEST SUITE 1: Scaffolding Flow"
echo "========================================="
echo ""

# Test 1: Student says "I don't know" - should enter scaffolding
run_test \
    "Enter scaffolding mode" \
    "I don't know" \
    "stuck" \
    1

# Test 2: Student responds to scaffolding question (assume they answer it correctly)
# Note: This would be detected as scaffold_progress by the agent
run_test \
    "Progress through scaffolding (answering sub-question)" \
    "It means we're at negative 3" \
    "stuck" \
    2

# Test 3: Student gets the main answer correct after scaffolding
run_test \
    "Solve main problem after scaffolding" \
    "2" \
    "correct" \
    3

echo ""
echo "========================================="
echo "TEST SUITE 2: Teach-Back Flow"
echo "========================================="
echo ""

# Start a new session for teach-back test
SESSION_ID="test_teachback_$(date +%s)"

# Test 4: Student gets answer correct on first try
run_test \
    "Get correct answer (should initiate teach-back)" \
    "2" \
    "correct" \
    1

# Test 5: Student provides explanation (should be classified as teach_back_explanation -> stuck)
run_test \
    "Provide teach-back explanation" \
    "I started at negative 3 and moved right 5 spaces on the number line to get to 2" \
    "stuck" \
    2

echo ""
echo "========================================="
echo "TEST SUITE 3: Edge Cases"
echo "========================================="
echo ""

# Start a new session
SESSION_ID="test_edge_$(date +%s)"

# Test 6: Scaffolding then wrong answer to scaffolding question
run_test \
    "Enter scaffolding" \
    "help" \
    "stuck" \
    1

# Test 7: Wrong answer to scaffolding question (should stay in stuck/scaffolding)
run_test \
    "Wrong answer to scaffolding question" \
    "positive 8" \
    "stuck" \
    2

# Test 8: Eventually get correct answer
run_test \
    "Correct answer after scaffolding attempts" \
    "2" \
    "correct" \
    3

echo ""
echo "========================================="
echo "SUMMARY"
echo "========================================="
echo ""
echo "Tests run: $TESTS_RUN"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review the output above.${NC}"
    exit 1
fi
