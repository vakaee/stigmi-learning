# n8n Workflow Setup Guide

**AI Tutor POC - n8n Configuration**

This guide walks you through importing and configuring the AI Tutor workflows in n8n.

---

## Prerequisites

Before starting, ensure you have:

- [ ] n8n instance running (Cloud or self-hosted)
- [ ] OpenAI API key
- [ ] Access to n8n editor UI
- [ ] Basic familiarity with n8n interface

---

## Quick Start: Choose Your Workflow

We provide two workflow files:

### Option A: Simple Test Workflow (Recommended First)
**File**: `workflow-simple.json`
- **Purpose**: Basic functionality test
- **Features**: Answer verification + 2 response paths (correct/wrong)
- **Use for**: Validating n8n setup, testing OpenAI connection
- **Time to setup**: 5 minutes

### Option B: Complete Production Workflow
**File**: `workflow.json`
- **Purpose**: Full adaptive tutoring system
- **Features**: Two-stage triage, 6 categories, session memory
- **Use for**: Production deployment, full testing
- **Time to setup**: 10 minutes

**Recommendation**: Start with Simple, then upgrade to Complete once validated.

---

## Step 1: Import Workflow

### Using n8n Cloud

1. Log in to your n8n Cloud instance
2. Click **Workflows** in left sidebar
3. Click **+ Add Workflow** button (top right)
4. Click the **⋮** menu (three dots, top right)
5. Select **Import from File**
6. Choose `workflow-simple.json` or `workflow.json`
7. Click **Open**
8. Workflow appears in editor

### Using Self-Hosted n8n

1. Navigate to `http://localhost:5678` (or your n8n URL)
2. Log in with your credentials
3. Follow same steps as Cloud (above)

---

## Step 2: Configure OpenAI Credentials

The workflow uses OpenAI's API for LLM calls. You need to add your API key.

### Add OpenAI Credential

1. Click **Credentials** in left sidebar
2. Click **+ Add Credential** button
3. Search for "OpenAI"
4. Select **OpenAI**
5. Enter your API key:
   - **API Key**: `sk-...` (from OpenAI dashboard)
   - **Organization ID**: (optional, leave blank if not using)
6. Click **Save**
7. Note the credential name (e.g., "OpenAI Account")

### Link Credential to Workflow

For **workflow-simple.json**:
1. Open the workflow
2. Click on **Response: Correct** node (OpenAI node)
3. In node settings, find **Credential to connect with**
4. Select the OpenAI credential you just created
5. Repeat for **Response: Wrong** node

For **workflow.json**:
1. Open the workflow
2. Click on **Stage 1: Triage (Is Answer?)** node
3. Link your OpenAI credential
4. Repeat for these nodes:
   - **Stage 2b: Non-Answer Intent**
   - **Response: Correct (Teach Back)**
   - **Response: Close (Probe)**
   - **Response: Wrong Operation (Clarify)**
   - **Response: Conceptual Question**
   - **Response: Stuck (Scaffold)**
   - **Response: Off Topic (Redirect)**

---

## Step 3: Activate Workflow

1. Click **Save** button (top right)
2. Toggle the **Active** switch (top right) to ON
3. Workflow is now listening for webhooks

---

## Step 4: Get Webhook URL

### Production URL (for use in your app)

1. Click on the **Webhook Trigger** node (first node)
2. In node settings, you'll see:
   - **Webhook URLs**
   - **Test URL**: `https://your-instance.app.n8n.cloud/webhook-test/tutor-test`
   - **Production URL**: `https://your-instance.app.n8n.cloud/webhook/tutor-test`

3. Copy the **Production URL**
4. Save this for integration (you'll use it in your app)

**Important**:
- Use **Test URL** for manual testing (shows execution in UI)
- Use **Production URL** for app integration (faster, no UI)

### For workflow.json:
- Path will be `/webhook/tutor/message` (not `/tutor-test`)

---

## Step 5: Test the Workflow

### Manual Test (Using n8n Test Feature)

1. Ensure workflow is **Active**
2. Click **Execute Workflow** button (top right)
3. n8n will wait for a webhook call
4. Open a new terminal and run:

```bash
curl -X POST https://your-instance.app.n8n.cloud/webhook-test/tutor-test \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_student_123",
    "session_id": "test_session_001",
    "message": "2",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 5?",
      "correct_answer": "2"
    }
  }'
```

5. Check n8n UI - you should see:
   - Green checkmarks on all executed nodes
   - Response JSON at the end
   - Execution time

### Expected Response (workflow-simple.json):

```json
{
  "response": "Great! Can you explain how you got 2?",
  "metadata": {
    "category": "correct",
    "is_correct": true,
    "timestamp": "2025-10-10T12:34:56.789Z"
  }
}
```

### Expected Response (workflow.json):

```json
{
  "response": "Perfect! Can you walk me through how you figured that out?",
  "metadata": {
    "category": "correct",
    "confidence": 0.99,
    "verification": {
      "correct": true,
      "student_value": 2,
      "correct_value": 2
    },
    "attempt_count": 1,
    "latency_ms": 1450,
    "session_id": "test_session_001"
  }
}
```

---

## Step 6: Test All Categories (workflow.json only)

Run these tests to verify all 6 response paths work:

### 1. Correct Answer
```bash
curl -X POST [WEBHOOK_URL] -H "Content-Type: application/json" -d '{
  "student_id": "test_123",
  "session_id": "sess_001",
  "message": "2",
  "current_problem": {"id": "neg_add_1", "text": "What is -3 + 5?", "correct_answer": "2"}
}'
```
Expected category: `correct`

### 2. Close Answer
```bash
curl -X POST [WEBHOOK_URL] -H "Content-Type: application/json" -d '{
  "student_id": "test_123",
  "session_id": "sess_002",
  "message": "1",
  "current_problem": {"id": "neg_add_1", "text": "What is -3 + 5?", "correct_answer": "2"}
}'
```
Expected category: `close`

### 3. Wrong Operation
```bash
curl -X POST [WEBHOOK_URL] -H "Content-Type: application/json" -d '{
  "student_id": "test_123",
  "session_id": "sess_003",
  "message": "-8",
  "current_problem": {"id": "neg_add_1", "text": "What is -3 + 5?", "correct_answer": "2"}
}'
```
Expected category: `wrong_operation`

### 4. Conceptual Question
```bash
curl -X POST [WEBHOOK_URL] -H "Content-Type: application/json" -d '{
  "student_id": "test_123",
  "session_id": "sess_004",
  "message": "What is a negative number?",
  "current_problem": {"id": "neg_add_1", "text": "What is -3 + 5?", "correct_answer": "2"}
}'
```
Expected category: `conceptual_question`

### 5. Stuck
```bash
curl -X POST [WEBHOOK_URL] -H "Content-Type: application/json" -d '{
  "student_id": "test_123",
  "session_id": "sess_005",
  "message": "I don'\''t know",
  "current_problem": {"id": "neg_add_1", "text": "What is -3 + 5?", "correct_answer": "2"}
}'
```
Expected category: `stuck`

### 6. Off Topic
```bash
curl -X POST [WEBHOOK_URL] -H "Content-Type: application/json" -d '{
  "student_id": "test_123",
  "session_id": "sess_006",
  "message": "What'\''s for lunch?",
  "current_problem": {"id": "neg_add_1", "text": "What is -3 + 5?", "correct_answer": "2"}
}'
```
Expected category: `off_topic`

---

## Step 7: Test Session Memory (workflow.json only)

To verify session memory works across turns:

### Turn 1
```bash
curl -X POST [WEBHOOK_URL] -H "Content-Type: application/json" -d '{
  "student_id": "test_123",
  "session_id": "memory_test",
  "message": "-8",
  "current_problem": {"id": "neg_add_1", "text": "What is -3 + 5?", "correct_answer": "2"}
}'
```
Note the response (should ask about adding vs subtracting)

### Turn 2 (same session_id)
```bash
curl -X POST [WEBHOOK_URL] -H "Content-Type: application/json" -d '{
  "student_id": "test_123",
  "session_id": "memory_test",
  "message": "adding",
  "current_problem": {"id": "neg_add_1", "text": "What is -3 + 5?", "correct_answer": "2"}
}'
```
Response should reference the previous turn

### Turn 3 (same session_id)
```bash
curl -X POST [WEBHOOK_URL] -H "Content-Type: application/json" -d '{
  "student_id": "test_123",
  "session_id": "memory_test",
  "message": "2",
  "current_problem": {"id": "neg_add_1", "text": "What is -3 + 5?", "correct_answer": "2"}
}'
```
Response should celebrate success and ask for explanation

Check `metadata.attempt_count` increments: 1 → 1 (not an answer) → 2

---

## Step 8: Check Execution Logs

1. Click **Executions** in left sidebar
2. See list of all workflow runs
3. Click on any execution to view:
   - Input data
   - Each node's output
   - Execution time per node
   - Total latency

**Performance check**: Total execution time should be <2000ms for most cases.

---

## Step 9: Production Configuration (Optional)

### Enable Authentication

For production, protect your webhook:

1. Click on **Webhook Trigger** node
2. Scroll to **Authentication** section
3. Select **Header Auth**
4. Set header name: `X-API-Key`
5. Set header value: `your-secret-token-here` (generate a secure random string)
6. Save workflow

Now all requests must include:
```bash
curl -X POST [WEBHOOK_URL] \
  -H "X-API-Key: your-secret-token-here" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Add Rate Limiting (n8n Cloud only)

n8n Cloud includes rate limiting by default. For self-hosted:

1. Use nginx reverse proxy with rate limiting
2. Or add rate limiting logic in backend proxy (Option B in INTEGRATION.md)

---

## Step 10: Integration with Your App

Once tested, integrate with your application:

### Update Environment Variables

In your app's `.env` file:
```bash
TUTOR_WEBHOOK_URL=https://your-instance.app.n8n.cloud/webhook/tutor/message
TUTOR_API_KEY=your-secret-token-here
```

### Frontend or Backend Integration

See `INTEGRATION.md` for code examples:
- **Option A**: Direct frontend call (quick test)
- **Option B**: Backend proxy (recommended)
- **Option C**: Iframe (testing only)

---

## Troubleshooting

If you run into issues, see `N8N-TROUBLESHOOTING.md` for common problems and fixes.

---

## Next Steps

1. Test all 6 categories
2. Test session memory across multiple turns
3. Measure latency (should be <2s average)
4. Review execution logs for errors
5. Configure authentication for production
6. Integrate with your app (see INTEGRATION.md)
7. Deploy to production (see DEPLOYMENT.md)

---

## Useful Resources

- **n8n Documentation**: https://docs.n8n.io
- **OpenAI API Reference**: https://platform.openai.com/docs
- **Workflow Files**:
  - `workflow-simple.json` (basic test)
  - `workflow.json` (full production)
- **Exemplar Questions**: `2-prototype/exemplars/questions.json`
- **API Specification**: `API-SPEC.md`

---

**Setup Version**: 1.0
**Last Updated**: October 10, 2025
**Estimated Setup Time**: 15-20 minutes (including testing)
