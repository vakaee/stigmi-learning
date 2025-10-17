# Option A: Redesign Classification Flow - Implementation Plan

**Date**: October 17, 2025  
**Estimated Effort**: 2-3 days  
**Risk Level**: Medium (architectural change, but well-scoped)

---

## EXECUTIVE SUMMARY

**Goal**: Replace dual classification system with single content-first flow

**Key Changes**:
- Remove state-based routing (Switch: Scaffolding Active?)
- Merge Pre-Agent and AI Agent classification paths
- Add operation error heuristic (fix "wrong_operation" overload)
- Add deterministic semantic validation (fix validation inconsistency)
- Single unified classification path

**Benefits**:
- No contradictory classifications
- Faster (deterministic where possible)
- More maintainable
- Fixes all 3 architectural issues

---

## NEW ARCHITECTURE OVERVIEW

### Current Flow (Problematic)
```
Webhook
  → Load Session
    → [FORK based on is_scaffolding_active flag]
      ├─ Path A (not scaffolding): LLM Extract → Code Verify → Route
      └─ Path B (scaffolding): AI Agent → Route
```

**Problem**: Two independent classification systems

### New Flow (Unified)
```
Webhook
  → Load Session
    → Content Feature Extractor (LLM)
      → Content-Based Router (Code)
        ├─ Numeric Answer → Enhanced Numeric Verifier (Code)
        ├─ Conceptual Answer → Semantic Validator (Code + OpenAI tool)
        └─ No Answer → Intent Classifier (LLM)
      → Merge Results
        → Response: Unified (unchanged)
          → Update Session
```

**Solution**: Single classification path, content-first routing

---

## DETAILED NODE CHANGES

### Nodes to REMOVE
1. **Switch: Scaffolding Active?**
   - Reason: State-based routing replaced with content-based
   
2. **AI Agent** (with tools)
   - Reason: Replaced with simpler deterministic logic
   - Note: Keep Response: Unified LLM (different purpose)

3. **Prepare Agent Context** (Code)
   - Reason: No longer need to prepare for AI Agent

4. **Parse Agent Output** (Code)
   - Reason: No longer have AI Agent to parse

5. **Format for Routing** (Code)
   - Reason: New routing logic

### Nodes to REPLACE

#### Old: LLM: Extract Intent & Value
**Purpose**: Determine if answer attempt, extract number

**Issues**:
- Only extracts numeric values
- Doesn't extract keywords for conceptual answers
- Part of dual classification problem

#### New: Content Feature Extractor (LLM)
**Purpose**: Extract ALL features for routing

**OpenAI Prompt**:
```
You are a content feature extractor for a math tutoring system.

Problem: {{ $json.current_problem.text }}
Correct Answer: {{ $json.current_problem.correct_answer }}
Student Message: "{{ $json.student_message }}"

Extract these features:

1. MESSAGE TYPE:
   - answer_attempt: Message contains a numeric answer
   - conceptual_response: Message contains conceptual keywords (operations, directions, concepts)
   - question: Message asks a question
   - help_request: Message requests help ("I don't know", "help me")
   - off_topic: Message unrelated to math

2. NUMERIC VALUE (if answer_attempt):
   - Extract the number from the message
   - Convert written numbers to digits ("two" → 2, "negative three" → -3)
   - Handle expressions ("1/2" → 0.5)
   - If multiple numbers, extract the ANSWER (not process description)
     Example: "that's 5 steps and we get 2" → extract 2

3. CONCEPTUAL KEYWORDS (if conceptual_response):
   - Extract operation keywords: "adding", "subtracting", "multiplying", "dividing"
   - Extract direction keywords: "right", "left", "up", "down"
   - Extract concept keywords: "negative", "positive", "zero", "number line"

4. CONFIDENCE:
   - 0.9-1.0: Clear, unambiguous extraction
   - 0.7-0.9: Reasonably clear
   - 0.0-0.7: Ambiguous or uncertain

Return JSON:
{
  "message_type": "answer_attempt" | "conceptual_response" | "question" | "help_request" | "off_topic",
  "numeric_value": number | null,
  "keywords": string[] | null,
  "confidence": number
}

CRITICAL: Extract what student SAID, not what you think they MEANT.
```

---

#### Old: Code: Verify Answer
**Purpose**: Compare student answer to correct answer

**Issues**:
- Classifies ALL wrong answers as "wrong_operation"
- No check for plausible operation errors

#### New: Enhanced Numeric Verifier (Code)
**Purpose**: Verify numeric answers AND detect operation errors

**JavaScript Implementation**:
```javascript
// Enhanced Numeric Verifier with Operation Error Detection
const features = $input.first().json;
const context = $('Load Session').first().json;

const studentValue = features.numeric_value;
const correctAnswer = context.current_problem.correct_answer;
const problemText = context.current_problem.text;

// Parse correct answer
let correctValue;
try {
  correctValue = parseFloat(String(correctAnswer).replace(/[^0-9.\-]/g, ''));
  if (isNaN(correctValue)) {
    throw new Error('Cannot parse correct answer');
  }
} catch (error) {
  return {
    json: {
      category: 'stuck',
      is_main_problem_attempt: true,
      confidence: 0.5,
      reasoning: `Cannot verify: ${error.message}`
    }
  };
}

// Check if valid numeric value
if (studentValue === null || isNaN(studentValue)) {
  return {
    json: {
      category: 'stuck',
      is_main_problem_attempt: true,
      confidence: 0.8,
      reasoning: 'Could not extract valid numeric value'
    }
  };
}

// Calculate difference
const diff = Math.abs(studentValue - correctValue);

// Check if correct
const isCorrect = diff < 0.001;
if (isCorrect) {
  return {
    json: {
      category: 'correct',
      is_main_problem_attempt: true,
      confidence: 1.0,
      reasoning: `Student answered ${studentValue}, correct!`
    }
  };
}

// Check if close (within 20% threshold)
const percentThreshold = Math.abs(correctValue * 0.2);
const closeThreshold = Math.max(percentThreshold, 0.3);
const isClose = diff <= closeThreshold;

if (isClose) {
  return {
    json: {
      category: 'close',
      is_main_problem_attempt: true,
      confidence: 0.9,
      reasoning: `Student answered ${studentValue}, close to ${correctValue} (diff: ${diff.toFixed(2)})`
    }
  };
}

// NEW: Check if plausible operation error
// Extract operation and numbers from problem
const operationMatch = problemText.match(/([\-\d]+)\s*([+\-*/])\s*([\-\d]+)/);

if (operationMatch) {
  const num1 = parseFloat(operationMatch[1]);
  const operation = operationMatch[2];
  const num2 = parseFloat(operationMatch[3]);
  
  // Calculate common operation errors
  const possibleErrors = [];
  
  if (operation === '+') {
    possibleErrors.push(Math.abs(num1) + Math.abs(num2));  // Forgot negatives: |-3| + |5| = 8
    possibleErrors.push(num1 - num2);                      // Subtracted instead: -3 - 5 = -8
    possibleErrors.push(Math.abs(num1 - num2));            // Abs of subtract: |-3 - 5| = 8
  } else if (operation === '-') {
    possibleErrors.push(num1 + num2);                      // Added instead
    possibleErrors.push(Math.abs(num1) + Math.abs(num2)); // Added absolutes
  }
  
  // Check if student's answer matches any plausible error
  const isOperationError = possibleErrors.some(errorValue => 
    Math.abs(studentValue - errorValue) < 0.001
  );
  
  if (isOperationError) {
    return {
      json: {
        category: 'wrong_operation',
        is_main_problem_attempt: true,
        confidence: 0.95,
        reasoning: `Student answered ${studentValue}, likely operation misconception`
      }
    };
  }
}

// Not correct, not close, not operation error → stuck
return {
  json: {
    category: 'stuck',
    is_main_problem_attempt: true,
    confidence: 0.85,
    reasoning: `Student answered ${studentValue}, not close to ${correctValue}, doesn't match operation errors`
  }
};
```

---

#### New: Content-Based Router (Code)
**Purpose**: Route to appropriate validator based on content features

**JavaScript Implementation**:
```javascript
// Content-Based Router
const features = $input.first().json;
const context = $('Load Session').first().json;

const messageType = features.message_type;
const isScaffolding = context.is_scaffolding_active;
const isTeachBack = context.is_teach_back_active;

// Route based on message type
let route;

if (isTeachBack) {
  // During teach-back, any response is explanation attempt
  route = 'teach_back_response';
} else if (messageType === 'answer_attempt') {
  // Numeric answer - check if main problem or scaffolding answer
  // During scaffolding, numeric answers could be either:
  // - Main problem attempt: "I think the answer is 2"
  // - Scaffolding sub-question answer: "5 steps"
  
  if (isScaffolding) {
    // Check if it looks like main problem attempt
    const numericValue = features.numeric_value;
    const correctAnswer = context.current_problem.correct_answer;
    const correctValue = parseFloat(String(correctAnswer).replace(/[^0-9.\-]/g, ''));
    
    // If number is close to correct answer, likely main problem attempt
    const diff = Math.abs(numericValue - correctValue);
    const isLikelyMainProblem = diff < Math.abs(correctValue * 0.5); // Within 50%
    
    route = isLikelyMainProblem ? 'verify_numeric' : 'validate_conceptual';
  } else {
    route = 'verify_numeric';
  }
} else if (messageType === 'conceptual_response') {
  // Conceptual answer (keywords) - semantic validation needed
  route = 'validate_conceptual';
} else if (messageType === 'question') {
  route = 'classify_question';
} else if (messageType === 'help_request') {
  route = 'classify_stuck';
} else {
  route = 'classify_other';
}

return {
  json: {
    ...features,
    ...context,
    _route: route
  }
};
```

---

#### New: Semantic Validator (Code + OpenAI Tool)
**Purpose**: Validate conceptual answers deterministically

**Code Node Implementation**:
```javascript
// Semantic Validator - Deterministic Keyword Matching
const input = $input.first().json;
const studentMessage = input.student_message.toLowerCase();
const scaffoldingQuestion = (input.scaffolding_last_question || '').toLowerCase();
const keywords = input.keywords || [];

// Extract expected answer from scaffolding question
let expectedKeywords = [];
let isCorrect = false;
let reasoning = '';

// Pattern matching for common scaffolding question types
if (scaffoldingQuestion.includes('adding or subtracting')) {
  expectedKeywords = ['adding', 'add', 'plus', '+'];
  const wrongKeywords = ['subtracting', 'subtract', 'minus', '-'];
  
  const hasCorrect = keywords.some(kw => expectedKeywords.includes(kw));
  const hasWrong = keywords.some(kw => wrongKeywords.includes(kw));
  
  if (hasCorrect && !hasWrong) {
    isCorrect = true;
    reasoning = 'Student correctly identified adding';
  } else if (hasWrong) {
    isCorrect = false;
    reasoning = 'Student incorrectly said subtracting';
  }
} else if (scaffoldingQuestion.includes('direction') || scaffoldingQuestion.includes('right or left')) {
  const expectedRight = ['right'];
  const expectedLeft = ['left'];
  
  // Determine which is correct based on problem (+ means right, - means left)
  const problemText = input.current_problem.text;
  const hasPlus = problemText.includes('+');
  
  if (hasPlus) {
    const hasRight = keywords.some(kw => expectedRight.includes(kw));
    const hasLeft = keywords.some(kw => expectedLeft.includes(kw));
    
    isCorrect = hasRight && !hasLeft;
    reasoning = hasRight ? 'Student correctly said right' : 'Student incorrectly said left';
  }
} else {
  // Fallback to OpenAI semantic validation for complex cases
  // This will be a separate OpenAI node connected in parallel
  return {
    json: {
      ...input,
      _needs_llm_validation: true
    }
  };
}

// Return classification
if (isCorrect) {
  return {
    json: {
      category: 'scaffold_progress',
      is_main_problem_attempt: false,
      confidence: 0.95,
      reasoning: reasoning
    }
  };
} else {
  return {
    json: {
      category: 'stuck',
      is_main_problem_attempt: false,
      confidence: 0.9,
      reasoning: reasoning
    }
  };
}
```

**OpenAI Tool (fallback for complex semantic validation)**:
```
You validate conceptual answers to scaffolding questions.

Scaffolding Question: "{{ $json.scaffolding_last_question }}"
Student Response: "{{ $json.student_message }}"

Is the student's response semantically CORRECT for this question?

Return JSON:
{
  "is_correct": true | false,
  "confidence": number,
  "reasoning": "brief explanation"
}

Examples:
Q: "What does -3 mean?"
- "negative 3" → correct
- "3 left of zero" → correct  
- "positive 3" → WRONG

Q: "When we see +, are we adding or subtracting?"
- "adding" → correct
- "subtracting" → WRONG
```

---

### Nodes to KEEP (unchanged)

1. **Webhook Trigger** - Entry point
2. **Normalize input** (Code) - Input sanitization
3. **Redis: Get Session** - Session retrieval
4. **Load Session** (Code) - Session parsing
5. **Response: Unified** (OpenAI) - Response generation (KEEP - it's good!)
6. **Update Session & Format Response** (Code) - Session updates
7. **Redis: Save Session** - Session persistence
8. **Webhook Response** - Return to client

---

## NEW WORKFLOW STRUCTURE

### Complete Node Flow
```
1. Webhook Trigger
   ↓
2. Normalize input (Code)
   ↓
3. Redis: Get Session
   ↓
4. Load Session (Code)
   ↓
5. Content Feature Extractor (OpenAI) ← NEW
   ↓
6. Content-Based Router (Code) ← NEW
   ↓
7. [Switch based on _route]
   ├─ verify_numeric → Enhanced Numeric Verifier (Code) ← ENHANCED
   ├─ validate_conceptual → Semantic Validator (Code + OpenAI fallback) ← NEW
   ├─ classify_question → Intent Classifier (OpenAI)
   ├─ classify_stuck → Stuck Classifier (Code)
   └─ classify_other → Other Classifier (OpenAI)
   ↓
8. Merge Results (Code) ← NEW (merge classification + context)
   ↓
9. Route by Category (Switch) ← KEEP (routes to synthesis if needed)
   ↓
10. Response: Unified (OpenAI) ← KEEP (unchanged)
    ↓
11. Update Session & Format Response (Code) ← KEEP
    ↓
12. Redis: Save Session
    ↓
13. Webhook Response
```

### Key Differences from Current
- Single classification path (not two)
- Content-based routing BEFORE classification
- Deterministic validation where possible
- No AI Agent with tools (simpler, faster)

---

## MIGRATION STRATEGY

### Phase 1: Preparation (30 minutes)
1. Create new branch: `refactor/option-a-classification`
2. Backup current workflow: `workflow-production-ready-backup.json`
3. Document current test cases and expected outputs

### Phase 2: Build New Nodes (3-4 hours)

**Order of Implementation**:

1. **Content Feature Extractor** (30 min)
   - Create new OpenAI node
   - Test with sample inputs
   - Verify extraction accuracy

2. **Content-Based Router** (30 min)
   - Create new Code node
   - Test routing logic with different message types
   - Verify routes correctly

3. **Enhanced Numeric Verifier** (1 hour)
   - Update Code: Verify Answer
   - Add operation error heuristic
   - Test with:
     * Correct answers
     * Close answers  
     * Operation errors (8, -8)
     * Random wrong answers (45)

4. **Semantic Validator** (1 hour)
   - Create new Code node (deterministic matching)
   - Create new OpenAI node (fallback)
   - Test with:
     * "adding" / "subtracting"
     * "right" / "left"
     * "negative" / "positive"

5. **Merge Results** (30 min)
   - Create new Code node
   - Merge classification with context
   - Preserve all session data

### Phase 3: Connect Nodes (1 hour)

1. Remove old nodes:
   - Delete AI Agent
   - Delete Switch: Scaffolding Active
   - Delete Prepare Agent Context
   - Delete Parse Agent Output

2. Reconnect workflow:
   - Load Session → Content Feature Extractor
   - Content Feature Extractor → Content-Based Router
   - Router → [classification nodes]
   - Classification → Merge Results
   - Merge Results → Route by Category
   - (Rest stays the same)

3. Update connections in JSON

### Phase 4: Testing (2-3 hours)

**Test Suite**:

1. **Numeric Answers (non-scaffolding)**
   - Correct: "2" → correct
   - Close: "1.8" → close
   - Operation error: "8" → wrong_operation
   - Random wrong: "45" → stuck

2. **Conceptual Answers (scaffolding)**
   - Correct keyword: "adding" → scaffold_progress
   - Wrong keyword: "subtracting" → stuck
   - Ambiguous: "I think plus" → (validate with LLM fallback)

3. **Main Problem During Scaffolding**
   - "I think the answer is 2" → correct (ends scaffolding)
   - "the answer is 45" → stuck (continues scaffolding)

4. **Edge Cases**
   - "I don't know" → stuck
   - "What does negative mean?" → conceptual_question
   - "I like pizza" → off_topic

5. **Complete Conversation Flows**
   - Run the "45" conversation test
   - Run other exemplar conversations
   - Verify all 4 turns classify correctly

### Phase 5: Session Compatibility (30 minutes)

Ensure session schema unchanged:
- `is_scaffolding_active` flag still used (for Response generation)
- `attempt_count` still tracked
- `recent_turns` still maintained
- No breaking changes to session structure

### Phase 6: Performance Testing (30 minutes)

Measure latency:
- Target: ≤ 3.5 seconds per turn
- Expected: ~2 seconds (one less LLM call, more deterministic)

Compare:
- Old flow: 2 LLM calls (Extract Intent + AI Agent)
- New flow: 1-2 LLM calls (Feature Extractor + optional semantic validation)

---

## TESTING CHECKLIST

### Unit Tests (per node)
- [ ] Content Feature Extractor extracts correct features
- [ ] Content-Based Router routes correctly
- [ ] Enhanced Numeric Verifier detects operation errors
- [ ] Semantic Validator validates keywords correctly

### Integration Tests (full flow)
- [ ] "45" conversation all 4 turns correct
- [ ] Correct answer triggers teach-back
- [ ] Close answer triggers gentle probe
- [ ] Operation error triggers clarification
- [ ] Scaffolding progress continues correctly
- [ ] Main problem during scaffolding exits correctly

### Regression Tests
- [ ] All exemplar questions still work
- [ ] Session management unchanged
- [ ] Response generation unchanged
- [ ] Latency within target

---

## ROLLBACK STRATEGY

If issues found:

1. **Immediate rollback** (5 minutes)
   - Restore `workflow-production-ready-backup.json`
   - Re-import to n8n
   - Activate original workflow

2. **Gradual rollback** (if in production)
   - Run both workflows in parallel
   - Route % of traffic to new workflow
   - Monitor error rates
   - Increase % gradually or rollback

3. **Data compatibility**
   - Session schema unchanged
   - Sessions from old workflow work with new workflow
   - No migration needed

---

## EFFORT ESTIMATION

### Optimistic (2 days)
- Developer familiar with n8n: 1 day
- Testing: 0.5 days
- Deployment: 0.5 days

### Realistic (3 days)
- Development: 1.5 days
- Testing and bug fixes: 1 day
- Documentation: 0.5 days

### Pessimistic (4 days)
- Development challenges: 2 days
- Unexpected issues: 1 day
- Extra testing: 1 day

**Recommended**: Plan for 3 days, allocate 4 days buffer

---

## RISK ASSESSMENT

### Low Risks
- ✓ Session compatibility (schema unchanged)
- ✓ Response generation (node unchanged)
- ✓ Rollback strategy (clear path)

### Medium Risks
- ⚠ Semantic validation edge cases (mitigated by LLM fallback)
- ⚠ Operation error heuristic coverage (mitigated by testing)
- ⚠ Performance (mitigated by fewer LLM calls)

### High Risks
- ✗ None identified

**Overall Risk**: Medium-Low

---

## SUCCESS CRITERIA

1. **Functional**:
   - [ ] All 4 bugs in "45" conversation fixed
   - [ ] All exemplar questions pass
   - [ ] No regression in existing functionality

2. **Performance**:
   - [ ] Latency ≤ 3.5 seconds (same or better)
   - [ ] Classification accuracy ≥ 95%

3. **Maintainability**:
   - [ ] Single classification path (no dual system)
   - [ ] Deterministic where possible (less LLM variability)
   - [ ] Clear node naming and documentation

4. **Stability**:
   - [ ] No new bugs introduced
   - [ ] Session compatibility maintained
   - [ ] Rollback plan tested

---

## NEXT STEPS

1. **Get approval** on this implementation plan
2. **Create branch** and backup workflow
3. **Implement Phase 2** (build new nodes)
4. **Test incrementally** after each node
5. **Connect and test** full workflow
6. **Deploy** after all tests pass

**Question for stakeholder**: Proceed with implementation?
