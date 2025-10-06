# System Architecture Diagrams

**AI Tutor POC - Visual Reference**

---

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     STUDENT INTERFACE                       │
│                                                             │
│  ┌─────────────────────┐                                   │
│  │  MinS Text Module   │                                   │
│  │  (React Component)  │                                   │
│  └──────────┬──────────┘                                   │
│             │                                               │
└─────────────┼───────────────────────────────────────────────┘
              │
              │ POST {student_id, session_id, message, problem}
              ↓
┌─────────────────────────────────────────────────────────────┐
│              MINS BACKEND (Optional Proxy)                  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  • Validate request                                  │  │
│  │  • Get current problem from DB                       │  │
│  │  • Call n8n webhook                                  │  │
│  │  • Log interaction to analytics                      │  │
│  │  • Return response                                   │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        │ POST to n8n
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                    n8n WORKFLOW ENGINE                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              ORCHESTRATION LAYER                     │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    │  │
│  │  │Webhook │→ │ Load   │→ │Triage  │→ │ Verify │    │  │
│  │  │Trigger │  │Session │  │ (LLM)  │  │(Math.js│    │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘    │  │
│  │       ↓                                    ↓         │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    │  │
│  │  │ Route  │→ │Generate│→ │ Update │→ │Response│    │  │
│  │  │6-way   │  │Response│  │Session │  │        │    │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ├────────────→ OpenAI API (GPT-4o-mini)
                    │              • Triage LLM
                    │              • Response generation
                    │
                    └────────────→ Redis (Session Storage)
                                   • Session state
                                   • 30-min TTL

```

---

## Detailed Workflow: Two-Stage Triage

```
Student Input: "-8"
Problem: "What is -3 + 5?"
    ↓
┌─────────────────────────────────────────────────────────────┐
│                    STAGE 1: INTENT DETECTION                │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ LLM Prompt:                                          │  │
│  │ "Is this an answer attempt or something else?"      │  │
│  │                                                      │  │
│  │ Input: "-8"                                          │  │
│  │ Problem: "What is -3 + 5?"                          │  │
│  │                                                      │  │
│  │ Output: {is_answer: true, confidence: 0.99}         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
         YES (is_answer)            NO (not answer)
                 │                         │
                 ↓                         ↓
┌────────────────────────────┐  ┌──────────────────────────┐
│   VERIFY ANSWER            │  │   STAGE 2b:              │
│                            │  │   NON-ANSWER INTENT      │
│  JavaScript math.js:       │  │                          │
│  evaluate("-8")            │  │  LLM Prompt:             │
│  vs                        │  │  "What type of           │
│  evaluate("2")             │  │   non-answer?"           │
│                            │  │                          │
│  Result:                   │  │  Categories:             │
│  {correct: false,          │  │  • conceptual_question   │
│   close: false,            │  │  • stuck                 │
│   student_value: -8}       │  │  • off_topic             │
│                            │  │                          │
└──────────┬─────────────────┘  └────────┬─────────────────┘
           │                              │
           ↓                              ↓
┌──────────────────────────┐  ┌──────────────────────────┐
│  STAGE 2a:               │  │  OUTPUT:                 │
│  ANSWER QUALITY          │  │  • Category              │
│                          │  │  • Confidence            │
│  Rule-based:             │  │                          │
│  if correct → "correct"  │  └────────┬─────────────────┘
│  if close → "close"      │           │
│  else → "wrong_operation"│           │
│                          │           │
│  Output: "wrong_operation│           │
└──────────┬───────────────┘           │
           │                            │
           └────────────┬───────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                    ROUTE TO RESPONSE                        │
│                                                             │
│  Category: "wrong_operation"                                │
│  → Select prompt: clarify.yaml                              │
│  → Generate response: "When we see +, are we adding or      │
│                        subtracting?"                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Session Memory Flow

```
Turn 1:
┌────────────────────────────────────────────────────────────┐
│ Session: sess_001                                          │
│ Problem: neg_add_1 ("What is -3 + 5?")                    │
│ Attempt count: 0                                           │
│ Recent turns: []                                           │
└────────────────────────────────────────────────────────────┘
    ↓ Student: "-8"
    ↓ Category: wrong_operation
    ↓ Response: "When we see +, are we adding or subtracting?"
    ↓
┌────────────────────────────────────────────────────────────┐
│ Session: sess_001                                          │
│ Problem: neg_add_1                                         │
│ Attempt count: 1 ← incremented                            │
│ Recent turns: [                                            │
│   {turn: 1, student: "-8", tutor: "When we see +...", } │
│ ]                                                          │
└────────────────────────────────────────────────────────────┘

Turn 2:
    ↓ Student: "adding"
    ↓ Category: stuck (not an answer)
    ↓ Response: "Right! Starting at -3, which way do we move?"
    ↓
┌────────────────────────────────────────────────────────────┐
│ Session: sess_001                                          │
│ Problem: neg_add_1                                         │
│ Attempt count: 1 ← NOT incremented (wasn't an answer)     │
│ Recent turns: [                                            │
│   {turn: 1, student: "-8", ...},                          │
│   {turn: 2, student: "adding", ...} ← added               │
│ ]                                                          │
└────────────────────────────────────────────────────────────┘

Turn 3:
    ↓ Student: "2"
    ↓ Category: correct
    ↓ Response: "Perfect! Can you explain how you got 2?"
    ↓
┌────────────────────────────────────────────────────────────┐
│ Session: sess_001                                          │
│ Problem: neg_add_1                                         │
│ Attempt count: 2 ← incremented (was an answer)            │
│ Recent turns: [                                            │
│   {turn: 1, student: "-8", ...},                          │
│   {turn: 2, student: "adding", ...},                      │
│   {turn: 3, student: "2", category: "correct", ...}       │
│ ]                                                          │
│ Stats: {problems_solved: 1} ← problem marked solved       │
└────────────────────────────────────────────────────────────┘
```

---

## Category Router (6-Way Switch)

```
                    After Triage
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
     │ correct │   │  close  │   │ wrong_  │
     │         │   │         │   │operation│
     └────┬────┘   └────┬────┘   └────┬────┘
          │             │             │
     ┌────▼────────────────────────────▼────┐
     │                                       │
┌────▼────┐  ┌─────────┐  ┌──────────┐
│conceptu-│  │  stuck  │  │off_topic │
│al_quest │  │         │  │          │
└────┬────┘  └────┬────┘  └────┬─────┘
     │            │            │
     └────────────┼────────────┘
                  │
          ┌───────▼─────────────┐
          │  Route to Prompt    │
          │  ┌────────────────┐ │
          │  │teach_back.yaml │ │
          │  │probe.yaml      │ │
          │  │clarify.yaml    │ │
          │  │concept.yaml    │ │
          │  │scaffold.yaml   │ │
          │  │redirect.yaml   │ │
          │  └────────────────┘ │
          └─────────┬───────────┘
                    │
          ┌─────────▼──────────┐
          │ Generate Response  │
          │ (LLM with prompt)  │
          └─────────┬──────────┘
                    │
                    ↓
              Tutor Response
```

---

## Escalation Strategy

```
Attempt Count → Teaching Strategy

Attempt 1:
┌──────────────────────────────────────┐
│ PROBE (Socratic Question)            │
│                                      │
│ "When we see +, are we adding        │
│  or subtracting?"                    │
│                                      │
│ Goal: Guide student to discover      │
└──────────────────────────────────────┘

Attempt 2:
┌──────────────────────────────────────┐
│ HINT (More Explicit)                 │
│                                      │
│ "Remember, + means we move RIGHT     │
│  on the number line. Starting at     │
│  -3, which way do we go?"            │
│                                      │
│ Goal: Provide clearer direction      │
└──────────────────────────────────────┘

Attempt 3+:
┌──────────────────────────────────────┐
│ TEACH (Direct Instruction)           │
│                                      │
│ "Let me show you: Start at -3.       │
│  Adding means move right. Count      │
│  with me: -3, -2, -1, 0, 1, 2.       │
│  We land on 2. Now try again."       │
│                                      │
│ Goal: Teach explicitly, then retry   │
└──────────────────────────────────────┘
```

---

## Data Flow: Request to Response

```
MinS Frontend
    │
    │ 1. Student types "-8"
    ↓
{
  student_id: "user123",
  session_id: "sess001",
  message: "-8",
  current_problem: {
    id: "neg_add_1",
    text: "What is -3 + 5?",
    correct_answer: "2"
  }
}
    │
    │ 2. POST to n8n webhook
    ↓
n8n Workflow
    │
    │ 3. Load session (Redis/memory)
    ↓
Session: {
  session_id: "sess001",
  current_problem: {...},
  attempt_count: 0,
  recent_turns: []
}
    │
    │ 4. Stage 1 Triage (LLM)
    ↓
{is_answer: true, confidence: 0.99}
    │
    │ 5. Verify (Math.js)
    ↓
{correct: false, close: false, student_value: -8}
    │
    │ 6. Stage 2a (Rules)
    ↓
category: "wrong_operation"
    │
    │ 7. Context Enrichment
    ↓
{
  category: "wrong_operation",
  attempt_count: 1,
  escalation_level: "probe"
}
    │
    │ 8. Generate Response (LLM with clarify.yaml)
    ↓
response: "When we see +, are we adding or subtracting?"
    │
    │ 9. Update Session
    ↓
Session (updated): {
  attempt_count: 1,
  recent_turns: [{...}]
}
    │
    │ 10. Return Response
    ↓
{
  response: "When we see +, are we adding or subtracting?",
  metadata: {
    category: "wrong_operation",
    confidence: 0.94,
    verification: {...},
    attempt_count: 1,
    latency_ms: 1450
  }
}
    │
    │ 11. Display in UI
    ↓
MinS Frontend shows tutor message
```

---

## Latency Breakdown

```
Total Turn: ~1.5 seconds

┌─────────────────────────────────────────────────────┐
│ Session Load (Redis)              50ms    █         │
│ Stage 1 Triage (LLM)             300ms    ████      │
│ Verification (Math.js)            50ms    █         │
│ Stage 2 Classification           200ms    ███       │
│ Response Generation (LLM)        800ms    ██████████│
│ Session Save (Redis async)        30ms    ▌         │
│ Overhead (network, processing)    70ms    █         │
├─────────────────────────────────────────────────────┤
│ TOTAL                           1500ms              │
└─────────────────────────────────────────────────────┘

Target: ≤3500ms
Actual: ~1500ms ✓ (57% faster than target)
```

---

## Production Architecture (Future)

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                        │
└───────────┬─────────────────────────────────────────────────┘
            │
      ┌─────┴─────┐
      │           │
   Node 1      Node 2      (n8n or Node.js instances)
      │           │
      └─────┬─────┘
            │
┌───────────┴─────────────────────────────────────────────────┐
│                     Shared Services                         │
│                                                             │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐            │
│  │  Redis   │  │ MongoDB   │  │  OpenAI API  │            │
│  │(Sessions)│  │(Analytics)│  │              │            │
│  └──────────┘  └───────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

**Version**: 1.0
**Last Updated**: October 10, 2025
**Purpose**: Visual reference for understanding system flow
