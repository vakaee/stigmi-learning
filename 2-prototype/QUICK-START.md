# Quick Start Guide - AI Tutor Workflow

## Import & Setup (5 minutes)

### Step 1: Import Workflow
1. Open n8n (http://localhost:5678 or your n8n Cloud instance)
2. Click **Workflows** → **Import from File**
3. Select `workflow-production-ready.json`
4. Click **Import**

### Step 2: Configure OpenAI Credential
1. n8n will prompt: "This workflow uses credentials you don't have"
2. Click **Create OpenAI credential**
3. Enter your OpenAI API key (get from https://platform.openai.com/api-keys)
4. Click **Save**
5. n8n automatically links credential to all 8 OpenAI nodes

### Step 3: Activate Workflow
1. Click the toggle switch in top-right: **Inactive** → **Active**
2. Your webhook URL appears in the Webhook Trigger node
3. Copy it (format: `http://localhost:5678/webhook/tutor/message`)

---

## Test the Workflow

### Test 1: Correct Answer
```bash
curl -X POST http://localhost:5678/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_123",
    "session_id": "sess_456",
    "message": "2",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 5?",
      "correct_answer": "2"
    }
  }'
```

**Expected Response:**
```json
{
  "response": "Perfect! Can you explain how you got 2?",
  "metadata": {
    "category": "correct",
    "confidence": 0.99,
    "is_answer": true,
    "verification": {
      "correct": true,
      "student_value": 2,
      "correct_value": 2
    },
    "attempt_count": 1,
    "escalation_level": "probe",
    "latency_ms": 1500
  }
}
```

### Test 2: Wrong Answer
```bash
curl -X POST http://localhost:5678/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_123",
    "session_id": "sess_456",
    "message": "-8",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 5?",
      "correct_answer": "2"
    }
  }'
```

**Expected:** Category `wrong_operation`, Socratic question about the + sign

### Test 3: Stuck
```bash
# Use same structure but message: "I don't know"
```

**Expected:** Category `stuck`, scaffolding hint to break problem into steps

### Test 4: Off-Topic
```bash
# Use same structure but message: "What's for lunch?"
```

**Expected:** Category `off_topic`, polite redirect to problem

---

## Test All 6 Categories

Run these tests in sequence with **same session_id** to see escalation:

| Test | Message | Expected Category | Expected Behavior |
|------|---------|-------------------|-------------------|
| 1 | `"2"` | `correct` | Celebrate + ask for explanation |
| 2 | `"-8"` | `wrong_operation` | Ask about + vs - sign |
| 3 | `"1"` | `close` | Gentle probe (close to 2) |
| 4 | `"What is a negative number?"` | `conceptual_question` | Teach concept with examples |
| 5 | `"I don't know"` | `stuck` | Break into smaller steps |
| 6 | `"What's for lunch?"` | `off_topic` | Polite redirect |

---

## View Execution Details

1. In n8n, click **Executions** tab
2. Click on latest execution
3. See node-by-node data flow:
   - Webhook Trigger → received input
   - Stage 1 Triage → LLM classified as answer/non-answer
   - Verify Answer → math evaluation result
   - Stage 2a/2b → category classification
   - Response LLM → generated tutor message
   - Update Session → saved turn to memory

---

## Test Multi-Turn Conversation

Use **same session_id** across multiple requests:

```bash
# Turn 1
curl ... -d '{"session_id": "multi_turn_1", "message": "-8", ...}'
# → wrong_operation, attempt 1 (probe)

# Turn 2 (same session)
curl ... -d '{"session_id": "multi_turn_1", "message": "-6", ...}'
# → wrong_operation, attempt 2 (hint)

# Turn 3 (same session)
curl ... -d '{"session_id": "multi_turn_1", "message": "I'm stuck", ...}'
# → stuck, attempt 2 (more explicit)

# Turn 4 (same session)
curl ... -d '{"session_id": "multi_turn_1", "message": "2", ...}'
# → correct, attempt 3 (celebrate persistence)
```

Check `metadata.attempt_count` increments correctly.

---

## Troubleshooting

### Issue: "Missing OpenAI credential"
**Fix:** Go to node, click credential dropdown, select your OpenAI credential

### Issue: "Webhook URL not found"
**Fix:** Activate workflow first, then URL appears

### Issue: LLM response not parsing
**Fix:** Check Executions tab → see error in Parse Triage node → fallback regex activates

### Issue: Session not persisting
**Fix:** Sessions stored in workflow static data. They persist until:
- n8n restart (static data cleared)
- 30 minutes inactivity (session expires in production with Redis)

### Issue: Latency > 3.5s
**Fix:**
- Check OpenAI API status
- Reduce chat_history (currently 5 turns)
- Use faster model (already using gpt-4o-mini)

---

## Architecture Overview

```
Webhook → Load Session → Stage 1 Triage (LLM) → Parse
                                ↓
                         If Answer?
                    TRUE ↙        ↘ FALSE
              Verify Answer     Stage 2b (LLM)
                    ↓                  ↓
            Stage 2a (rules)      Parse 2b
                    ↓                  ↓
                 Enrich Context ←------
                        ↓
                Route by Category (6 branches)
                        ↓
        [correct] [close] [wrong] [conceptual] [stuck] [off_topic]
             ↓       ↓       ↓         ↓         ↓         ↓
           Response LLMs (6 nodes with adaptive prompts)
                        ↓
              Update Session & Format
                        ↓
                 Webhook Response
```

**Total Nodes:** 19
**LLM Calls:** 2 per request (Stage 1 + one Response LLM)
**Average Latency:** ~1.5s
**Cost per Turn:** ~$0.0003

---

## Next Steps

1. **Test all exemplars:** See `2-prototype/exemplars/questions.json`
2. **Integrate with MinS:** See `2-prototype/docs/INTEGRATION.md`
3. **Production deployment:** See `2-prototype/docs/DEPLOYMENT.md`
4. **Add Redis:** For persistent session storage (replace workflow static data)
5. **Monitor performance:** Track latency_ms in responses

---

## Reference

- **Full Blueprint:** `1-blueprint/Tutoring-Flow-Blueprint.md`
- **API Spec:** `2-prototype/docs/API-SPEC.md`
- **Prompt Templates:** `1-blueprint/prompts/*.yaml`
- **Test Questions:** `2-prototype/exemplars/questions.json`
