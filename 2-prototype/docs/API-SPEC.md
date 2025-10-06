# API Specification - AI Tutor Webhook

**Version**: 1.0
**Protocol**: HTTP/REST
**Format**: JSON
**Authentication**: Optional (Bearer token or API key)

---

## Base URL

```
Production: https://your-n8n-instance.com
Development: http://localhost:5678
```

---

## Endpoints

### POST /webhook/tutor/message

Send student message to AI tutor and receive adaptive response.

#### Request

**Headers**:
```http
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY (optional)
```

**Body**:
```json
{
  "student_id": "string (required)",
  "session_id": "string (required)",
  "message": "string (required)",
  "current_problem": {
    "id": "string (required)",
    "text": "string (required)",
    "correct_answer": "string (required)"
  }
}
```

**Field Descriptions**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_id` | string | Yes | Unique student identifier |
| `session_id` | string | Yes | Unique session identifier (create once per tutoring session) |
| `message` | string | Yes | Student's input message |
| `current_problem.id` | string | Yes | Unique problem identifier |
| `current_problem.text` | string | Yes | Problem statement shown to student |
| `current_problem.correct_answer` | string | Yes | Expected answer (for verification) |

**Example Request**:
```bash
curl -X POST https://n8n-instance.com/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer abc123" \
  -d '{
    "student_id": "user_789",
    "session_id": "sess_2024_10_08_001",
    "message": "-8",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 5?",
      "correct_answer": "2"
    }
  }'
```

---

#### Response

**Success (200 OK)**:
```json
{
  "response": "string",
  "metadata": {
    "category": "string",
    "confidence": "number",
    "is_answer": "boolean",
    "verification": {
      "correct": "boolean",
      "close": "boolean",
      "student_value": "number|null",
      "correct_value": "number|null",
      "difference": "number|null",
      "error": "string|null"
    },
    "attempt_count": "number",
    "escalation_level": "string",
    "latency_ms": "number",
    "timestamp": "string (ISO 8601)"
  }
}
```

**Field Descriptions**:

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | Tutor's message to display to student |
| `metadata.category` | string | One of: `correct`, `close`, `wrong_operation`, `conceptual_question`, `stuck`, `off_topic` |
| `metadata.confidence` | number | Classification confidence (0.0-1.0) |
| `metadata.is_answer` | boolean | Whether student provided an answer attempt |
| `metadata.verification` | object | Answer verification result (null if not answer) |
| `metadata.attempt_count` | number | Number of attempts on current problem |
| `metadata.escalation_level` | string | One of: `probe`, `hint`, `teach` |
| `metadata.latency_ms` | number | Total processing time in milliseconds |
| `metadata.timestamp` | string | Response generation timestamp |

**Example Response**:
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
      "correct_value": 2,
      "difference": 10,
      "error": null
    },
    "attempt_count": 1,
    "escalation_level": "probe",
    "latency_ms": 1450,
    "timestamp": "2025-10-08T10:31:22.456Z"
  }
}
```

---

#### Error Responses

**400 Bad Request** - Invalid input
```json
{
  "error": "Bad Request",
  "message": "Missing required field: current_problem.correct_answer",
  "timestamp": "2025-10-08T10:31:22.456Z"
}
```

**401 Unauthorized** - Invalid or missing API key
```json
{
  "error": "Unauthorized",
  "message": "Invalid API key",
  "timestamp": "2025-10-08T10:31:22.456Z"
}
```

**500 Internal Server Error** - System error
```json
{
  "error": "Internal Server Error",
  "message": "LLM API timeout - please try again",
  "retry_recommended": true,
  "timestamp": "2025-10-08T10:31:22.456Z"
}
```

**503 Service Unavailable** - Temporary failure
```json
{
  "error": "Service Unavailable",
  "message": "Session storage temporarily unavailable",
  "retry_after": 5,
  "timestamp": "2025-10-08T10:31:22.456Z"
}
```

---

## Authentication

### Option 1: Bearer Token (Recommended)

```http
Authorization: Bearer YOUR_SECRET_TOKEN
```

Configure in n8n Webhook node → Authentication → Header Auth:
- Header Name: `Authorization`
- Header Value: `Bearer {{$env.WEBHOOK_TOKEN}}`

### Option 2: API Key Header

```http
X-API-Key: YOUR_API_KEY
```

### Option 3: No Authentication (Development Only)

For testing, authentication can be disabled. **Not recommended for production.**

---

## Rate Limiting

**Current limits** (can be configured):
- **Per student**: 60 requests/minute
- **Global**: 1000 requests/minute

**Rate limit headers** (returned in response):
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1633024800
```

**Rate limit exceeded (429)**:
```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded. Try again in 15 seconds.",
  "retry_after": 15,
  "timestamp": "2025-10-08T10:31:22.456Z"
}
```

---

## Categories Reference

### 6 Teaching Categories

| Category | Trigger | Example Student Input | Tutor Strategy |
|----------|---------|----------------------|----------------|
| `correct` | Verified correct answer | "2" | Ask for explanation (teach-back) |
| `close` | Answer within 20% of correct | "1", "2.5" | Gentle probe to find error |
| `wrong_operation` | Significantly wrong answer | "-8", "8" | Clarify operation or concept |
| `conceptual_question` | Asking about concept | "What's a negative?" | Teach with examples |
| `stuck` | Help request | "I don't know", "help" | Break into smaller steps |
| `off_topic` | Unrelated message | "What's for lunch?" | Politely redirect |

---

## Session Management

### Session Lifecycle

1. **Create session**: Generate unique `session_id` when student starts
2. **Maintain session**: Use same `session_id` for all turns
3. **Session expires**: After 30 minutes of inactivity (TTL)
4. **New session**: If expired, create new `session_id`

### Session ID Format

Recommended format:
```
sess_{timestamp}_{student_id}_{random}
```

Example:
```
sess_20251008_user789_a3f2c1
```

### Problem Changes

When `current_problem.id` changes:
- `attempt_count` resets to 0
- Session memory continues (last 5 turns preserved)

---

## Data Flow Examples

### Example 1: Correct Answer (First Try)

**Request**:
```json
{
  "student_id": "user123",
  "session_id": "sess001",
  "message": "2",
  "current_problem": {
    "id": "neg_add_1",
    "text": "What is -3 + 5?",
    "correct_answer": "2"
  }
}
```

**Response**:
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
      "correct_value": 2,
      "difference": 0
    },
    "attempt_count": 1,
    "escalation_level": "probe",
    "latency_ms": 1220
  }
}
```

---

### Example 2: Multi-Turn Conversation

**Turn 1** (wrong answer):
```json
// Request
{"message": "-8", ...}

// Response
{
  "response": "When we see +, are we adding or subtracting?",
  "metadata": {
    "category": "wrong_operation",
    "attempt_count": 1,
    "escalation_level": "probe"
  }
}
```

**Turn 2** (non-answer, stuck):
```json
// Request (same session_id)
{"message": "adding", ...}

// Response
{
  "response": "Right! Starting at -3, which way do we move when adding?",
  "metadata": {
    "category": "stuck",
    "attempt_count": 1,
    "escalation_level": "probe"
  }
}
```

**Turn 3** (correct):
```json
// Request (same session_id)
{"message": "2", ...}

// Response
{
  "response": "Yes! Can you explain how you got from -3 to 2?",
  "metadata": {
    "category": "correct",
    "attempt_count": 2,
    "escalation_level": "hint"
  }
}
```

---

### Example 3: Escalation After Multiple Attempts

**Turn 1** (attempt 1):
```json
{
  "response": "You're close! Want to check your calculation?",
  "metadata": {
    "category": "close",
    "attempt_count": 1,
    "escalation_level": "probe"
  }
}
```

**Turn 2** (attempt 2):
```json
{
  "response": "Almost! Let's count together: -3, -2, -1, 0, 1...",
  "metadata": {
    "category": "close",
    "attempt_count": 2,
    "escalation_level": "hint"
  }
}
```

**Turn 3** (attempt 3):
```json
{
  "response": "Let me show you: starting at -3, move right 5 spaces: -3, -2, -1, 0, 1, 2. See how we landed on 2?",
  "metadata": {
    "category": "close",
    "attempt_count": 3,
    "escalation_level": "teach"
  }
}
```

---

## Performance Expectations

### Latency Targets

| Metric | Target | Typical |
|--------|--------|---------|
| **P50 (median)** | ≤1.5s | ~1.2s |
| **P95** | ≤2.5s | ~2.1s |
| **P99** | ≤3.5s | ~3.0s |
| **Max acceptable** | 5.0s | - |

### Latency Breakdown

Typical 1.5s turn:
- Session load: 50ms
- Stage 1 triage: 300ms
- Verification: 50ms
- Stage 2 classification: 200ms
- Response generation: 800ms
- Session save: 30ms
- Overhead: 70ms

---

## Testing

### Health Check Endpoint

```bash
GET /webhook/health

# Response
{
  "status": "ok",
  "version": "1.0",
  "timestamp": "2025-10-08T10:31:22.456Z"
}
```

### Test Payloads

See `tests/test-scenarios/` for complete test payloads covering all 6 categories.

Quick test:
```bash
curl -X POST http://localhost:5678/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -d @tests/test-scenarios/correct.json
```

---

## Webhooks vs REST API

This system uses **webhook pattern** (POST-only, single endpoint) rather than full REST API.

**Why webhook?**
- Simpler integration (one endpoint)
- Stateless requests (session stored server-side)
- Easier to migrate to async/event-driven architecture later

**Future REST API** (if needed):
```
GET    /api/sessions/{session_id}          # Get session state
POST   /api/sessions                       # Create session
DELETE /api/sessions/{session_id}          # End session
POST   /api/tutor/message                  # Send message (same as webhook)
GET    /api/students/{student_id}/history  # Get conversation history
```

---

## Security Best Practices

1. **Always use HTTPS** in production
2. **Enable authentication** (Bearer token minimum)
3. **Validate all inputs** server-side
4. **Rate limit** per student and globally
5. **Don't expose** `correct_answer` in responses (keep server-side only)
6. **Log minimal PII** (student_id only, not names/emails)
7. **Set CORS** appropriately (whitelist MinS domains only)

---

## Migration Path

### From Prototype to Production

**Phase 1** (Now): n8n webhook
**Phase 2** (Later): Node.js/Express API

**Migration strategy**:
1. Keep exact same API contract
2. Replace n8n with Express.js server
3. Use same JavaScript functions (already in Node.js)
4. Add database persistence (MongoDB)
5. Add Redis for session caching
6. Deploy as separate microservice or integrate into MinS backend

**Zero changes needed** in frontend integration code.

---

## Support

- **API issues**: Check n8n execution logs
- **Latency problems**: See `LATENCY-ANALYSIS.md`
- **Integration help**: See `INTEGRATION.md`
- **Full specification**: See `../1-blueprint/Tutoring-Flow-Blueprint.md`

---

**Version**: 1.0
**Last Updated**: October 10, 2025
**Status**: Phase 1 Prototype
