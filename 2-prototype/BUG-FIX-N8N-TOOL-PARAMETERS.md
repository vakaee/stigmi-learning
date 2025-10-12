# Bug Fix: n8n AI Agent Tool Parameter Passing

**Date**: October 12, 2025
**Duration**: Hours of debugging
**Bug**: n8n toolCode cannot access OpenAI function call parameters
**Solution**: Use workflow context (`$json`) instead of function call parameters

---

## The Problem

When building n8n AI Agent workflows with custom tools (using `@n8n/n8n-nodes-langchain.toolCode`), the JavaScript code inside the tool **cannot access the parameters that OpenAI passes when calling the function**.

### What We Observed

1. OpenAI successfully calls the tools (confirmed via n8n execution logs)
2. OpenAI passes the correct parameters according to the JSON schema
3. But the JavaScript toolCode receives **no parameters** in any accessible form

### Error Message

```
Cannot read properties of undefined (reading 'scaffolding_question')
```

Or:

```
scaffolding_question is not defined
```

---

## What We Tried (All Failed)

Over several hours, we attempted multiple approaches to access the function call parameters:

### Attempt 1: Direct Global Variables ❌
```javascript
const scaffoldingQuestion = scaffolding_question;
const studentResponse = student_response;
```
**Result**: `ReferenceError: scaffolding_question is not defined`

### Attempt 2: Query Object ❌
```javascript
const scaffoldingQuestion = query.scaffolding_question;
```
**Result**: `TypeError: Cannot read properties of undefined (reading 'scaffolding_question')`

### Attempt 3: n8n Input Accessor ❌
```javascript
const params = $input.first().json;
const scaffoldingQuestion = params.scaffolding_question;
```
**Result**: Parameters not in `$input.first().json` (only workflow context data)

### Attempt 4: AI-Specific Variables ❌
```javascript
const params = $fromAI || $fromai || $fromAi;
```
**Result**: These are **functions**, not objects containing parameters

### Debug Discovery

We added comprehensive debugging to see what's actually available:

```javascript
const debugInfo = {
  typeof_$fromAI: typeof $fromAI,  // "function"
  typeof_$fromai: typeof $fromai,  // "function"
  typeof_$fromAi: typeof $fromAi,  // "function"
  $json_value: $json,              // Contains workflow context
  $input_first: $input.first().json, // Same workflow context
  arguments_length: arguments.length, // 0
  arguments_0: arguments[0]           // null
};
```

**Key Findings**:
- `$fromAI`/`$fromai`/`$fromAi` are **functions**, not parameter objects
- `$json` contains **workflow context**, not OpenAI function call parameters
- `arguments` array is **empty** (length = 0)
- **No accessible way to get OpenAI function call parameters**

---

## The Solution

**Stop trying to access OpenAI function call parameters. Use workflow context instead.**

n8n AI Agent tools have access to the workflow's input data via `$json`. This contains all the context passed to the AI Agent node by the previous nodes in the workflow.

### Tool Schema (Keep This)

The JSON schema in the tool definition is still needed for OpenAI to understand what parameters to pass. But these parameters are **never accessible** to the JavaScript code.

```json
{
  "type": "object",
  "properties": {
    "scaffolding_question": {
      "type": "string",
      "description": "The scaffolding question that was asked to the student"
    },
    "student_response": {
      "type": "string",
      "description": "The student's response to the scaffolding question"
    }
  },
  "required": ["scaffolding_question", "student_response"]
}
```

Keep this schema - it helps OpenAI decide when to call the tool and understand its purpose.

### Tool Code (Use Workflow Context)

```javascript
// CORRECT: Read from workflow context
const studentResponse = $json.student_message || '';
const scaffoldingQuestion = $json.scaffolding_last_question || '';
const problemContext = $json.current_problem?.text || '';

// Now you have the data you need
return JSON.stringify({
  scaffolding_question: scaffoldingQuestion,
  student_response: studentResponse,
  problem_context: problemContext
});
```

---

## Why This Works

In our n8n workflow, the "Prepare Agent Context" node builds a comprehensive context object containing:

```javascript
{
  student_message: "idk",
  current_problem: {
    id: "default_problem_1",
    text: "What is -3 + 5?",
    correct_answer: "2"
  },
  scaffolding_last_question: "Can you explain...",
  is_scaffolding_active: true,
  // ... etc
}
```

This context is passed to the AI Agent, and **the same context is available in `$json` within tool code**.

So instead of expecting OpenAI to re-pass this data as function parameters, we:
1. Build the context in a preceding node
2. Pass it to the AI Agent
3. Access it via `$json` in tool code

---

## Files Modified

### `/Users/Vlad/Dev/MinS/ai-tutor-poc/2-prototype/workflow-production-ready.json`

#### Tool: Validate Scaffolding (lines 206-228)

**Before (Broken)**:
```javascript
const scaffoldingQuestion = scaffolding_question || '';
const studentResponse = student_response || '';
// ReferenceError: scaffolding_question is not defined
```

**After (Working)**:
```javascript
const studentResponse = $json.student_message || '';
const scaffoldingQuestion = $json.scaffolding_last_question || '';
const problemContext = $json.current_problem?.text || '';
```

#### Tool: Verify Main Answer (lines 178-196)

**Before (Broken)**:
```javascript
const studentMessage = student_message || '';
const correctAnswer = correct_answer || '';
// ReferenceError: student_message is not defined
```

**After (Working)**:
```javascript
const studentMessage = $json.student_message || '';
const correctAnswer = $json.current_problem?.correct_answer || '';
```

---

## Key Takeaways

### For n8n AI Agent Tool Development

1. **OpenAI function call parameters are NOT accessible in toolCode JavaScript**
2. **Use `$json` to access workflow context instead**
3. **Build your context in a preceding node** (like "Prepare Agent Context")
4. **Keep the JSON schema** - it's for OpenAI's understanding, not for parameter passing
5. **Don't waste time trying different parameter access methods** - none of them work

### For This Workflow Specifically

Our tools now correctly read from:
- `$json.student_message` - student's input
- `$json.scaffolding_last_question` - last scaffolding question asked
- `$json.current_problem.text` - the main problem
- `$json.current_problem.correct_answer` - correct answer
- `$json.is_scaffolding_active` - scaffolding state flag

All of these are prepared by the "Prepare Agent Context" node (lines 252-255) and passed through to the AI Agent and its tools.

---

## Testing

To verify the fix works:

```bash
# Test scaffolding scenario
curl -X POST http://localhost:5678/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_123",
    "session_id": "test_scaffolding",
    "message": "idk",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 5?",
      "correct_answer": "2"
    }
  }'
```

**Expected tool output**:
```json
{
  "scaffolding_question": "Can you explain what you think happens...",
  "student_response": "idk",
  "problem_context": "What is -3 + 5?",
  "validation_guidelines": {
    "accept_text_numbers": true,
    "semantic_meaning": "Accept \"minus 2\" = \"-2\" = \"negative 2\"",
    "criteria": "correct|partially_correct|incorrect"
  }
}
```

**Expected classification**: `category: "stuck"`, `is_main_problem_attempt: false`

---

## Impact

This fix resolves the critical blocker that prevented:
1. ✅ Scaffolding validation from working
2. ✅ Main problem answer verification during scaffolding
3. ✅ AI Agent from properly classifying student responses
4. ✅ The entire adaptive tutoring flow from functioning

**Time saved for future developers**: Hours of debugging by documenting this n8n limitation.

---

## n8n Version Info

- **n8n Version**: 1.102.4 Self Hosted
- **AI Agent Node**: `@n8n/n8n-nodes-langchain.agent` typeVersion 2
- **Tool Code Node**: `@n8n/n8n-nodes-langchain.toolCode` typeVersion 1.2
- **Date**: October 2025

This behavior may change in future n8n versions, but as of October 2025, this is how tool parameter passing works (or doesn't work).

---

## Commit Message

```
fix: n8n tool parameters - use workflow context instead of function params

After hours of debugging, discovered that n8n AI Agent toolCode cannot
access OpenAI function call parameters in any form (not as global vars,
not in $input, not in $fromAI, not in arguments array).

Solution: Read from workflow context ($json) which contains all needed
data from "Prepare Agent Context" node:
- $json.student_message
- $json.scaffolding_last_question
- $json.current_problem.text
- $json.current_problem.correct_answer

Both tools (Validate Scaffolding, Verify Main Answer) now work correctly.

This fixes the critical scaffolding validation blocker and enables the
full adaptive tutoring flow.

See: BUG-FIX-N8N-TOOL-PARAMETERS.md for complete investigation details
```
