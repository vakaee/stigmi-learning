# Bug Fix: Scaffolding - Main Problem Answers Ignored

**Date**: October 11, 2025
**Bug**: When students answer the main problem during scaffolding (e.g., "I see, the correct answer is 2"), the tutor ignores it and continues asking scaffolding questions
**Expected**: Should recognize main problem attempt, verify it, and if correct, celebrate and end scaffolding

---

## Root Cause

Two critical issues prevented the AI Agent from handling main problem attempts during scaffolding:

### Issue 1: Missing Tool Connection
The "Tool: Verify Main Answer" node was **not connected** to the AI Agent. In n8n, tools must have an `ai_tool` connection to be available to agents.

**What was happening:**
1. During scaffolding, student says "I see, the correct answer is 2"
2. AI Agent only has access to `validate_scaffolding` tool (verify_main_answer was disconnected)
3. Agent tries to validate "the correct answer is 2" against the scaffolding question
4. This fails, returns "stuck"
5. Tutor repeats the same scaffolding question

**Evidence from workflow diagram:**
The connections section (line 937+) was missing the `ai_tool` connection from "Tool: Verify Main Answer" to "AI Agent".

### Issue 2: Agent Prompt Too Narrow
The AI Agent system prompt (line 226) said "You are a scaffolding validation agent" and **only** instructed it to use the `validate_scaffolding` tool. It had no logic to:
- Detect when student is answering the main problem vs. scaffolding question
- Call the `verify_main_answer` tool
- Set `is_main_problem_attempt: true` flag

**Old prompt:**
```
You are a scaffolding validation agent.
...
YOUR JOB:
The student is responding to a scaffolding sub-question. Use the validate_scaffolding tool to check if their response is correct.
```

This assumed ALL responses during scaffolding are scaffolding responses, which is incorrect.

---

## The Fix

### Fix 1: Added Tool Connection
Added the missing `ai_tool` connection in the connections section (lines 718-727):

```json
"Tool: Verify Main Answer": {
  "ai_tool": [
    [
      {
        "node": "AI Agent",
        "type": "ai_tool",
        "index": 0
      }
    ]
  ]
}
```

Now the AI Agent has access to BOTH tools:
- `validate_scaffolding` - for scaffolding responses
- `verify_main_answer` - for main problem attempts

### Fix 2: Intelligent Routing Prompt
Replaced the scaffolding-only prompt with a two-step intelligent routing prompt:

**New prompt structure:**
```
You are an AI agent that classifies student responses during scaffolding.

STEP 1: DETECT INTENT
Check if student's response is attempting to answer the MAIN PROBLEM:
- Contains phrases like "the answer is", "I see", "correct answer is"
- Contains a numeric answer that could be for the main problem
- Looks like a direct answer to the main problem

If YES → MAIN PROBLEM ATTEMPT
If NO → SCAFFOLDING RESPONSE

STEP 2: USE THE APPROPRIATE TOOL
**If MAIN PROBLEM ATTEMPT:**
Call verify_main_answer tool
- Returns: "correct", "close", or "wrong_operation"
- Set is_main_problem_attempt: true

**If SCAFFOLDING RESPONSE:**
Call validate_scaffolding tool
- Returns: {correct, partially_correct, reasoning}
- Set is_main_problem_attempt: false
```

This gives the agent the intelligence to:
1. Detect whether student is answering main problem or scaffolding question
2. Route to the appropriate tool
3. Set the critical `is_main_problem_attempt` flag correctly

---

## Expected Flow After Fix

### Scenario 1: Student Answers Main Problem During Scaffolding

**Input**: Student says "I see, the correct answer is 2" during scaffolding

1. **AI Agent**:
   - STEP 1: Detects "the correct answer is" phrase + numeric value
   - Intent: MAIN PROBLEM ATTEMPT
   - STEP 2: Calls `verify_main_answer` tool

2. **Tool: Verify Main Answer**:
   - Extracts "2" from student message
   - Compares to correct_answer: "2"
   - Returns: "correct"

3. **AI Agent**:
   - Tool result: "correct"
   - Returns: `{"category": "correct", "is_main_problem_attempt": true, "confidence": 0.95, "reasoning": "Student correctly solved the main problem"}`

4. **Route by Category**: Routes to "Response: Correct"

5. **Update Session**: Sets `scaffolding.active = false` (because category = "correct" and is_scaffolding_active = true)

6. **Tutor Response**: Celebrates and asks for teach-back explanation

### Scenario 2: Student Responds to Scaffolding Question

**Input**: Student says "it's on the left of 0" in response to scaffolding question

1. **AI Agent**:
   - STEP 1: Detects conceptual answer (no "answer is" phrase, no numeric answer to main problem)
   - Intent: SCAFFOLDING RESPONSE
   - STEP 2: Calls `validate_scaffolding` tool

2. **Tool: Validate Scaffolding**:
   - Uses OpenAI to semantically validate the response
   - Returns: `{correct: true, reasoning: "Student correctly explained the position"}`

3. **AI Agent**:
   - Tool result: correct = true
   - Returns: `{"category": "scaffold_progress", "is_main_problem_attempt": false, "confidence": 0.9, "reasoning": "Student correctly explained the position"}`

4. **Route by Category**: Routes to "Response: Scaffold Progress"

5. **Update Session**: Increments `scaffolding.depth`, updates `scaffolding.last_question`

6. **Tutor Response**: Acknowledges and asks next scaffolding step

---

## Testing

### Test Case 1: Main Problem Answer During Scaffolding

```bash
# Turn 1: Student gives wrong answer, tutor starts scaffolding
curl -X POST http://localhost:5678/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_123",
    "session_id": "test_main_answer_scaffolding",
    "message": "1",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 5?",
      "correct_answer": "2"
    }
  }'

# Turn 2: Tutor asks scaffolding question (e.g., "What does -3 mean?")
# Turn 3: Student answers main problem during scaffolding
curl -X POST http://localhost:5678/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_123",
    "session_id": "test_main_answer_scaffolding",
    "message": "I see, the correct answer is 2",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 5?",
      "correct_answer": "2"
    }
  }'
```

**Expected result for Turn 3**:
- `category: "correct"`
- `is_main_problem_attempt: true`
- `scaffolding.active: false` (scaffolding ends)
- Tutor celebrates and ends scaffolding

### Test Case 2: Correct Scaffolding Response
```bash
# Student gives correct conceptual answer to scaffolding question
curl -X POST http://localhost:5678/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_123",
    "session_id": "test_scaffolding_progress",
    "message": "it'\''s on the left of 0",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 5?",
      "correct_answer": "2"
    }
  }'
```

**Expected result**:
- `category: "scaffold_progress"`
- `is_main_problem_attempt: false`
- `scaffolding.active: true` (scaffolding continues)
- Tutor acknowledges and asks next step

### Test Case 3: Various Main Problem Phrases
Test that agent detects these as main problem attempts:
- "the answer is 2"
- "I think it's 2"
- "it's 2"
- "the correct answer is 2"
- "I see, it's 2"
- "oh, 2"

All should be classified as `category: "correct"` with `is_main_problem_attempt: true`.

---

## Files Modified

### `/Users/Vlad/Dev/MinS/ai-tutor-poc/2-prototype/workflow-production-ready.json`

#### 1. Connections Section (lines 718-727)
Added `ai_tool` connection from "Tool: Verify Main Answer" to "AI Agent":
```json
"Tool: Verify Main Answer": {
  "ai_tool": [
    [
      {
        "node": "AI Agent",
        "type": "ai_tool",
        "index": 0
      }
    ]
  ]
}
```

#### 2. AI Agent System Prompt (line 226)
Replaced scaffolding-only prompt with intelligent routing prompt:
- Added STEP 1: DETECT INTENT (main problem vs. scaffolding)
- Added STEP 2: USE THE APPROPRIATE TOOL (with instructions for both)
- Added examples for both tool types
- Added critical is_main_problem_attempt flag instructions

---

## Related Issues

### This Fix Enables Proper Scaffolding Flow
Before this fix, scaffolding was a "one-way street" - once started, students were trapped until they answered all scaffolding questions sequentially, even if they figured out the main answer.

After this fix, scaffolding becomes **adaptive**:
- Student can "exit" scaffolding by solving the main problem at any time
- Tutor recognizes and celebrates when student figures it out
- Natural conversation flow is preserved

### Why This Bug Wasn't Caught Earlier
The workflow diagram shows nodes visually, but tool connections (`ai_tool` type) are defined in the JSON connections section, not visible in the diagram. The "Tool: Verify Main Answer" node existed but was disconnected from the agent.

---

## Commit Message

```
fix: enable main problem answers during scaffolding

Two issues prevented students from answering the main problem during
scaffolding:

1. Tool Connection Missing: "Tool: Verify Main Answer" was not
   connected to AI Agent (missing ai_tool connection in JSON)

2. Agent Prompt Too Narrow: Agent only knew about validate_scaffolding
   tool, had no logic to detect main problem attempts or call
   verify_main_answer tool

Fixes:
- Added ai_tool connection from verify_main_answer to AI Agent
- Replaced scaffolding-only prompt with intelligent 2-step routing:
  - STEP 1: Detect if main problem attempt vs scaffolding response
  - STEP 2: Route to appropriate tool (verify_main_answer or
    validate_scaffolding)
- Added critical is_main_problem_attempt flag logic

Result: Students can now exit scaffolding by solving the main problem,
and tutor celebrates instead of repeating scaffolding questions.

Fixes: Student saying "the correct answer is 2" gets stuck loop
```

---

## Impact

This fix ensures:
1. Students can exit scaffolding naturally by solving the main problem
2. Tutor recognizes and celebrates when students figure it out during scaffolding
3. No more stuck loops where correct main problem answers are ignored
4. Scaffolding becomes adaptive rather than rigid sequential flow
5. Conversation flow feels natural and responsive

This was a **critical bug** that made scaffolding feel frustrating and broken. Now scaffolding is truly adaptive and student-responsive.
