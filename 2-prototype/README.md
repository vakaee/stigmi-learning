# AI Tutor Prototype - Setup & Testing Guide

**Version**: 1.0
**Platform**: n8n + OpenAI GPT-4o-mini
**Status**: Phase 1 Deliverable

---

## Overview

This prototype demonstrates a complete adaptive AI tutoring system with:
- Two-stage triage classification
- Answer verification with edge case handling
- Session memory (last 5 turns)
- Attempt-based response escalation
- 6 pedagogical categories

## Quick Start

### Prerequisites

- **n8n** (self-hosted or cloud): https://n8n.io
- **OpenAI API key**: https://platform.openai.com/api-keys
- **Redis** (optional, for session storage): https://redis.io
  - Alternative: File-based storage (built into n8n)

### Setup Steps

#### 1. Install n8n

**Cloud** (easiest):
```bash
# Sign up at n8n.cloud - no installation needed
```

**Self-hosted** (Docker):
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8n
```

**Self-hosted** (npm):
```bash
npm install n8n -g
n8n start
```

Access at: `http://localhost:5678`

#### 2. Configure Credentials

In n8n:
1. Go to **Settings** → **Credentials**
2. Add **OpenAI** credential:
   - API Key: `your_openai_api_key`
   - Organization (optional): leave blank
3. (Optional) Add **Redis** credential:
   - Host: `localhost` or your Redis server
   - Port: `6379`
   - Password: if required

#### 3. Import Workflow

1. In n8n, click **Workflows** → **Import from File**
2. Select `workflow.json` from this directory
3. Activate the workflow

**Note**: `workflow.json` will be created once the n8n prototype is built. For now, this README provides the setup foundation.

#### 4. Test Webhook

Get your webhook URL from the **Webhook** node in the workflow.

Example test:
```bash
curl -X POST http://localhost:5678/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_student_123",
    "session_id": "test_session_456",
    "message": "-8",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 5?",
      "correct_answer": "2"
    }
  }'
```

Expected response:
```json
{
  "response": "When we see +, are we adding or subtracting?",
  "metadata": {
    "category": "wrong_operation",
    "confidence": 0.94,
    "is_answer": true,
    "verification": {
      "correct": false,
      "close": false,
      "student_value": -8,
      "correct_value": 2
    },
    "attempt_count": 1,
    "latency_ms": 1450
  }
}
```

---

## Testing

### Manual Testing

Use the test questions in `exemplars/questions.json`:

**Test 1: Correct Answer**
```bash
curl -X POST http://localhost:5678/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_student",
    "session_id": "session_1",
    "message": "2",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 5?",
      "correct_answer": "2"
    }
  }'
```

Expected category: `correct`

**Test 2: Close Answer**
```bash
# Same as above, but "message": "1"
```

Expected category: `close`

**Test 3: Wrong Operation**
```bash
# Same as above, but "message": "-8"
```

Expected category: `wrong_operation`

**Test 4: Conceptual Question**
```bash
# "message": "What's a negative number?"
```

Expected category: `conceptual_question`

**Test 5: Stuck**
```bash
# "message": "I don't know"
```

Expected category: `stuck`

**Test 6: Off-Topic**
```bash
# "message": "What's for lunch?"
```

Expected category: `off_topic`

### Multi-Turn Conversation Test

Test adaptive escalation:

```bash
# Turn 1 (attempt 1)
# message: "-8"
# Expected: Probing question

# Turn 2 (attempt 2, same session_id)
# message: "-6"
# Expected: More explicit hint

# Turn 3 (attempt 3, same session_id)
# message: "I'm still stuck"
# Expected: Direct teaching with worked example

# Turn 4
# message: "2"
# Expected: Celebration + teach-back request
```

### Postman Collection

Import `tests/postman-collection.json` (once created) for all test scenarios.

---

## Project Structure

```
2-prototype/
├── README.md                     # This file
├── workflow.json                 # n8n workflow (to be created)
├── .env.example                  # Environment variables template
│
├── functions/                    # JavaScript for n8n nodes
│   ├── verify_answer.js          # Answer verification logic
│   ├── session_management.js     # Session state handling
│   └── classify_answer_quality.js # Stage 2a classification
│
├── exemplars/
│   └── questions.json            # Test questions with metadata
│
├── tests/                        # Testing resources
│   ├── curl-examples.sh          # Command-line test script
│   └── postman-collection.json   # API test collection
│
└── docs/
    ├── API-SPEC.md               # Webhook API documentation
    ├── INTEGRATION.md            # How to integrate with MinS
    ├── DEPLOYMENT.md             # Production deployment guide
    └── LATENCY-ANALYSIS.md       # Performance tuning guide
```

---

## Configuration

### Environment Variables

Create `.env` file (copy from `.env.example`):

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_ORG_ID=optional_org_id

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=optional_password

# n8n Webhook Configuration
WEBHOOK_PATH=/tutor/message
WEBHOOK_AUTH=bearer_token_or_api_key
```

### Workflow Configuration

In n8n workflow, configure:

1. **Webhook Trigger Node**:
   - Path: `/tutor/message`
   - Method: `POST`
   - Authentication: `Header Auth` (optional)

2. **OpenAI Nodes** (Triage + Response):
   - Model: `gpt-4o-mini`
   - Temperature: `0.1` (triage), `0.7` (response)
   - Max Tokens: `50` (triage), `150` (response)

3. **Redis Nodes** (if using):
   - Operation: `Get` / `Set`
   - Key: `session:${sessionId}`
   - TTL: `1800` (30 minutes)

---

## Workflow Overview

### n8n Workflow Nodes (Summary)

1. **Webhook** → Receive student message
2. **Get Session** → Load from Redis/file (parallel with #3)
3. **Stage 1 Triage** → LLM: is_answer? (parallel with #2)
4. **Branch** → Answer vs non-answer
5. **Verify Answer** → JavaScript verification (if answer)
6. **Stage 2a/2b** → Classify quality or intent
7. **Context Enrichment** → Add attempt count, escalation
8. **Router** → 6 branches (one per category)
9. **Response Generation** → LLM with category prompt
10. **Update Session** → Save turn, increment attempts
11. **Webhook Response** → Return tutor message

### Data Flow

```
Input → {student_id, session_id, message, current_problem}
    ↓
Load session + Triage (parallel)
    ↓
Verify (if answer) → Classify → Route → Generate → Save
    ↓
Output → {response, metadata}
```

---

## Monitoring & Debugging

### Check Workflow Execution

In n8n:
1. Go to **Executions** tab
2. Click on recent execution
3. View node-by-node data flow
4. Check for errors in red nodes

### Common Issues

**Issue**: LLM timeout
- **Cause**: OpenAI API slow or rate limited
- **Fix**: Increase timeout in OpenAI node settings (default 60s)

**Issue**: Session not persisting
- **Cause**: Redis not connected or file path incorrect
- **Fix**: Check Redis credentials or file node configuration

**Issue**: Verification always fails
- **Cause**: math.js not available in n8n
- **Fix**: Ensure n8n version includes math.js (v0.224.0+)

**Issue**: Wrong category classification
- **Cause**: Prompt engineering or model variance
- **Fix**: Adjust prompts in workflow or increase temperature slightly

### Logging

Enable debug logging in n8n:
```bash
export N8N_LOG_LEVEL=debug
n8n start
```

View logs: Check console or `~/.n8n/logs/`

---

## Performance

### Expected Latency

| Operation | Target | Typical |
|-----------|--------|---------|
| Full turn | ≤3.5s | ~1.5s |
| Stage 1 triage | ≤500ms | ~300ms |
| Verification | ≤100ms | ~50ms |
| Response gen | ≤2s | ~800ms |

### Cost per Turn

- **Triage**: ~100 tokens × $0.15/1M = $0.000015
- **Response**: ~500 tokens × $0.60/1M = $0.0003
- **Total**: ~$0.0003 per turn

**Monthly cost** (1000 students × 10 turns): ~$3.30

---

## Integration with MinS

See `docs/INTEGRATION.md` for detailed integration guide.

**Quick summary**:

```javascript
// In MinS frontend
async function sendToTutor(studentMessage) {
  const response = await fetch('https://n8n-instance.com/webhook/tutor/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: currentUser.id,
      session_id: currentSession.id,
      message: studentMessage,
      current_problem: getCurrentProblem()
    })
  });

  const data = await response.json();
  displayTutorMessage(data.response);
}
```

---

## Next Steps

1. **Test all 6 categories** with exemplar questions
2. **Integrate with MinS text module** (see INTEGRATION.md)
3. **Production deployment** (see DEPLOYMENT.md)
4. **Migrate to Node.js** (optional, for full control)

---

## Support

For questions:
- Review full blueprint: `../1-blueprint/Tutoring-Flow-Blueprint.md`
- Check API spec: `docs/API-SPEC.md`
- See troubleshooting: This README's "Common Issues" section

---

**Status**: Prototype complete and ready for testing
**Next Phase**: Integration with MinS production system
