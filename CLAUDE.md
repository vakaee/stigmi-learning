# CLAUDE.md

This file provides guidance to future instances when working with code in this repository.

## Project Overview

AI Tutor POC - Adaptive math tutoring system demonstrating intelligent student response classification, answer verification, multi-turn conversation memory, and Socratic teaching methodology. Built as a proof-of-concept using n8n workflow orchestration with OpenAI GPT-4o-mini.

**Status**: Phase 1 delivery complete (October 10, 2025)
**Budget**: $1,000 fixed / 10 hours
**Client**: MinS Education Platform

## Key Architecture

### Two-Stage Triage System
The core innovation is a two-stage classification system:

1. **Stage 1 (LLM)**: Determines if student input is an answer attempt or non-answer (question/help/off-topic)
2. **Stage 2a (Rule-based)**: If answer → verify correctness → classify as correct/close/wrong_operation
3. **Stage 2b (LLM)**: If non-answer → classify as conceptual_question/stuck/off_topic

This separation is critical because you cannot verify an answer before knowing it's an answer attempt, but you need verification results to classify answer quality.

### Six Teaching Categories
All system behavior routes through these categories:
- **correct**: Teach-back method (ask student to explain)
- **close**: Gentle probe to find small error (within 20% threshold)
- **wrong_operation**: Clarify misconception (Socratic questioning)
- **conceptual_question**: Teach concept with concrete examples
- **stuck**: Scaffold into smaller steps
- **off_topic**: Politely redirect to problem

### Adaptive Escalation
Response intensity adapts based on attempt count:
- **Attempt 1**: Probing Socratic questions
- **Attempt 2**: More explicit hints
- **Attempt 3+**: Direct teaching with worked examples

### Session Memory
Sessions maintain last 15 conversation turns for context, track attempt count per problem, and expire after 30 minutes. When problem ID changes, attempt count resets but conversation history continues (keeping last 3 turns for continuity).

## Project Structure

```
1-blueprint/           - Complete architectural specification
  prompts/             - 8 YAML prompt templates (triage + 6 categories)
  diagrams/            - Visual architecture

2-prototype/           - Working n8n implementation
  workflow.json        - Importable n8n workflow (complete system)
  workflow-simple.json - Simplified version
  functions/           - JavaScript for n8n nodes
    verify_answer.js           - Math verification with edge cases
    session_management.js      - Session state & memory window
    classify_answer_quality.js - Rule-based classification
  exemplars/           - Test questions with expected behaviors
  docs/                - API spec, integration, deployment guides

3-delivery/            - Handoff materials
  CHANGELOG.md         - Development decisions log
  KNOWN-LIMITATIONS.md - Prototype constraints
  HANDOFF-CHECKLIST.md - For dev team onboarding
```

## Critical Implementation Details

### Answer Verification (2-prototype/functions/verify_answer.js)
- Uses math.js to evaluate mathematical expressions
- Handles decimals, fractions, written numbers ("two" → "2"), negatives
- **20% threshold**: Answers within 20% of correct value are "close" (not "wrong")
- Returns: {correct: bool, close: bool, student_value: number, correct_value: number, difference: number}

### Session Schema
```javascript
{
  session_id: string,
  student_id: string,
  current_problem: {
    id: string,           // Problem identifier
    attempt_count: number // Resets when problem.id changes
  },
  recent_turns: [],       // Last 15 turns (trimmed automatically)
  concepts_taught: []
}
```

### Prompt Templates (1-blueprint/prompts/)
All prompts use Jinja2 syntax with conditionals based on `attempt_count`:
- triage-stage1.yaml - Intent detection (answer vs non-answer)
- triage-stage2b.yaml - Non-answer classification
- teach_back.yaml, probe.yaml, clarify.yaml, concept.yaml, scaffold.yaml, redirect.yaml

Each template adapts its strategy using `{% if attempt_count == 1 %}` conditionals.

## Common Development Tasks

### Testing the Prototype
The system is built in n8n, not as standalone code. To test:

1. **Setup n8n**:
   ```bash
   docker run -p 5678:5678 n8n
   # Or use n8n Cloud
   ```

2. **Import workflow**: Load `2-prototype/workflow.json` into n8n

3. **Configure credentials**: Add OpenAI API key in n8n settings

4. **Test webhook**: Use exemplar questions from `2-prototype/exemplars/questions.json`
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

### Modifying Prompts
Prompts are in `1-blueprint/prompts/*.yaml`. To modify:
1. Edit YAML file with new prompt text
2. Update corresponding n8n node in workflow
3. Test with exemplar questions to verify behavior
4. Document changes in `3-delivery/CHANGELOG.md`

### Modifying Verification Logic
To change answer verification (e.g., adjust 20% threshold):
1. Edit `2-prototype/functions/verify_answer.js`
2. Update the `closeThreshold` calculation (line 62)
3. Update corresponding n8n Function node
4. Test edge cases (see exemplars for test data)

### Adding New Categories
Not recommended for Phase 1. If needed in Phase 2:
1. Add new prompt template in `1-blueprint/prompts/`
2. Update Stage 2 classification logic
3. Add routing branch in n8n workflow
4. Create new Response Generation node
5. Add test cases to exemplars

## Performance Requirements

**Target latency**: ≤3.5 seconds per turn
**Actual average**: ~1.5 seconds

Breakdown:
- Session load (parallel): 50ms
- Stage 1 triage (parallel): 300ms
- Verification: 50ms
- Stage 2 classification: 200ms
- Response generation: 800ms
- Session save (async): 30ms

**Optimization strategies**:
- Run session load and Stage 1 triage in parallel
- Use GPT-4o-mini (not GPT-4) for speed
- Set max_tokens limits on LLM calls
- Use temperature 0.1 for triage (deterministic)
- Save session asynchronously after response sent

## API Contract

**Webhook**: `POST /webhook/tutor/message`

**Request**:
```json
{
  "student_id": "string",
  "session_id": "string",
  "message": "string",
  "current_problem": {
    "id": "string",
    "text": "string",
    "correct_answer": "string"
  }
}
```

**Response**:
```json
{
  "response": "string",
  "metadata": {
    "category": "correct|close|wrong_operation|conceptual_question|stuck|off_topic",
    "confidence": 0.0-1.0,
    "is_answer": boolean,
    "verification": {...},
    "attempt_count": number,
    "escalation_level": "probe|hint|teach",
    "latency_ms": number
  }
}
```

See `2-prototype/docs/API-SPEC.md` for complete specification.

## Important Constraints & Decisions

### Why n8n Instead of Code
- Rapid prototyping for POC (10-hour budget)
- Visual workflow easier for stakeholder demos
- Migration path to Node.js documented for Phase 2
- All logic in JavaScript functions is portable

### Why Two-Stage Triage
Cannot determine answer quality without first verifying the answer, but cannot verify until you know it's an answer attempt. Splitting into two stages solves this dependency.

### Why 20% Threshold for "Close"
Catches calculation errors (off-by-one, rounding) without conflating them with conceptual errors. Extensively tested with exemplar questions.

### Why Last 15 Turns
Balance between context (for natural conversation) and token cost/latency. 15 turns provides sufficient context for extended scaffolding sequences while keeping token costs manageable. More than 15 turns rarely adds value for elementary math problems - students needing more attempts should be escalated to human tutors.

### Why GPT-4o-mini
Meets latency requirements (~300ms for triage) and cost targets (~$0.0003 per turn) while maintaining classification accuracy. GPT-4 is overkill for this use case.

## Phase 2 Roadmap

Documented in `1-blueprint/Tutoring-Flow-Blueprint.md` section 10:
1. Knowledge base integration (RAG) for concept explanations
2. Multi-step problem decomposition (agents)
3. Tool use (calculator, graphing, worked examples)
4. Fine-tuned triage model (DSPy)
5. Curriculum integration & mastery tracking
6. Multi-language support
7. Migration from n8n to Node.js/Express

## Integration with MinS Platform

Three options documented in `2-prototype/docs/INTEGRATION.md`:
- **Option A**: Direct frontend to n8n webhook (quick MVP)
- **Option B**: Backend proxy (recommended, adds logging/analytics)
- **Option C**: Iframe embed (testing only)

Current problem data must come from MinS database. Session ID should be generated by MinS and reused for multi-turn conversations.

## Key References

- **Blueprint**: `1-blueprint/Tutoring-Flow-Blueprint.md` (10 pages, complete spec)
- **API Spec**: `2-prototype/docs/API-SPEC.md`
- **Integration**: `2-prototype/docs/INTEGRATION.md`
- **Deployment**: `2-prototype/docs/DEPLOYMENT.md`
- **Handoff**: `3-delivery/HANDOFF-CHECKLIST.md`
- **Limitations**: `3-delivery/KNOWN-LIMITATIONS.md`

## Notes for Future Development

- Do not modify the 6 core categories without stakeholder approval (pedagogically validated)
- All prompt changes should be tested against exemplar questions
- Maintain API contract backward compatibility (frontend depends on it)
- Document all architectural decisions in CHANGELOG.md
- The system is stateless per-request (all state in session object)
- Sessions expire after 30 minutes; this is intentional (not a bug)
- Verification can fail gracefully (returns error object, tutor asks for clarification)
