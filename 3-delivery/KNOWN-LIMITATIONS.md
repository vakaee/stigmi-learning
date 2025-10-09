# Known Limitations - AI Tutor POC

**Project**: MinS AI Tutor Prototype
**Phase**: 1 (Discovery & Prototype)
**Version**: 1.0

---

## Purpose

This document outlines the constraints and limitations of the Phase 1 prototype. These are intentional scope decisions, not bugs. Future phases will address these as needed.

---

## Prototype Limitations

### 1. Session Storage

**Limitation**: Sessions stored in n8n workflow variables (in-memory) or local files

**Impact**:
- Sessions lost if n8n restarts
- Not suitable for production (no persistence)
- Can't share sessions across multiple n8n instances

**Production solution**:
- Use Redis for session storage
- Or migrate to Node.js with database persistence

**Workaround for POC**:
- Use n8n Cloud (rarely restarts)
- Or implement Redis node (documented in blueprint)

---

### 2. Single Problem Focus

**Limitation**: No curriculum sequencing or multi-problem flows

**Current behavior**:
- Tutor handles one problem at a time
- No automatic progression to next problem
- No mastery tracking across problems

**Impact**:
- Can't scaffold multi-problem learning paths
- No "you've mastered addition, now try subtraction" flow

**Production solution**:
- Add curriculum engine (problem sequencing)
- Track mastery per concept
- Unlock problems based on prerequisites

---

### 3. Limited Question Bank

**Limitation**: 5-7 fully tested questions, 3 additional with basic specs

**Topics covered**:
- Negative number addition/subtraction
- Fraction addition/subtraction
- Simple word problems
- Order of operations

**Not covered**:
- Multiplication/division
- Decimals
- Geometry
- Algebra
- Word problems (complex)

**Production solution**:
- Expand to 100+ questions
- Cover all grade-level topics
- Build content management system

---

### 4. Text-Only (No Voice)

**Limitation**: Prototype handles text input/output only

**Not included**:
- Speech-to-text (STT)
- Text-to-speech (TTS)
- Voice conversation flow
- Interruption handling

**Production solution**:
- MinS already has voice module
- Can integrate via same webhook API
- Voice → STT → text webhook → tutor → TTS → voice

**Note**: Architecture supports this (stateless webhook), just not implemented in POC

---

### 5. English Only

**Limitation**: All prompts and responses in English

**Not supported**:
- Spanish, French, Mandarin, etc.
- Multi-language switching
- Localized examples

**Production solution**:
- Translate prompt templates
- Use multilingual models (GPT-4o supports 50+ languages)
- Detect language and route to appropriate prompts

---

### 6. Basic Math Verification

**Limitation**: Verification handles basic numeric and algebraic expressions only

**Supported**:
- `2`, `-8`, `1/2`, `0.5`
- `1/2 + 1/4` (simple expressions)
- `2 + 3 × 4` (order of operations)

**Not supported**:
- Complex symbolic math (e.g., `x^2 + 2x + 1 = (x+1)^2`)
- Matrix operations
- Calculus
- Proofs

**Production solution**:
- Add sympy (Python) or mathjs advanced features
- Or build separate symbolic math verification service

---

### 7. No Knowledge Base (RAG)

**Limitation**: Tutor cannot retrieve teaching materials from knowledge base

**Current behavior**:
- Generates all explanations on-the-fly with LLM
- No access to curated concept explanations
- No worked examples database

**Impact**:
- Inconsistent explanations (LLM variance)
- Can't reference specific teaching materials
- No guarantee of age-appropriate examples

**Production solution**:
- Build knowledge base (vector store with concept explanations)
- Implement RAG (retrieval-augmented generation)
- Curate age-appropriate examples

---

### 8. Single-Step Problems Only

**Limitation**: No multi-step problem decomposition

**Current**: Handles problems like "What is -3 + 5?"

**Not handled**:
- "Sarah had $5, spent $8, earned $10. How much now?" (requires 3 steps: 5-8, -3+10, = 7)
- "Solve for x: 2x + 5 = 13" (requires isolation, then division)

**Production solution**:
- Add agent-based decomposition (LangGraph)
- Break complex problems into sub-problems
- Guide through each step sequentially

---

### 9. No Student Profiles

**Limitation**: No persistent student data beyond session

**Not tracked**:
- Student skill level
- Learning preferences
- Historical performance
- Weak concepts

**Impact**:
- Can't adapt difficulty to student level
- No personalization across sessions
- Treats every student the same

**Production solution**:
- Build student profile database
- Track: concepts mastered, avg attempts, preferred learning style
- Adaptive difficulty and pace

---

### 10. Simple Triage (No Fine-Tuning)

**Limitation**: Uses generic GPT-4o-mini for classification (not fine-tuned)

**Impact**:
- Occasionally misclassifies edge cases
- No optimization for student language patterns
- Generic prompts (not tuned to MinS's student population)

**Production solution**:
- Collect real student interaction data
- Fine-tune GPT-4o-mini on MinS-specific patterns
- Use DSPy for automated prompt optimization

---

### 11. No Admin Dashboard

**Limitation**: No UI for content management or analytics

**Not included**:
- Question bank editor
- Prompt editor
- Analytics dashboard (category distribution, latency, etc.)
- Student progress reports

**Production solution**:
- Build admin portal
- Content management system for questions
- Real-time analytics dashboards

---

### 12. Manual Testing Only

**Limitation**: No automated test suite

**Current**: Manual testing with curl/Postman

**Not included**:
- Unit tests
- Integration tests
- End-to-end tests
- Continuous integration

**Production solution**:
- Add Jest/Mocha test suite
- Test all 6 categories automatically
- CI/CD pipeline with automated tests

---

## Security Limitations

### 1. Basic Authentication

**Current**: Optional Bearer token

**Not included**:
- OAuth2
- JWT validation
- Role-based access control (RBAC)
- IP whitelisting

**Production solution**: Use MinS's existing auth system (backend proxy pattern)

---

### 2. No Rate Limiting (Built-in)

**Current**: n8n doesn't have built-in rate limiting

**Risk**: Potential API abuse or DoS

**Production solution**:
- Add rate limiting middleware
- Use API gateway (AWS API Gateway, Kong)
- Or implement in backend proxy

---

### 3. Minimal Input Validation

**Current**: Basic type checking only

**Not validated**:
- SQL injection attempts (if database used)
- XXS in student inputs
- Extremely long inputs (token limit attacks)

**Production solution**: Add comprehensive input validation + sanitization

---

## Performance Limitations

### 1. No Caching

**Current**: Every request hits LLM (no response caching)

**Impact**:
- Same question asked 100 times = 100 LLM calls
- Higher cost and latency

**Production solution**:
- Cache common responses ("What's a negative number?" → cached explanation)
- Use Redis for response cache
- TTL: 1 hour

---

### 2. Sequential Operations

**Current**: Some operations run sequentially that could be parallel

**Example**:
- Load session (50ms)
- Stage 1 triage (300ms)
→ Could run in parallel (save 50ms)

**Production solution**: Parallelize independent operations with Promise.all()

---

### 3. Session Race Conditions

**Limitation**: Concurrent requests for the same session can overwrite each other

**Current behavior**:
- No locking mechanism for session updates
- If two requests arrive simultaneously for same session_id:
  1. Both load identical session state (e.g., attempt_count=1)
  2. Both process independently
  3. Both save back to storage
  4. Second save overwrites first save

**Impact**:
- Lost session updates (incorrect attempt_count, missing conversation turns)
- Data inconsistency in high-traffic scenarios
- Edge case that rarely occurs in POC (single student, ~1 request per 3-10 seconds)

**Example scenario**:
```
Time 0ms:   Request A loads session (attempt_count=1)
Time 10ms:  Request B loads session (attempt_count=1)
Time 500ms: Request A saves session (attempt_count=2)
Time 510ms: Request B saves session (attempt_count=2) ← OVERWRITES Request A!
Result: Only 1 increment instead of 2
```

**Likelihood in POC**: Very low
- Typical student response time: 3-10 seconds between messages
- Would require backend/frontend to send duplicate requests
- More likely in production with multiple students

**Production solutions**:

**Option A - Optimistic Locking** (recommended for low-medium traffic):
```javascript
// Add version number to session
session.version = session.version + 1;

// On save, check version matches
if (currentSession.version !== loadedSession.version) {
  throw new Error('Session modified by another request - retry');
}
```

**Option B - Pessimistic Locking** (for high traffic):
```javascript
// Acquire lock before loading
const lock = await acquireLock(sessionId, timeout=1000ms);
try {
  // Load, process, save
} finally {
  await releaseLock(sessionId);
}
```

**Option C - External Session Store** (best for production):
- Use Redis with WATCH/MULTI/EXEC (atomic transactions)
- Or use database with row-level locking
- Handles concurrency automatically

**Workaround for POC**:
- Not implemented (acceptable risk for single-student prototype)
- If encountered: restart session or ignore minor inconsistencies
- Production deployment MUST address this (recommend Redis with transactions)

**Related**: See "Session Storage" limitation (#1) - migrating to Redis solves both issues

---

### 4. No Load Balancing

**Current**: Single n8n instance

**Impact**: Limited to ~100 concurrent users

**Production solution**:
- Deploy multiple n8n instances behind load balancer
- Or migrate to Node.js with horizontal scaling

---

## Data Limitations

### 1. No Analytics Storage

**Current**: Metadata returned but not stored persistently

**Not tracked long-term**:
- Category distribution over time
- Student success rates
- Average attempts per problem
- Latency trends

**Production solution**:
- Log all interactions to database
- Build analytics pipeline
- Create dashboards

---

### 2. No Conversation History Export

**Current**: Sessions expire after 30 min (no long-term storage)

**Impact**:
- Can't review past conversations
- No data for training/improvement
- No student transcript

**Production solution**:
- Store full conversation history in MongoDB
- Keep indefinitely (or per retention policy)
- Enable export for review

---

## Edge Cases Not Fully Handled

### 1. Ambiguous Inputs

**Example**: "I think it's around two-ish"

**Current behavior**: May classify as non-answer (stuck) or fail verification

**Better handling**: Detect uncertainty ("around", "ish", "maybe") and ask for clarification

---

### 2. Multiple Answers

**Example**: "It's either 2 or 3"

**Current behavior**: Verification fails (can't parse)

**Better handling**: Detect "or" pattern and ask student to choose one

---

### 3. Non-Math Responses

**Example**: Student asks "Can you help with history too?"

**Current behavior**: Classified as off-topic, redirected

**Better handling**: Politely explain scope ("I'm a math tutor, but I'd love to help with math!")

---

### 4. Extremely Long Inputs

**Example**: Student pastes entire essay

**Current behavior**: May hit token limit or timeout

**Better handling**: Truncate with message ("That's a lot! Can you summarize in one sentence?")

---

## Pedagogical Limitations

### 1. No Learning Style Adaptation

**Current**: Same teaching approach for all students

**Not considered**:
- Visual vs verbal learners
- Fast vs slow pace preference
- Hint preference (lots vs minimal)

**Production solution**: Detect learning style from interaction patterns and adapt

---

### 2. No Metacognitive Prompts

**Current**: Focuses on problem-solving only

**Not included**:
- "What strategy did you use?"
- "How would you check your answer?"
- "Where have you seen this before?"

**Production solution**: Add metacognitive prompts to TEACH_BACK template

---

### 3. No Error Pattern Detection

**Current**: Treats each error independently

**Not detected**:
- Consistently confusing + and -
- Always forgetting negative signs
- Pattern of sign errors

**Production solution**: Track error patterns across problems, provide targeted remediation

---

## Deployment Limitations

### 1. n8n Platform Lock-in

**Current**: Tied to n8n infrastructure

**Impact**: Must migrate to Node.js for full control

**Timeline**: 2-3 weeks migration effort (documented in DEPLOYMENT.md)

---

### 2. No Blue-Green Deployment

**Current**: Workflow updates require downtime (activate/deactivate)

**Production solution**: Deploy to Node.js with zero-downtime deploys

---

### 3. No Auto-Scaling

**Current**: n8n Cloud auto-scales, but self-hosted doesn't

**Production solution**: Kubernetes deployment with HPA (horizontal pod autoscaling)

---

## Future Enhancement Roadmap

### Phase 2 (1-2 months)
- ✅ Knowledge base (RAG)
- ✅ Redis session storage
- ✅ Full analytics pipeline
- ✅ 50+ questions

### Phase 3 (3-6 months)
- ✅ Multi-step problem decomposition (agents)
- ✅ Fine-tuned triage model
- ✅ Student profiles & personalization
- ✅ Voice integration

### Phase 4 (6-12 months)
- ✅ Migrate to Node.js microservice
- ✅ Curriculum sequencing engine
- ✅ Multi-language support
- ✅ Admin dashboard & CMS

---

## Acceptance Criteria

**This prototype is considered successful if**:

✅ Demonstrates all 6 teaching categories correctly
✅ Shows adaptive multi-turn conversations
✅ Maintains session memory across turns
✅ Verifies answers accurately (edge cases handled)
✅ Meets latency target (≤3.5s, actual: ~1.5s)
✅ Provides clear architectural blueprint for production

**This prototype is NOT expected to**:

❌ Handle production-scale traffic (100+ concurrent users)
❌ Support full curriculum (just 5-10 exemplar questions)
❌ Integrate with all MinS systems (just webhook API)
❌ Replace existing MinS tutoring (just proof-of-concept)

---

## Using This Document

**For stakeholders (Min/Isaac)**:
- Use this to set realistic expectations for investor demo
- Understand what's in scope vs future roadmap

**For dev team**:
- Use this to plan Phase 2 implementation
- Prioritize which limitations to address first

**For support team**:
- Use this to answer "why doesn't it do X?" questions
- Set student expectations appropriately

---

**Version**: 1.0
**Last Updated**: October 10, 2025
**Next Review**: After Phase 1 debrief
