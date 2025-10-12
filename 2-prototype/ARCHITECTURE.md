# Stigmi AI Tutor Architecture

**Version**: 2.0 (Production-Ready Prototype)
**Last Updated**: October 12, 2025
**Status**: Production-ready single-problem workflow implemented

---

## Table of Contents

1. [Current Architecture](#1-current-architecture)
2. [Technical Implementation](#2-technical-implementation)
3. [Future: Multi-Problem Session Architecture](#3-future-multi-problem-session-architecture)

---

## 1. Current Architecture

### 1.1 High-Level Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          WEBHOOK / CHAT TRIGGER                               │
│  Input: {student_id, session_id, message, current_problem: {id, text, ans}}  │
└────────────────────────────────┬─────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   Normalize Input      │
                    │ (Chat/Webhook adapter) │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  Redis: Get Session    │
                    │  (Load or initialize)  │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │    Load Session        │
                    │  (Merge + validate)    │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ Prepare Agent Context  │
                    │ (Detect scaffolding)   │
                    └────────────┬───────────┘
                                 │
                ┌────────────────┴──────────────────┐
                │                                   │
                ▼                                   ▼
  ┌─────────────────────────┐      ┌───────────────────────────┐
  │ LLM: Extract Intent     │      │  Is Scaffolding Active?   │
  │  (Answer vs Question)   │      │                           │
  └───────────┬─────────────┘      └──────────┬────────────────┘
              │                               │
              ▼                               │ YES (scaffolding)
  ┌─────────────────────────┐                │
  │  Code: Verify Answer    │                │
  │  (20% threshold logic)  │                │
  └───────────┬─────────────┘                │
              │                               │
              ▼                               ▼
  ┌─────────────────────────┐      ┌─────────────────────────────┐
  │  Parse Classification   │      │        AI Agent             │
  │  (Merge LLM + code)     │      │  (Tool-based validation)    │
  └───────────┬─────────────┘      │                             │
              │                    │  Tools:                     │
              │                    │  - Verify Main Answer       │
              │                    │  - Validate Scaffolding     │
              │                    │                             │
              │                    │  Context: $json (workflow)  │
              │                    └─────────────┬───────────────┘
              │                                  │
              │                                  ▼
              │                    ┌─────────────────────────────┐
              │                    │   Parse Agent Output        │
              │                    │ (Strategy 0-5 extraction)   │
              │                    └─────────────┬───────────────┘
              │                                  │
              └──────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ Build Response Context │
                    │ (Format chat history)  │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   Route by Category    │
                    │  (6-way switch node)   │
                    └────────────┬───────────┘
                                 │
         ┌───────────┬───────────┼───────────┬───────────┬────────────┐
         │           │           │           │           │            │
         ▼           ▼           ▼           ▼           ▼            ▼
    ┌────────┐ ┌─────────┐ ┌────────┐ ┌──────────┐ ┌───────┐ ┌────────────┐
    │Correct │ │  Close  │ │ Wrong  │ │Conceptual│ │ Stuck │ │Off-Topic   │
    │(Teach  │ │ (Probe) │ │Operation│ │ (Teach)  │ (Scaf- │ │(Redirect)  │
    │ Back)  │ │         │ │(Clarify)│ │          │ fold)  │ │            │
    └───┬────┘ └────┬────┘ └────┬───┘ └─────┬────┘ └───┬───┘ └──────┬─────┘
        │           │           │           │          │            │
        │           │           │           │          │            │
        │           │           │           │          ├────────────┘
        │           │           │           │          │ (+ Scaffold Progress)
        └───────────┴───────────┴───────────┴──────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ Update Session & Format│
                    │  (State transitions)   │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  Redis: Save Session   │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   Webhook Response     │
                    │ {output, _debug, ...}  │
                    └────────────────────────┘
```

### 1.2 Core Architectural Principles

#### Two-Path Classification
- **Non-Scaffolding Path**: LLM extraction → Code verification → Classification
  - Fast, deterministic for numeric answers
  - Uses 20% threshold for "close" vs "wrong_operation"
- **Scaffolding Path**: AI Agent with tools
  - Semantic validation for conceptual answers
  - Tools read from workflow context (`$json`), NOT function parameters
  - Agent decides: main problem attempt vs scaffolding response

#### State Management
- **Scaffolding State**: `{active: bool, depth: number, last_question: string}`
- **Teach-Back State**: `{active: bool, awaiting_explanation: bool}`
- **Transitions**:
  - `stuck` (non-scaffolding) → scaffolding.active = true
  - `scaffold_progress` → depth++
  - `correct` (during scaffolding) → scaffolding.active = false
  - `correct` (non-teach-back) → teach_back.active = true

#### Session Persistence
- **Storage**: Redis with 30-minute TTL
- **Key**: `tutor_session:{session_id}`
- **Schema**:
  ```javascript
  {
    session_id: string,
    student_id: string,
    current_problem: {
      id: string,
      text: string,
      correct_answer: string,
      attempt_count: number,
      scaffolding: {...},
      teach_back: {...}
    },
    recent_turns: [{student_message, tutor_response, category, timestamp}], // Last 15
    stats: {total_turns, problems_attempted, problems_solved}
  }
  ```

---

## 2. Technical Implementation

### 2.1 Node-by-Node Breakdown

#### Entry Points
**Webhook Trigger** (line 268)
- Path: `POST /webhook/tutor/message`
- Schema validation: `{student_id, session_id, message, current_problem}`

**Chat Trigger** (line 5)
- Alternative entry for n8n chat interface
- Maps chat fields to webhook format

**Normalize Input** (line 286)
- Detects source (webhook/chat/unknown)
- Transforms to canonical format
- Adds metadata: `_source`, `_original_payload`

#### Session Management
**Redis: Get Session** (line 829)
- Loads existing session or returns null
- Key: `tutor_session:{session_id}`

**Load Session** (line 300)
- Parses Redis JSON or creates new session
- **Hybrid Memory**: On problem change, keeps last 3 turns from previous problem
- Validates required fields (defensive programming)
- Adds `_start_time` for latency tracking

**Prepare Agent Context** (line 207)
- Detects scaffolding mode heuristically (if state not set)
  - Checks for question marks + scaffolding keywords
- Detects teach-back mode (last category = correct + explanation keywords)
- Builds context object for downstream nodes

#### Classification Path: Non-Scaffolding
**LLM: Extract Intent & Value** (line 126)
- Model: GPT-4o-mini (fast, cost-effective)
- **Critical Instruction**: "Extract EXACTLY what student SAID, NOT what you think they MEANT"
- Handles written numbers: "one" → 1, "minus two" → -2
- Returns: `{is_answer: bool, category, extracted_value, confidence, reasoning}`

**Code: Verify Answer** (line 112)
- **20% Threshold Logic**:
  ```javascript
  diff = |student_value - correct_value|
  threshold = max(0.3, |correct_value * 0.2|)

  if diff < 0.001: "correct"
  elif diff <= threshold: "close"
  else: "wrong_operation"
  ```
- Handles edge cases: NaN, null, parse errors

**Parse Classification** (line 99)
- Merges LLM extraction with code verification
- Passes through non-answer categories unchanged

#### Classification Path: Scaffolding
**Switch: Scaffolding Active?** (line 56)
- Routes to AI Agent only if `is_scaffolding_active = true`
- Otherwise, routes to Format for Routing (non-scaffolding path)

**AI Agent** (line 220)
- Model: OpenAI Chat Model (GPT-4o-mini)
- **Prompt**: Two-step intelligent routing
  - STEP 1: Detect if student is answering main problem vs scaffolding question
  - STEP 2: Call appropriate tool
- **Tools**:
  - `verify_main_answer` - for main problem attempts
  - `validate_scaffolding` - for scaffolding responses
- **Memory**: Window Buffer Memory (last 15 turns per problem)
- **Output**: JSON with `{category, is_main_problem_attempt, confidence, reasoning}`

**Tool: Verify Main Answer** (line 179)
- **CRITICAL**: Reads from `$json.student_message` and `$json.current_problem.correct_answer`
- Does NOT access OpenAI function call parameters (n8n limitation)
- Same 20% threshold logic as Code: Verify Answer
- Returns string: "correct" | "close" | "wrong_operation"

**Tool: Validate Scaffolding** (line 193)
- Reads from `$json.student_message`, `$json.scaffolding_last_question`, `$json.current_problem.text`
- Returns JSON with validation guidelines for agent to evaluate
- Agent uses its LLM to determine if response is correct/partially_correct/incorrect

**Parse Agent Output** (line 240)
- **Strategy 0**: Check for `__structured__output` wrapper (n8n + OpenAI pattern)
  ```javascript
  if (agentData.text && typeof agentData.text === 'string') {
    parsed = JSON.parse(agentData.text);
    if (parsed.__structured__output?.category) {
      classification = parsed.__structured__output;
    }
  }
  ```
- **Strategies 1-5**: Fallback extraction patterns
  - Direct object with expected fields
  - Nested in 'output' field
  - Nested in 'text' field
  - Array format
  - OpenAI message.content format
- **Error Handling**: Returns fallback classification if all strategies fail

#### Response Generation
**Build Response Context** (line 254)
- Formats recent_turns as chat history string
- Merges classification + session context
- Passes `_session`, `_session_id`, `_start_time` for later nodes

**Route by Category** (line 537)
- 7-way switch based on `category` field
- Routes: correct, close, wrong_operation, conceptual_question, stuck, off_topic, scaffold_progress

**Response Nodes** (lines 567-797)
- Each uses GPT-4o-mini with tailored prompts
- **Response: Correct** (567): Celebrate + teach-back (ask for explanation)
- **Response: Close** (603): Gentle probe, escalate hints on attempt 3+
- **Response: Wrong Operation** (639): Clarify misconception, teach concept on attempt 3+
- **Response: Conceptual** (675): Teach with examples, end with check question
- **Response: Stuck** (711): Scaffold into smaller steps (INITIATE scaffolding)
- **Response: Off-Topic** (747): Politely redirect to problem
- **Response: Scaffold Progress** (783): Acknowledge + ask next scaffolding step

#### State Persistence
**Update Session & Format Response** (line 799)
- **State Transitions** (documented in code):
  - Scaffolding: stuck → active, scaffold_progress → depth++, correct → inactive
  - Teach-Back: correct → active, teach_back_explanation → inactive
- Increments `attempt_count` only for main problem attempts
- Adds turn to `recent_turns` (keep last 15)
- Updates `last_active`, `stats.total_turns`
- Returns `{output, _session_id, _session_for_redis, _debug}`

**Redis: Save Session** (line 857)
- Saves updated session to Redis
- TTL: 30 minutes (implicit, configurable in Redis)

**Webhook Response** (line 819)
- Returns entire JSON payload to client
- Includes `output` (tutor response), `_debug` (state transitions, classification)

### 2.2 Critical Implementation Details

#### Tool Parameter Passing (n8n Limitation)
**Problem**: n8n toolCode nodes cannot access OpenAI function call parameters directly.

**Solution**: Use workflow context (`$json`) instead.
- Prepare Agent Context builds comprehensive context object
- Tools read from `$json.student_message`, `$json.current_problem`, etc.
- Tool JSON schema is still needed (for OpenAI to understand tool purpose)

**Documentation**: See `BUG-FIX-N8N-TOOL-PARAMETERS.md` for full debugging journey.

#### Structured Output Parser (Removed)
**Problem**: Structured Output Parser rejected AI Agent output format.

**Solution**: Removed parser connection, rely on Parse Agent Output multi-strategy extraction.
- Strategy 0 handles `__structured__output` wrapper
- Fallback strategies handle other formats
- More flexible than rigid parser validation

#### Scaffolding Detection Heuristics
**Fallback Logic** (line 207):
If session state doesn't have scaffolding.active set, detect heuristically:
```javascript
const isScaffoldingQuestion =
  lastTutorMessage.includes('?') &&
  (lastTutorMessage.includes('what does') ||
   lastTutorMessage.includes('think about') ||
   lastTutorMessage.includes('how') ||
   lastTutorMessage.includes("let's start"))
```

This ensures scaffolding detection works even if state wasn't persisted correctly.

#### Hybrid Memory Management
When problem changes:
- Keep last 3 turns from previous problem (for conversational continuity)
- Mark them as `is_previous_problem: true`
- Reset `attempt_count`, scaffolding, teach-back states

This prevents abrupt context loss when advancing to next problem.

### 2.3 Performance Characteristics

**Target Latency**: ≤3.5 seconds per turn
**Actual Average**: ~1.5 seconds

**Breakdown**:
- Session load: 50ms
- LLM extraction: 300ms
- Code verification: 50ms
- Agent classification (scaffolding): 500ms
- Response generation: 800ms
- Session save: 30ms (async)

**Optimizations**:
- GPT-4o-mini (not GPT-4) for speed
- Max tokens limits on all LLM calls
- Temperature 0.2 for deterministic classification
- Parallel tool calls in AI Agent

---

## 3. Future: Multi-Problem Session Architecture

### 3.1 Problem Statement

**Current Limitation**: The existing workflow handles one problem at a time. Each webhook call is stateless except for session memory. To create an accurate tutoring session, we need:

1. **Pre-loaded Question Sequences**: A session should contain 5-10 problems upfront
2. **Adaptive Progression**: System decides when to advance based on mastery signals
3. **Session-Level Context**: Maintain context across multiple problems
4. **Progress Tracking**: Record performance, time-on-task, mastery per problem
5. **Session Analytics**: Generate post-session reports for teachers

### 3.2 Proposed Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                        SESSION INITIALIZATION                          │
│  POST /sessions                                                        │
│  {student_id, question_set_id, problem_ids: [p1, p2, ...]}           │
│  → Returns: {session_id, current_problem_index, status: "active"}    │
└─────────────────────────────────┬─────────────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │   Session Orchestrator      │
                    │  (New control plane node)   │
                    │                             │
                    │  - Load question sequence   │
                    │  - Track current index      │
                    │  - Decide when to advance   │
                    └──────────────┬──────────────┘
                                   │
                                   │ Delegates to existing workflow
                                   ▼
            ┌──────────────────────────────────────────────┐
            │                                              │
            │         EXISTING WORKFLOW (UNCHANGED)        │
            │  Handles single problem classification →    │
            │         response generation                  │
            │                                              │
            └──────────────────┬───────────────────────────┘
                               │
                               │ Returns classification + response
                               ▼
                ┌──────────────────────────────────────────┐
                │      Problem State Machine               │
                │  (New post-processing node)              │
                │                                          │
                │  Analyzes: attempt_count, category,      │
                │           confidence, time_elapsed       │
                │                                          │
                │  Signals:                                │
                │  - MASTERED: correct on 1st try          │
                │  - LEARNED: correct after scaffolding    │
                │  - STRUGGLING: 3+ attempts wrong         │
                │  - STUCK: scaffolding depth > 3          │
                │                                          │
                │  Actions:                                │
                │  - ADVANCE: Move to next problem         │
                │  - CONTINUE: Stay on current problem     │
                │  - INTERVENE: Alert teacher              │
                └──────────────┬───────────────────────────┘
                               │
                               ▼
                ┌──────────────────────────────────────────┐
                │   Update Session State                   │
                │                                          │
                │  If ADVANCE:                             │
                │  - Mark current problem complete         │
                │  - Increment current_problem_index       │
                │  - Preserve recent_turns (hybrid memory) │
                │  - Load next problem                     │
                │                                          │
                │  If CONTINUE:                            │
                │  - Update problem-level stats            │
                │  - Check for intervention triggers       │
                │                                          │
                │  Save to Redis + Database                │
                └──────────────┬───────────────────────────┘
                               │
                               ▼
                ┌──────────────────────────────────────────┐
                │        Session Analytics                 │
                │  (Background job / async webhook)        │
                │                                          │
                │  Metrics:                                │
                │  - problems_completed / total            │
                │  - mastery_rate (correct on 1st try)    │
                │  - scaffolding_effectiveness             │
                │  - avg_time_per_problem                  │
                │  - struggle_points (problem IDs)         │
                │                                          │
                │  Triggers:                               │
                │  - Session complete → POST to LMS        │
                │  - Student stuck → Real-time alert       │
                └──────────────────────────────────────────┘
```

### 3.3 Data Model Extensions

#### Session Schema (Extended)
```javascript
{
  session_id: string,
  student_id: string,
  question_set_id: string,
  status: "active" | "paused" | "completed",

  // NEW: Problem sequence management
  problem_sequence: [
    {
      problem_id: string,
      problem_text: string,
      correct_answer: string,
      index: number,
      status: "pending" | "in_progress" | "completed" | "skipped"
    }
  ],
  current_problem_index: number,

  // Existing: Current problem state (as is)
  current_problem: {
    id: string,
    text: string,
    correct_answer: string,
    attempt_count: number,
    time_started: timestamp,
    time_completed: timestamp | null,
    scaffolding: {...},
    teach_back: {...},

    // NEW: Problem-level analytics
    analytics: {
      first_attempt_category: string,
      total_attempts: number,
      scaffolding_depth_reached: number,
      time_spent_seconds: number,
      mastery_signal: "mastered" | "learned" | "struggling" | "stuck",
      hint_sequence: [string] // Tutor responses for replay
    }
  },

  // Existing: Conversation history (hybrid memory)
  recent_turns: [
    {
      student_message: string,
      tutor_response: string,
      category: string,
      timestamp: string,
      problem_id: string, // NEW: Track which problem this turn belongs to
      is_previous_problem: boolean
    }
  ],

  // NEW: Session-level analytics
  session_analytics: {
    total_time_seconds: number,
    problems_completed: number,
    problems_total: number,
    mastery_count: number,
    learned_count: number,
    struggling_count: number,
    scaffolding_invoked_count: number,
    avg_time_per_problem: number,
    struggle_problem_ids: [string]
  },

  // Existing: Stats
  stats: {
    total_turns: number,
    problems_attempted: number,
    problems_solved: number
  },

  created_at: timestamp,
  last_active: timestamp,
  completed_at: timestamp | null
}
```

#### Database Schema (PostgreSQL)
```sql
-- Sessions table
CREATE TABLE tutoring_sessions (
  session_id UUID PRIMARY KEY,
  student_id VARCHAR(255) NOT NULL,
  question_set_id VARCHAR(255) NOT NULL,
  status VARCHAR(20) NOT NULL, -- active, paused, completed
  current_problem_index INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  last_active TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP NULL,

  -- Denormalized analytics (for fast queries)
  problems_completed INT DEFAULT 0,
  problems_total INT NOT NULL,
  mastery_count INT DEFAULT 0,
  total_time_seconds INT DEFAULT 0,

  INDEX idx_student_status (student_id, status),
  INDEX idx_created_at (created_at DESC)
);

-- Problem attempts table (one row per problem in session)
CREATE TABLE problem_attempts (
  id SERIAL PRIMARY KEY,
  session_id UUID NOT NULL REFERENCES tutoring_sessions(session_id),
  problem_id VARCHAR(255) NOT NULL,
  problem_index INT NOT NULL,

  status VARCHAR(20) NOT NULL, -- pending, in_progress, completed, skipped

  -- Attempt tracking
  attempt_count INT DEFAULT 0,
  first_attempt_category VARCHAR(50) NULL,
  final_category VARCHAR(50) NULL,

  -- Scaffolding tracking
  scaffolding_invoked BOOLEAN DEFAULT FALSE,
  scaffolding_depth_reached INT DEFAULT 0,

  -- Timing
  time_started TIMESTAMP NULL,
  time_completed TIMESTAMP NULL,
  time_spent_seconds INT DEFAULT 0,

  -- Mastery signal
  mastery_signal VARCHAR(20) NULL, -- mastered, learned, struggling, stuck

  UNIQUE (session_id, problem_index),
  INDEX idx_session_problem (session_id, problem_index)
);

-- Turn history table (one row per conversation turn)
CREATE TABLE conversation_turns (
  id SERIAL PRIMARY KEY,
  session_id UUID NOT NULL REFERENCES tutoring_sessions(session_id),
  problem_id VARCHAR(255) NOT NULL,
  problem_index INT NOT NULL,

  student_message TEXT NOT NULL,
  tutor_response TEXT NOT NULL,
  category VARCHAR(50) NOT NULL,

  timestamp TIMESTAMP DEFAULT NOW(),

  INDEX idx_session_timestamp (session_id, timestamp DESC)
);
```

### 3.4 Integration Points

#### New Endpoints

**1. Initialize Session**
```
POST /sessions
Request:
{
  "student_id": "student_123",
  "question_set_id": "algebra_basics_set_1",
  "problem_ids": ["p1", "p2", "p3", "p4", "p5"]
}

Response:
{
  "session_id": "sess_abc123",
  "current_problem_index": 0,
  "current_problem": {
    "id": "p1",
    "text": "What is -3 + 5?",
    "correct_answer": "2"
  },
  "status": "active",
  "problems_total": 5
}
```

**2. Get Session Status**
```
GET /sessions/{session_id}
Response:
{
  "session_id": "sess_abc123",
  "status": "active",
  "current_problem_index": 2,
  "problems_completed": 2,
  "problems_total": 5,
  "session_analytics": {
    "mastery_count": 1,
    "learned_count": 1,
    "total_time_seconds": 420
  }
}
```

**3. Submit Turn (Modified Existing Endpoint)**
```
POST /webhook/tutor/message
Request:
{
  "session_id": "sess_abc123", // Links to session
  "student_id": "student_123",
  "message": "2",
  // current_problem is now loaded from session, not passed in request
}

Response:
{
  "output": "Perfect! Can you explain how you solved it?",
  "session_status": {
    "current_problem_index": 2, // Advanced to next problem
    "action": "ADVANCE", // or "CONTINUE"
    "problems_remaining": 3
  },
  "_debug": {
    "classification": {...},
    "mastery_signal": "mastered",
    "state_transitions": {...}
  }
}
```

**4. Complete Session**
```
POST /sessions/{session_id}/complete
Response:
{
  "session_id": "sess_abc123",
  "status": "completed",
  "session_report": {
    "problems_completed": 5,
    "mastery_count": 3,
    "learned_count": 2,
    "total_time_seconds": 1200,
    "avg_time_per_problem": 240,
    "struggle_problems": ["p4"]
  }
}
```

#### New Nodes in n8n Workflow

**Session Orchestrator Node** (Pre-workflow)
- Check if session exists
- Load current problem from `problem_sequence[current_problem_index]`
- Inject `current_problem` into workflow context
- Pass to existing Webhook Trigger

**Problem State Machine Node** (Post-workflow)
- Input: classification result from existing workflow
- Analyze mastery signal:
  ```javascript
  if (category === 'correct' && attempt_count === 1 && !is_scaffolding_active) {
    mastery_signal = 'mastered';
    action = 'ADVANCE';
  } else if (category === 'correct' && is_scaffolding_active) {
    mastery_signal = 'learned';
    action = 'ADVANCE';
  } else if (attempt_count >= 3 && category !== 'correct') {
    mastery_signal = 'struggling';
    action = 'CONTINUE'; // Maybe intervene
  } else if (scaffolding_depth > 3) {
    mastery_signal = 'stuck';
    action = 'INTERVENE';
  } else {
    action = 'CONTINUE';
  }
  ```
- Update `problem_attempts` table
- If ADVANCE: increment `current_problem_index`, load next problem

**Session Analytics Node** (Async)
- Runs in background (n8n webhook trigger on session complete)
- Aggregates data from `problem_attempts`, `conversation_turns`
- Generates session report
- Posts to LMS webhook

### 3.5 Adaptive Progression Logic

#### Mastery Signals
- **MASTERED**: Correct on 1st attempt, high confidence, no scaffolding → ADVANCE immediately
- **LEARNED**: Correct after scaffolding, shows understanding → ADVANCE after teach-back
- **STRUGGLING**: 3+ attempts, wrong category → CONTINUE, offer hint
- **STUCK**: Scaffolding depth > 3, no progress → INTERVENE (teacher alert) or SKIP

#### Problem Advancement Rules
1. **Rule 1 (Mastery)**: correct + attempt_count = 1 → ADVANCE
2. **Rule 2 (Learned)**: correct + scaffolding completed → ADVANCE
3. **Rule 3 (Teach-Back)**: If teach-back active, wait for explanation before ADVANCE
4. **Rule 4 (Timeout)**: If time_on_problem > 10 minutes → offer SKIP option
5. **Rule 5 (Stuck)**: If scaffolding_depth > 3 → INTERVENE or SKIP

#### Hybrid Memory Preservation
When advancing to next problem:
- Keep last 3 turns from previous problem (as current implementation does)
- Mark them as `is_previous_problem: true`
- This maintains conversational continuity ("Great! Now let's try a new one...")

### 3.6 Teacher Dashboard Integration

#### Real-Time Monitoring
- WebSocket connection to broadcast session progress
- Show current problem, attempt count, time elapsed
- Alert on STRUGGLING or STUCK signals

#### Post-Session Report
```javascript
{
  session_id: "sess_abc123",
  student_id: "student_123",
  question_set: "algebra_basics_set_1",

  summary: {
    problems_completed: 5,
    total_time: "20m 15s",
    mastery_rate: "60%", // 3/5 mastered
    scaffolding_rate: "40%" // 2/5 needed scaffolding
  },

  problem_breakdown: [
    {
      problem_id: "p1",
      text: "What is -3 + 5?",
      mastery_signal: "mastered",
      attempts: 1,
      time_spent: "1m 30s",
      scaffolding_used: false
    },
    {
      problem_id: "p2",
      text: "What is -7 + 3?",
      mastery_signal: "learned",
      attempts: 4,
      time_spent: "5m 45s",
      scaffolding_used: true,
      scaffolding_depth: 2,
      key_misconception: "Struggled with negative + negative vs negative + positive"
    }
    // ... more problems
  ],

  insights: {
    strengths: ["Quick on simple addition", "Good teach-back explanations"],
    weaknesses: ["Confused by double negatives", "Needs work on signed arithmetic"],
    recommended_next_steps: ["Practice negative + negative problems", "Review number line visuals"]
  }
}
```

### 3.7 Migration Path

#### Phase 1: Session Management (Week 1-2)
- Add `sessions` table, `problem_attempts` table
- Implement Session Orchestrator node
- Modify existing workflow to read `current_problem` from session context
- Test with single-problem sessions (backward compatible)

#### Phase 2: Problem State Machine (Week 3-4)
- Implement mastery signal logic
- Add Problem State Machine node
- Implement ADVANCE/CONTINUE/INTERVENE actions
- Test advancement logic with 2-3 problem sequences

#### Phase 3: Analytics & Reporting (Week 5-6)
- Implement session analytics aggregation
- Create teacher dashboard API endpoints
- Build post-session report generation
- Add real-time monitoring (optional)

#### Backward Compatibility
- Existing webhook API still works (creates single-problem session implicitly)
- Gradual migration: new sessions use full flow, old sessions continue as-is
- Feature flag to enable/disable session mode per student

---

## 4. Appendix

### 4.1 Key Files Reference
- `workflow-production-ready.json` - Main n8n workflow (1245 lines)
- `BUG-FIX-N8N-TOOL-PARAMETERS.md` - Tool parameter passing documentation
- `BUG-FIX-SCAFFOLDING-MAIN-ANSWER-IGNORED.md` - Agent routing fix
- `BUG-FIX-SCAFFOLDING-TEXT-NUMBERS.md` - Text number validation fix
- `BUG-FIX-WRITTEN-NUMBERS.md` - LLM extraction literal extraction fix

### 4.2 Related Documents
- `1-blueprint/Tutoring-Flow-Blueprint.md` - Original design specification
- `2-prototype/docs/API-SPEC.md` - Current API documentation
- `2-prototype/docs/INTEGRATION.md` - Frontend integration guide
- `3-delivery/KNOWN-LIMITATIONS.md` - Known constraints and limitations

### 4.3 Performance Benchmarks
- Average latency: 1.5s (target: <3.5s)
- Redis read: 10-20ms
- LLM extraction: 250-350ms
- AI Agent (scaffolding): 400-600ms
- Response generation: 700-900ms
- Redis write: 20-30ms

### 4.4 Version History
- **v1.0** (Oct 9, 2025): Initial prototype with 6 teaching categories
- **v1.1** (Oct 10, 2025): Added scaffolding support
- **v1.5** (Oct 11, 2025): Fixed tool parameter passing, text number validation
- **v2.0** (Oct 12, 2025): Removed Structured Output Parser, production-ready
- **v3.0** (Planned): Multi-problem session architecture (this document)

---

**Document Maintained By**: AI Development Team
**Last Review**: October 12, 2025
**Next Review**: When implementing v3.0 (multi-problem sessions)
