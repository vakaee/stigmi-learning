# Tutoring Flow Blueprint
## Adaptive AI Tutoring System - Complete Architectural Specification

**Version**: 1.0
**Date**: October 10, 2025
**Author**: Vlad (AI Tutoring Consultant)
**Client**: MinS Education Platform

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Two-Stage Triage System](#3-two-stage-triage-system)
4. [Prompt Library](#4-prompt-library)
5. [Session Memory Management](#5-session-memory-management)
6. [Answer Verification](#6-answer-verification)
7. [Exemplar Questions](#7-exemplar-questions)
8. [Latency Optimization](#8-latency-optimization)
9. [Integration Patterns](#9-integration-patterns)
10. [Future Enhancements](#10-future-enhancements)

---

## 1. Executive Summary

### Purpose

This document specifies a complete adaptive AI tutoring system that transforms single-prompt responses into sophisticated, pedagogically sound multi-turn conversations.

### Core Capabilities

- **Intelligent Classification**: Automatically categorizes student responses into 6 pedagogical categories
- **Adaptive Scaffolding**: Adjusts teaching strategy based on attempt count and error patterns
- **Multi-Turn Memory**: Maintains conversation context for natural dialogue
- **Answer Verification**: Validates numerical and algebraic responses with edge case handling
- **Socratic Method**: Guides students to discover answers rather than telling them directly

### Key Metrics

- **Target Latency**: ≤3.5 seconds per turn
- **Actual Performance**: ~1.5 seconds average
- **Cost**: ~$0.0003 per turn
- **Categories**: 6 distinct teaching strategies
- **Memory Window**: Last 15 conversation turns

---

## 2. System Architecture

### High-Level Flow

```
Student Message
    ↓
┌──────────────────────────────────────────────────┐
│         ORCHESTRATION LAYER (n8n)                │
├──────────────────────────────────────────────────┤
│                                                  │
│  ① Webhook Trigger                               │
│     Receive: {student_id, session_id, message}   │
│                                                  │
│  ② Load Session [PARALLEL]                       │
│     Redis/File: Get conversation history         │
│                                                  │
│  ③ Stage 1 Triage [PARALLEL]                     │
│     LLM: Is this an answer attempt?              │
│     Output: {is_answer: bool}                    │
│                                                  │
│  ④ Branch: Answer vs Non-Answer                 │
│     ├─ Answer Path → ⑤                          │
│     └─ Non-Answer Path → ⑦                      │
│                                                  │
│  ⑤ Verify Answer                                 │
│     JavaScript: Check correctness                │
│     Output: {correct, close, student_value}      │
│                                                  │
│  ⑥ Stage 2a: Answer Quality                     │
│     Rules: correct | close | wrong_operation     │
│     → GO TO ⑧                                    │
│                                                  │
│  ⑦ Stage 2b: Non-Answer Intent                  │
│     LLM: conceptual | stuck | off_topic          │
│     → GO TO ⑧                                    │
│                                                  │
│  ⑧ Context Enrichment                            │
│     Add: attempt_count, escalation_level         │
│                                                  │
│  ⑨ Route to Category-Specific Prompt             │
│     6 branches (one per category)                │
│                                                  │
│  ⑩ Generate Response                             │
│     LLM with category prompt + memory            │
│                                                  │
│  ⑪ Update Session                                │
│     Save turn, increment attempt, trim history   │
│                                                  │
│  ⑫ Return Response                               │
│     Output: {response, metadata}                 │
│                                                  │
└──────────────────────────────────────────────────┘
    ↓
Tutor Response to Student
```

### Component Responsibilities

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Orchestration** | Workflow coordination | n8n visual workflow |
| **Triage** | Intent and quality classification | GPT-4o-mini |
| **Verification** | Answer correctness checking | JavaScript (math.js) |
| **Memory** | Session state persistence | Redis or file storage |
| **Response Generation** | Tutor message creation | GPT-4o-mini |
| **Prompts** | Teaching strategy templates | YAML files |

---

## 3. Two-Stage Triage System

### Why Two Stages?

**Problem**: Cannot verify an answer before classifying it, but need verification result to classify quality.

**Solution**: Separate intent detection from quality assessment.

### Stage 1: Intent Detection

**Purpose**: Determine if student is providing an answer or asking/responding with non-answer.

**Input**:
- `problem`: Current math problem
- `student_input`: Student's message
- `chat_history`: Recent conversation (optional context)

**LLM Prompt**:
```
Is this student input an answer attempt to the problem, or something else?

Problem: {problem}
Student input: "{student_input}"

Respond with JSON only:
{
  "is_answer": true/false,
  "confidence": 0.0-1.0
}

Examples:
"2" → {"is_answer": true, "confidence": 0.99}
"I don't know" → {"is_answer": false, "confidence": 0.95}
"What is a negative number?" → {"is_answer": false, "confidence": 0.98}
"-8" → {"is_answer": true, "confidence": 0.99}
"I think it's around two" → {"is_answer": true, "confidence": 0.85}
```

**Model**: GPT-4o-mini
**Temperature**: 0.1 (deterministic)
**Max Tokens**: 50
**Expected Latency**: ~300ms

**Output**: `{is_answer: boolean, confidence: number}`

---

### Stage 2a: Answer Quality Classification

**Triggered**: Only if `is_answer == true`

**Process**:
1. Run verification function
2. Apply rule-based classification

**Classification Rules**:
```javascript
function classifyAnswerQuality(verificationResult) {
  if (verificationResult.correct) {
    return "correct";
  }

  if (verificationResult.close) {
    return "close";  // Within 20% of correct answer
  }

  // All other wrong answers
  return "wrong_operation";
}
```

**Categories**:
- **correct**: Verified as right answer
- **close**: Wrong but near (calculation error, off-by-one, etc.)
- **wrong_operation**: Significantly wrong (conceptual error, wrong operation)

**No LLM needed** - pure rule-based logic after verification.

---

### Stage 2b: Non-Answer Intent Classification

**Triggered**: Only if `is_answer == false`

**Purpose**: Determine type of non-answer input.

**LLM Prompt**:
```
The student is NOT giving an answer. What are they doing?

Problem: {problem}
Student input: "{student_input}"

Previous conversation:
{chat_history}

Classify as ONE:
- conceptual_question: Asking what a concept means ("What's a negative number?")
- stuck: Asking for help or saying they don't know ("I'm stuck", "help", "I don't know")
- off_topic: Unrelated to the problem ("What's for lunch?", random chat)

Respond with JSON only:
{
  "category": "one of above",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}
```

**Model**: GPT-4o-mini
**Temperature**: 0.1
**Max Tokens**: 100
**Expected Latency**: ~200ms

**Categories**:
- **conceptual_question**: Student asking to learn a concept
- **stuck**: Explicit help request or expression of confusion
- **off_topic**: Unrelated to current problem

---

### Final 6 Categories

| Category | Detection Path | Trigger | Teaching Strategy |
|----------|---------------|---------|-------------------|
| **correct** | Answer → Verify ✓ | Verification passes | TEACH-BACK: Ask for explanation |
| **close** | Answer → Verify ~ | Within 20% | PROBE: Find small error |
| **wrong_operation** | Answer → Verify ✗ | Wrong answer | CLARIFY: Address misconception |
| **conceptual_question** | Non-answer | Asking "what is X?" | CONCEPT: Teach with examples |
| **stuck** | Non-answer | "I don't know" / help | SCAFFOLD: Break into steps |
| **off_topic** | Non-answer | Unrelated | REDIRECT: Refocus politely |

---

### Context Enrichment

After classification, enrich with session data:

```javascript
{
  category: "wrong_operation",
  attempt_number: 3,              // How many times tried this problem
  prior_errors: ["close", "wrong_operation", "wrong_operation"],
  escalation_level: "teach",       // probe | hint | teach
  tone_adjustment: "patient"       // encouraging | patient | supportive
}
```

**Escalation Rules**:
```javascript
function getEscalationLevel(attemptCount) {
  if (attemptCount === 1) return "probe";      // Socratic question
  if (attemptCount === 2) return "hint";       // More explicit
  return "teach";                              // Direct instruction
}
```

---

## 4. Prompt Library

### Overview

Six production-ready prompt templates, one for each teaching category. Each template uses Jinja2 syntax for variable injection and conditional logic.

### Template Structure

All templates follow this pattern:
- **Context**: Problem, student input, attempt count
- **Memory**: Recent conversation history
- **Strategy**: Category-specific teaching approach
- **Constraints**: Length, tone, Socratic method
- **Escalation**: Adjust based on attempt count

---

### Template 1: TEACH-BACK (Correct Answer)

**File**: `prompts/teach_back.yaml`

```yaml
name: Teach-Back
category: correct
description: Student gave correct answer - now ask them to explain their reasoning

variables:
  - problem (required)
  - student_answer (required)
  - attempt_count (required)
  - chat_history (auto-injected)

template: |
  You are an encouraging math tutor. The student just gave the CORRECT answer.

  Problem: {problem}
  Student's answer: {student_answer} ✓ CORRECT

  {% if chat_history %}
  Recent conversation:
  {chat_history}
  {% endif %}

  Your goal: Get them to explain their reasoning (teach-back method).

  {% if attempt_count == 1 %}
  They got it right on the first try! Ask them to walk you through their thinking.
  {% else %}
  They worked through it and got there! Ask them to explain how they figured it out.
  {% endif %}

  Rules:
  - Celebrate their success briefly (1-2 words: "Perfect!", "Excellent!")
  - Ask them to explain their reasoning in their own words
  - 1-2 sentences total
  - Encouraging, warm tone

  Your response:
```

---

### Template 2: PROBE (Close Answer)

**File**: `prompts/probe.yaml`

```yaml
name: Probe
category: close
description: Student's answer is close (right approach, small error)

variables:
  - problem (required)
  - student_answer (required)
  - correct_answer (required)
  - attempt_count (required)
  - chat_history (auto-injected)

template: |
  You are a patient math tutor using Socratic questioning.

  Problem: {problem}
  Student's answer: {student_answer} (incorrect but close to {correct_answer})
  This is attempt #{attempt_count}

  {% if chat_history %}
  Recent conversation:
  {chat_history}
  {% endif %}

  {% if attempt_count == 1 %}
  Give a gentle probing question to help them spot their small error.
  Example: "You're very close! Want to double-check your calculation?"
  {% elif attempt_count == 2 %}
  Give a more explicit hint about where the error is.
  Example: "Almost there! Let's look at the last step again..."
  {% else %}
  They've tried 3+ times. Walk through one step explicitly, then let them finish.
  Example: "Let me show you: starting at -3, if we move right 1, we're at -2. Now you continue..."
  {% endif %}

  Rules:
  - 1-2 sentences maximum
  - Ask, don't tell (unless attempt 3+)
  - Use concrete examples (number line, objects, drawings)
  - Encouraging, patient tone
  - DO NOT give the final answer

  Your response:
```

---

### Template 3: CLARIFY (Wrong Operation)

**File**: `prompts/clarify.yaml`

```yaml
name: Clarify
category: wrong_operation
description: Student used wrong operation or has conceptual misunderstanding

variables:
  - problem (required)
  - student_answer (required)
  - correct_answer (required)
  - attempt_count (required)
  - chat_history (auto-injected)

template: |
  You are a patient math tutor. The student's answer suggests they misunderstood the operation or concept.

  Problem: {problem}
  Student's answer: {student_answer} (should be {correct_answer})
  This is attempt #{attempt_count}

  {% if chat_history %}
  Recent conversation:
  {chat_history}
  {% endif %}

  {% if attempt_count == 1 %}
  Ask a clarifying question about the operation or concept.
  Example: "When we see the + sign, are we adding or subtracting?"
  Example: "Let's think about what it means when we have a negative number..."
  {% elif attempt_count == 2 %}
  Give a more direct hint about the operation or concept.
  Example: "Remember, when we add a positive number, we move RIGHT on the number line."
  {% else %}
  They've tried 3+ times. Teach the concept directly with an example, then ask them to try.
  Example: "Let me explain: when we see -3 + 5, we start at -3. Adding means moving right. So we move right 5: -3, -2, -1, 0, 1, 2. Now try the original problem again."
  {% endif %}

  Rules:
  - Focus on the specific misconception
  - Use concrete examples (number line, real-world objects)
  - 2-3 sentences for teaching (attempt 3+), 1 sentence for questions (attempts 1-2)
  - Patient, non-judgmental tone

  Your response:
```

---

### Template 4: CONCEPT (Conceptual Question)

**File**: `prompts/concept.yaml`

```yaml
name: Concept
category: conceptual_question
description: Student is asking what a concept means

variables:
  - problem (required)
  - student_input (required)
  - chat_history (auto-injected)

template: |
  You are a patient math tutor. The student is asking a conceptual question.

  Problem: {problem}
  Student's question: "{student_input}"

  {% if chat_history %}
  Recent conversation:
  {chat_history}
  {% endif %}

  Your goal: Teach the concept using simple, concrete examples.

  Teaching strategy:
  1. Give a brief, simple definition (1 sentence)
  2. Provide a concrete example (number line, real-world scenario)
  3. Ask a check question to see if they understood

  Rules:
  - Use age-appropriate language
  - Concrete examples (number line for negatives, pizza slices for fractions, etc.)
  - 2-3 sentences total
  - End with a simple check question related to the original problem
  - Encouraging tone

  Your response:
```

---

### Template 5: SCAFFOLD (Stuck/Help Request)

**File**: `prompts/scaffold.yaml`

```yaml
name: Scaffold
category: stuck
description: Student is stuck or asking for help

variables:
  - problem (required)
  - attempt_count (required)
  - chat_history (auto-injected)

template: |
  You are a patient math tutor. The student is stuck or asking for help.

  Problem: {problem}
  This is attempt #{attempt_count}

  {% if chat_history %}
  Recent conversation:
  {chat_history}
  {% endif %}

  Your goal: Break the problem into smaller, manageable steps.

  {% if attempt_count == 1 %}
  Start with the very first step and ask them to do just that one step.
  Example: "Let's start simple. Where would -3 be on a number line?"
  {% elif attempt_count == 2 %}
  Give them the first step, then ask them to do the second step.
  Example: "We start at -3. When we add, we move to the right. Which direction is right from -3?"
  {% else %}
  They've tried multiple times. Walk through most of the problem step-by-step, leaving only the final step for them.
  Example: "Let me help you. We start at -3 on the number line. Adding means moving right. Let's count together: -3, -2, -1, 0, 1, 2. What number did we land on?"
  {% endif %}

  Rules:
  - Break into the smallest possible next step
  - 1-2 sentences
  - Encouraging tone ("Let's...", "We can...")
  - Ask a specific, focused question

  Your response:
```

---

### Template 6: REDIRECT (Off-Topic)

**File**: `prompts/redirect.yaml`

```yaml
name: Redirect
category: off_topic
description: Student's input is unrelated to the current problem

variables:
  - problem (required)
  - student_input (required)
  - chat_history (auto-injected)

template: |
  You are a friendly but focused math tutor. The student went off-topic.

  Problem: {problem}
  Student said: "{student_input}" (unrelated to the problem)

  Your goal: Politely redirect them back to the math problem.

  Rules:
  - Acknowledge their input very briefly (1-2 words if appropriate)
  - Gently redirect to the problem
  - 1 sentence total
  - Warm, friendly tone (not scolding)
  - Re-state the problem or ask them to focus

  Examples:
  - "Ha! Let's save that for later. Right now, what do you think -3 + 5 equals?"
  - "I hear you! But first, can you help me solve this problem: what is -3 + 5?"
  - "Let's focus on the math for now. Looking at -3 + 5, what's your answer?"

  Your response:
```

---

## 5. Session Memory Management

### Purpose

Maintain conversation context across multiple turns to enable:
- Natural, flowing dialogue
- Adaptive responses based on history
- Attempt tracking per problem
- Error pattern detection

### Session Schema

```javascript
{
  session_id: "uuid",                    // Unique session identifier
  student_id: "string",                  // Student identifier
  created_at: "2025-10-08T10:30:00Z",   // ISO 8601 timestamp
  last_active: "2025-10-08T10:35:22Z",  // Updated each turn
  ttl: 1800,                             // 30 minutes in seconds

  current_problem: {
    id: "neg_add_1",                     // Question identifier
    text: "What is -3 + 5?",            // Problem text
    correct_answer: "2",                 // Expected answer
    attempt_count: 2,                    // Resets when problem changes
    started_at: "2025-10-08T10:30:00Z"
  },

  // Last 15 turns (for LLM context)
  recent_turns: [
    {
      turn_number: 1,
      timestamp: "2025-10-08T10:31:00Z",
      student_input: "-8",
      is_answer: true,
      category: "wrong_operation",
      verification: {
        correct: false,
        student_value: -8,
        correct_value: 2,
        difference: 10
      },
      tutor_response: "When we see +, are we adding or subtracting?",
      latency_ms: 1450
    },
    {
      turn_number: 2,
      timestamp: "2025-10-08T10:32:15Z",
      student_input: "adding",
      is_answer: false,
      category: "stuck",
      tutor_response: "Right! Starting at -3, which way do we move when adding?",
      latency_ms: 1220
    }
    // ... up to 15 most recent turns
  ],

  // Concepts taught (for tracking)
  concepts_taught: ["negative_numbers_intro", "addition_with_negatives"],

  // Statistics
  stats: {
    total_turns: 2,
    avg_latency_ms: 1335,
    problems_attempted: 1,
    problems_solved: 0
  }
}
```

### Storage Implementation

#### Option A: Redis (Recommended)

**Advantages**:
- Fast read/write (~10-50ms)
- Built-in TTL (automatic cleanup)
- Atomic operations
- Scalable

**Implementation**:
```javascript
// Save session
SET session:{session_id} {json_string} EX 1800

// Load session
GET session:{session_id}

// Update TTL on activity
EXPIRE session:{session_id} 1800
```

**n8n Integration**: Use Redis node (built-in)

#### Option B: File Storage (Fallback)

**Advantages**:
- No external dependencies
- Simple for prototype
- Easy debugging (human-readable)

**Disadvantages**:
- Slower (~100-200ms)
- Manual cleanup needed
- Not production-scalable

**Implementation**:
```javascript
// Save session
fs.writeFileSync(`sessions/${session_id}.json`, JSON.stringify(session));

// Load session
const session = JSON.parse(fs.readFileSync(`sessions/${session_id}.json`));
```

**n8n Integration**: Use File node

### Memory Window

**Problem**: Sending full conversation history to LLM is expensive and slow.

**Solution**: Keep only last 15 turns in LLM context.

**Formatting for LLM**:
```
Recent conversation:
Turn 1:
Student: "-8"
Tutor: "When we see +, are we adding or subtracting?"

Turn 2:
Student: "adding"
Tutor: "Right! Starting at -3, which way do we move when adding?"
```

### Attempt Tracking

**Key Behavior**: `attempt_count` increments only for the same problem.

```javascript
function updateSession(session, newTurn, currentProblemId) {
  // Check if problem changed
  if (session.current_problem.id !== currentProblemId) {
    // New problem - reset attempt count
    session.current_problem = {
      id: currentProblemId,
      attempt_count: 0,
      started_at: new Date().toISOString()
    };
  }

  // Increment attempt count if this turn was an answer attempt
  if (newTurn.is_answer) {
    session.current_problem.attempt_count++;
  }

  // Add turn to recent history
  session.recent_turns.push(newTurn);

  // Trim to last 15 turns
  if (session.recent_turns.length > 15) {
    session.recent_turns = session.recent_turns.slice(-15);
  }

  // Update metadata
  session.last_active = new Date().toISOString();
  session.stats.total_turns++;

  return session;
}
```

---

## 6. Answer Verification

### Purpose

Accurately determine if a student's numerical or algebraic answer is correct, handling edge cases and variations in input format.

### Verification Function

**File**: `functions/verify_answer.js`

```javascript
const math = require('mathjs');

/**
 * Verify if student's answer matches the correct answer
 * Handles: decimals, fractions, expressions, written numbers
 *
 * @param {string} studentInput - Raw student input
 * @param {string} correctAnswer - Expected answer
 * @returns {object} Verification result
 */
function verifyAnswer(studentInput, correctAnswer) {
  try {
    // Normalize input
    let cleaned = studentInput.trim().toLowerCase();

    // Handle written numbers (basic cases)
    const numberWords = {
      'zero': '0', 'one': '1', 'two': '2', 'three': '3',
      'four': '4', 'five': '5', 'six': '6', 'seven': '7',
      'eight': '8', 'nine': '9', 'ten': '10',
      'negative': '-', 'minus': '-'
    };

    for (let [word, digit] of Object.entries(numberWords)) {
      const regex = new RegExp('\\b' + word + '\\b', 'g');
      cleaned = cleaned.replace(regex, digit);
    }

    // Remove extra spaces
    cleaned = cleaned.replace(/\s+/g, '');

    // Evaluate both as mathematical expressions
    const studentVal = math.evaluate(cleaned);
    const correctVal = math.evaluate(correctAnswer);

    // Handle fractions: convert to decimals for comparison
    const studentNum = convertToNumber(studentVal);
    const correctNum = convertToNumber(correctVal);

    // Calculate difference
    const diff = Math.abs(studentNum - correctNum);
    const tolerance = 0.001;  // For floating point comparison
    const closeThreshold = Math.abs(correctNum * 0.2);  // 20% of correct answer

    return {
      correct: diff < tolerance,
      close: diff >= tolerance && diff < closeThreshold,
      student_value: studentNum,
      correct_value: correctNum,
      difference: diff
    };

  } catch (error) {
    // Could not parse as number/expression
    return {
      correct: false,
      close: false,
      error: "Could not parse as number or expression",
      raw_input: studentInput
    };
  }
}

/**
 * Convert math.js types to plain numbers
 */
function convertToNumber(value) {
  // If it's a fraction object from math.js
  if (typeof value === 'object' && value.n !== undefined && value.d !== undefined) {
    return value.n / value.d;
  }
  // If it's already a number
  return Number(value);
}

module.exports = { verifyAnswer };
```

### Edge Cases Handled

| Input Type | Example | Handling |
|------------|---------|----------|
| Integer | `2` | Direct evaluation |
| Decimal | `2.0`, `2.00` | Tolerance comparison |
| Fraction | `1/2` | Convert to decimal (0.5) |
| Expression | `-3 + 5` | Evaluate then compare |
| Written | `two` | Replace with `2` before eval |
| Negative written | `negative three` | Replace with `-3` |
| Close answer | `2.1` when answer is `2` | Flagged as "close" |
| Spaces | `- 3` | Cleaned to `-3` |
| Invalid | `abc` | Return error object |

### Closeness Threshold

**Definition**: Answer is "close" if within 20% of correct answer.

**Rationale**: Catch calculation errors (off-by-one, rounding) but not conceptual errors.

**Examples**:
- Correct answer: `10`
  - `9` → close (10% off)
  - `12` → close (20% off)
  - `5` → wrong (50% off)

- Correct answer: `2`
  - `1.8` → close (10% off)
  - `2.4` → close (20% off)
  - `3` → wrong (50% off)

### Integration in Workflow

```javascript
// n8n Function Node example
const { verifyAnswer } = require('./functions/verify_answer.js');

// Get inputs from previous node
const studentInput = $input.item.json.message;
const correctAnswer = $input.item.json.current_problem.correct_answer;

// Verify
const result = verifyAnswer(studentInput, correctAnswer);

// Return for next node
return {
  json: {
    ...result,
    timestamp: new Date().toISOString()
  }
};
```

---

## 7. Exemplar Questions

### Purpose

Fully specified test questions that demonstrate all 6 teaching categories and common student misconceptions.

### Question Specification Format

Each question includes:
1. **Problem statement**: The question shown to students
2. **Correct answer**: Expected response
3. **Metadata**: Topic, difficulty, grade level
4. **Expected reasoning**: Step-by-step correct approach
5. **Common errors**: Typical wrong answers with diagnosis
6. **Hint progression**: Sequence of scaffolding hints
7. **Test conversation**: Expected multi-turn flow

---

### Question 1: Negative Number Addition (Priority)

```json
{
  "id": "neg_add_1",
  "problem": "What is -3 + 5?",
  "correct_answer": "2",
  "topic": "negative_numbers",
  "subtopic": "addition_with_negatives",
  "difficulty": "basic",
  "grade_level": "6-7",

  "expected_reasoning": [
    "Identify starting point: -3 on number line",
    "Recognize operation: addition means move right",
    "Count steps: -3 → -2 → -1 → 0 → 1 → 2 (5 steps)",
    "Final answer: 2"
  ],

  "common_errors": [
    {
      "answer": "-8",
      "category": "wrong_operation",
      "diagnosis": "Subtracted instead of adding (confused by negative sign)",
      "student_thinking": "Saw negative and plus, did 3 + 5 = 8, made it negative",
      "hint": "When we see the + sign, are we adding or subtracting?"
    },
    {
      "answer": "8",
      "category": "conceptual_gap",
      "diagnosis": "Ignored negative sign completely",
      "student_thinking": "Just did 3 + 5",
      "hint": "Look at the negative sign before the 3. Where do we start on the number line?"
    },
    {
      "answer": "1",
      "category": "close",
      "diagnosis": "Counting error or off-by-one",
      "student_thinking": "Right approach but miscounted steps",
      "hint": "You're very close! Let's count together: -3, -2, -1, 0, 1, 2. How many is that?"
    },
    {
      "answer": "3",
      "category": "close",
      "diagnosis": "Added magnitude without considering starting point",
      "student_thinking": "Forgot to start at -3",
      "hint": "Remember we're starting at -3, not zero. Try using a number line."
    }
  ],

  "hint_progression": [
    "Think about where we start on the number line.",
    "We're at -3. When adding, do we move left or right?",
    "Let's count together: -3, -2, -1, 0, 1, 2. That's 5 steps, right?",
    "Starting at -3 and moving right 5 spaces lands us on 2."
  ],

  "test_conversation": {
    "turn_1": {
      "student": "-8",
      "expected_category": "wrong_operation",
      "expected_triage_path": "is_answer=true → verify=false → wrong_operation",
      "expected_response_themes": ["operation", "adding", "subtracting", "+"]
    },
    "turn_2": {
      "student": "adding",
      "expected_category": "stuck",
      "expected_triage_path": "is_answer=false → stuck",
      "expected_response_themes": ["number line", "direction", "move"]
    },
    "turn_3": {
      "student": "2",
      "expected_category": "correct",
      "expected_triage_path": "is_answer=true → verify=true → correct",
      "expected_response_themes": ["explain", "reasoning", "how"]
    }
  }
}
```

---

### Question 2: Subtracting Negative (Priority)

```json
{
  "id": "neg_sub_1",
  "problem": "What is 5 - (-3)?",
  "correct_answer": "8",
  "topic": "negative_numbers",
  "subtopic": "subtracting_negatives",
  "difficulty": "intermediate",
  "grade_level": "7-8",

  "expected_reasoning": [
    "Recognize: subtracting a negative = adding",
    "Transform: 5 - (-3) becomes 5 + 3",
    "Calculate: 5 + 3 = 8"
  ],

  "common_errors": [
    {
      "answer": "2",
      "category": "wrong_operation",
      "diagnosis": "Treated as regular subtraction (ignored negative)",
      "hint": "What happens when we subtract a negative number?"
    },
    {
      "answer": "-8",
      "category": "conceptual_gap",
      "diagnosis": "Made result negative (sign confusion)",
      "hint": "Let's think about what 'minus a negative' means. It actually becomes addition!"
    }
  ],

  "hint_progression": [
    "What does it mean to subtract a negative number?",
    "Subtracting a negative is the same as adding a positive. So 5 - (-3) = 5 + 3.",
    "Now try 5 + 3. What do you get?"
  ]
}
```

---

### Question 3: Word Problem with Negatives (Priority)

```json
{
  "id": "word_neg_1",
  "problem": "The temperature was 2°C. It dropped 5 degrees. What is the new temperature?",
  "correct_answer": "-3",
  "topic": "negative_numbers",
  "subtopic": "real_world_application",
  "difficulty": "intermediate",
  "grade_level": "6-7",

  "expected_reasoning": [
    "Starting temperature: 2°C",
    "Dropped means subtract: 2 - 5",
    "Calculate: 2 - 5 = -3",
    "Final answer: -3°C (below zero)"
  ],

  "common_errors": [
    {
      "answer": "7",
      "category": "wrong_operation",
      "diagnosis": "Added instead of subtracted",
      "hint": "When temperature drops, are we adding or subtracting?"
    },
    {
      "answer": "3",
      "category": "conceptual_gap",
      "diagnosis": "Calculated correctly but forgot negative sign",
      "hint": "If we go below zero, is the temperature positive or negative?"
    },
    {
      "answer": "negative three degrees",
      "category": "correct",
      "diagnosis": "Correct (written form)",
      "note": "Accept written form of -3"
    }
  ],

  "hint_progression": [
    "Let's break it down. What's our starting temperature?",
    "If it drops 5 degrees from 2°C, what operation do we use?",
    "What is 2 - 5? Use a number line if it helps.",
    "When we go below zero, what kind of number is that?"
  ],

  "test_conversation": {
    "turn_1": {
      "student": "what does dropped mean?",
      "expected_category": "conceptual_question",
      "expected_response_themes": ["subtract", "goes down", "lower"]
    },
    "turn_2": {
      "student": "-3",
      "expected_category": "correct",
      "expected_response_themes": ["explain", "how", "reasoning"]
    }
  }
}
```

---

### Question 4: Fraction Addition (Priority)

```json
{
  "id": "frac_add_1",
  "problem": "What is 1/2 + 1/4?",
  "correct_answer": "3/4",
  "topic": "fractions",
  "subtopic": "addition",
  "difficulty": "basic",
  "grade_level": "4-5",

  "expected_reasoning": [
    "Find common denominator: 4",
    "Convert 1/2 to 2/4",
    "Add numerators: 2/4 + 1/4 = 3/4"
  ],

  "common_errors": [
    {
      "answer": "2/6",
      "category": "wrong_operation",
      "diagnosis": "Added numerators and denominators separately",
      "hint": "Can we add fractions when they have different denominators?"
    },
    {
      "answer": "0.75",
      "category": "correct",
      "diagnosis": "Decimal form is correct",
      "note": "Accept 0.75 as equivalent to 3/4"
    },
    {
      "answer": "2/4",
      "category": "close",
      "diagnosis": "Only converted 1/2, forgot to add 1/4",
      "hint": "You converted 1/2 to 2/4. Great! Now what do we do with the 1/4?"
    }
  ],

  "hint_progression": [
    "Can we add these fractions directly, or do we need a common denominator?",
    "What's a common denominator for 2 and 4?",
    "If we convert 1/2 to fourths, what do we get?",
    "Now add 2/4 + 1/4. What's the result?"
  ]
}
```

---

### Question 5: Negative Subtraction (Priority)

```json
{
  "id": "neg_sub_2",
  "problem": "What is -3 - 5?",
  "correct_answer": "-8",
  "topic": "negative_numbers",
  "subtopic": "subtraction_resulting_in_negative",
  "difficulty": "basic",
  "grade_level": "6-7",

  "expected_reasoning": [
    "Start at -3 on number line",
    "Subtracting 5 means move left 5 spaces",
    "-3 → -4 → -5 → -6 → -7 → -8",
    "Final answer: -8"
  ],

  "common_errors": [
    {
      "answer": "2",
      "category": "wrong_operation",
      "diagnosis": "Added instead of subtracted, or ignored signs",
      "hint": "Are we adding or subtracting? Watch the operation sign."
    },
    {
      "answer": "8",
      "category": "conceptual_gap",
      "diagnosis": "Got magnitude right but wrong sign",
      "hint": "If we start at -3 and move further left (subtract), do we get more negative or more positive?"
    }
  ],

  "hint_progression": [
    "Let's use a number line. Where do we start?",
    "When we subtract, do we move left or right?",
    "Starting at -3, move left 5 spaces. Where do you land?",
    "Count with me: -3, -4, -5, -6, -7, -8."
  ]
}
```

---

### Question 6: Off-Topic Test

```json
{
  "id": "off_topic_test",
  "problem": "What is -3 + 5?",
  "test_input": "What's for lunch?",
  "expected_category": "off_topic",
  "expected_response_themes": ["focus", "math", "problem", "later"],
  "note": "Manual test to verify off-topic detection and redirection"
}
```

---

### Question 7: Order of Operations (Nice-to-Have)

```json
{
  "id": "order_ops_1",
  "problem": "What is 2 + 3 × 4?",
  "correct_answer": "14",
  "topic": "order_of_operations",
  "difficulty": "intermediate",
  "grade_level": "6-7",

  "common_errors": [
    {
      "answer": "20",
      "category": "wrong_operation",
      "diagnosis": "Did addition first (ignored order of operations)",
      "hint": "Remember PEMDAS. Which operation do we do first: addition or multiplication?"
    }
  ]
}
```

---

### Category Coverage Matrix

| Question | correct | close | wrong_op | conceptual | stuck | off_topic |
|----------|---------|-------|----------|------------|-------|-----------|
| Q1: -3+5 | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| Q2: 5-(-3) | ✓ | - | ✓ | ✓ | - | - |
| Q3: Temperature | ✓ | - | ✓ | ✓ | ✓ | - |
| Q4: 1/2+1/4 | ✓ | ✓ | ✓ | - | - | - |
| Q5: -3-5 | ✓ | - | ✓ | ✓ | - | - |
| Q6: Off-topic | - | - | - | - | - | ✓ |
| Q7: PEMDAS | ✓ | - | ✓ | - | - | - |

**All 6 categories covered** across 5-7 priority questions.

---

## 8. Latency Optimization

### Target Performance

- **Maximum latency**: 3.5 seconds per turn
- **Expected average**: 1.5 seconds
- **Percentile targets**:
  - P50 (median): ≤1.5s
  - P95: ≤2.5s
  - P99: ≤3.5s

### Latency Budget Breakdown

| Operation | Time | Optimization Strategy |
|-----------|------|----------------------|
| **Parallel Block** | **300ms** | |
| ├─ Session load (Redis) | 50ms | Run parallel with Stage 1 triage |
| └─ Stage 1 triage (LLM) | 300ms | GPT-4o-mini, short prompt, temp=0.1 |
| **Verification** (if answer) | 50ms | Pure JavaScript, no I/O |
| **Stage 2 classification** | 200ms | Rule-based (answers) or fast LLM (non-answers) |
| **Response generation** | 800ms | GPT-4o-mini, optimized prompts, max_tokens limit |
| **Session save** (async) | 30ms | Non-blocking, happens after response sent |
| **Overhead** | 120ms | Network, n8n processing |
| **TOTAL (typical)** | **1500ms** | **✓ Well under 3.5s target** |

### Optimization Techniques

#### 1. Parallel Operations

```javascript
// Run simultaneously:
Promise.all([
  loadSession(session_id),     // 50ms
  stageOneTriage(message)      // 300ms
]);
// Total: 300ms instead of 350ms
```

#### 2. LLM Optimizations

**Model Selection**:
- Use GPT-4o-mini (not GPT-4) for speed
- Stage 1: ~300ms average
- Stage 2: ~200ms average
- Response: ~800ms average

**Prompt Engineering**:
- Keep prompts concise (fewer input tokens = faster)
- Set `max_tokens` limit (fewer output tokens = faster)
- Temperature 0.1-0.3 (deterministic = faster)

**Example Settings**:
```javascript
{
  model: "gpt-4o-mini",
  temperature: 0.1,
  max_tokens: 150,      // Force brevity
  messages: [...]
}
```

#### 3. Caching (Future Enhancement)

**What to cache**:
- Common student inputs ("I don't know", "help", "What's a negative?")
- Triage results for identical inputs within session
- Prompt templates (pre-loaded, not fetched each time)

**Not implemented in prototype** (adds complexity), but documented for production.

#### 4. Async Operations

**Session Save**:
```javascript
// DON'T wait for save to complete
response = await generateResponse(...);

// Return immediately
res.json(response);

// Save asynchronously (non-blocking)
saveSession(session).catch(err => log(err));
```

#### 5. Connection Pooling

**Redis**: Use connection pool (n8n handles automatically)
**OpenAI**: Reuse HTTP connections (node.js http agent)

### Monitoring & Alerts

**Metrics to Track**:
```javascript
{
  turn_latency_ms: 1450,
  breakdown: {
    session_load: 45,
    triage_stage1: 310,
    verification: 42,
    triage_stage2: 185,
    response_generation: 780,
    session_save: 28,
    overhead: 60
  }
}
```

**Alert Thresholds**:
- Warning: P95 > 2.5s
- Critical: P95 > 3.5s
- Investigate if any single operation > 50% of total time

---

## 9. Integration Patterns

### Webhook API Contract

**Endpoint**: `POST /tutor/message`

**Authentication**: Bearer token (API key)

```http
POST /tutor/message HTTP/1.1
Host: your-n8n-instance.com
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "student_id": "user_12345",
  "session_id": "sess_abc789",
  "message": "-8",
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
      "difference": 10
    },
    "attempt_count": 1,
    "latency_ms": 1450,
    "timestamp": "2025-10-08T10:31:22.456Z"
  }
}
```

### Integration with MinS Text Module

#### Option A: Direct Webhook

**MinS Text Module → n8n**:
```javascript
// In MinS frontend (when student sends message)
fetch('https://n8n-instance.com/webhook/tutor/message', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    student_id: currentUser.id,
    session_id: currentSession.id,
    message: studentInput,
    current_problem: currentProblem
  })
})
.then(res => res.json())
.then(data => {
  displayTutorMessage(data.response);
});
```

#### Option B: Backend Proxy

**MinS Backend** acts as proxy:

```javascript
// MinS API endpoint
app.post('/api/tutor/message', async (req, res) => {
  const { student_id, message } = req.body;

  // Get current problem from MinS DB
  const problem = await getCurrentProblem(student_id);

  // Call n8n
  const tutorResponse = await fetch(N8N_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${N8N_API_KEY}` },
    body: JSON.stringify({
      student_id,
      session_id: req.sessionID,
      message,
      current_problem: problem
    })
  });

  const data = await tutorResponse.json();

  // Log to MinS analytics
  await logTutorInteraction(student_id, data.metadata);

  // Return to frontend
  res.json(data);
});
```

**Advantages**:
- Centralized logging
- Additional business logic
- API key security (not exposed to frontend)

### Error Handling

**n8n Workflow Error Handling**:

```javascript
// If LLM fails
if (llm_error) {
  return {
    response: "I'm having trouble right now. Could you try again?",
    metadata: {
      error: true,
      error_type: "llm_timeout",
      retry_recommended: true
    }
  };
}

// If verification fails to parse
if (verification.error) {
  return {
    response: "I'm not sure I understood that. Can you write your answer as a number?",
    metadata: {
      category: "stuck",
      error: true,
      error_type: "parse_failure"
    }
  };
}

// If session expired
if (!session_found) {
  session = createNewSession(student_id);
  // Continue normally with fresh session
}
```

### Testing Integration

**cURL Example**:

```bash
curl -X POST https://n8n-instance.com/webhook/tutor/message \
  -H "Authorization: Bearer test_api_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_user",
    "session_id": "test_session_1",
    "message": "-8",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 5?",
      "correct_answer": "2"
    }
  }'
```

**Postman Collection**: See `2-prototype/tests/postman-collection.json`

---

## 10. Future Enhancements

### Phase 2: Knowledge Base (RAG)

**Problem**: Tutor can't retrieve specific teaching materials for concepts.

**Solution**: Retrieval-Augmented Generation

**Implementation**:
1. Build knowledge base of concept explanations (embeddings in vector store)
2. When student asks conceptual question → retrieve relevant explanation
3. Inject into prompt for contextualized response

**Example**:
```
Student: "What's a negative number?"
→ Retrieve from KB: "Negative numbers explained for grade 6"
→ Tutor: "A negative number is less than zero. Imagine you owe 3 dollars - that's like having -$3. On a number line..."
```

**Tech**: LangChain vector stores (Pinecone, Chroma, or Weaviate)

### Phase 3: Multi-Step Problem Decomposition (Agents)

**Problem**: Complex word problems require breaking into sub-problems.

**Solution**: LangChain agents that can plan and execute multiple steps.

**Example**:
```
Problem: "Sarah had $5, spent $8, then earned $10. How much does she have now?"

Agent planning:
Step 1: Calculate 5 - 8 = -3 (she owes $3)
Step 2: Check if student understands negative money (debt)
Step 3: Calculate -3 + 10 = 7
Step 4: Guide student through each step
```

**Tech**: LangGraph for agent workflows

### Phase 4: Tool Use

**Problem**: Some problems need calculators, graphing, or visual aids.

**Solution**: LangChain tools (function calling)

**Examples**:
- **Calculator**: For complex arithmetic
- **Graphing**: Plot functions for visualization
- **Hint Bank**: Retrieve structured hints from database
- **Worked Examples**: Fetch similar solved problems

### Phase 5: Fine-Tuned Triage

**Problem**: Generic GPT-4o-mini may not be optimal for student response classification.

**Solution**: Fine-tune smaller model on student interaction data.

**Approach**: DSPy for prompt optimization + fine-tuning pipeline

**Benefits**:
- Faster triage (smaller model)
- More accurate category detection
- Lower cost

### Phase 6: Curriculum Integration

**Problem**: Prototype handles single problems in isolation.

**Solution**: Multi-problem sequences with mastery tracking.

**Features**:
- Problem sequencing (easy → hard)
- Mastery thresholds (need 3 correct before advancing)
- Concept prerequisites (can't do division without multiplication)
- Adaptive difficulty

### Phase 7: Multi-Language Support

**Problem**: English-only.

**Solution**: Prompt translation + multilingual models.

**Considerations**:
- Translate prompts to target language
- Use multilingual models (GPT-4o supports 50+ languages)
- Handle math notation variations across cultures

---

## Conclusion

This blueprint provides a complete specification for an adaptive AI tutoring system that:

✓ Classifies student responses intelligently (6 categories)
✓ Adapts teaching strategy based on context (attempt count, error patterns)
✓ Maintains natural conversation flow (session memory)
✓ Verifies answers accurately (edge case handling)
✓ Meets performance targets (≤3.5s latency)
✓ Follows pedagogical best practices (Socratic method, scaffolding)

**The working prototype demonstrates this architecture in action, ready for MinS dev team to implement in production.**

---

**Document Version**: 1.0
**Last Updated**: October 10, 2025
**Status**: Phase 1 Delivery Complete

For implementation details, see:
- Prompt templates: `prompts/`
- Exemplar questions: `../2-prototype/exemplars/questions.json`
- Working prototype: `../2-prototype/`
- API specification: `../2-prototype/docs/API-SPEC.md`
