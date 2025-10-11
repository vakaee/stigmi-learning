# Bug Fix: Scaffolding Validation - Text Number Representations

**Date**: October 11, 2025
**Bug**: Student response "minus 2" to scaffolding question classified as "stuck" when it's the correct answer
**Expected**: Should be classified as "scaffold_progress"

---

## Root Cause

The scaffolding validation LLM was too strict with text number representations, failing to recognize semantic equivalence between different forms.

### What was happening:
1. Tutor asks scaffolding question: "What number do we get when we start at -3 and add 1?"
2. Student responds: "minus 2" (correct answer to -3 + 1)
3. Validation LLM compares:
   - Expected: "-2" (numeric form)
   - Student said: "minus 2" (text form)
4. Validation doesn't recognize these as equivalent
5. Returns `{"status": "incorrect"}`
6. Agent classifies as "stuck" instead of "scaffold_progress"
7. Tutor repeats the same scaffolding question instead of progressing

### Evidence from debug data:
```json
{
  "student_message": "minus 2",
  "classification": {
    "category": "stuck",
    "original_category": "stuck",
    "is_main_problem_attempt": false
  }
}
```

Should have been:
```json
{
  "category": "scaffold_progress"
}
```

### Why this happened:
The validation prompt in Tool: Validate Scaffolding (line 195) didn't include explicit instructions to accept text number representations as equivalent to numeric forms. The LLM was matching strings literally rather than semantically.

---

## The Fix

Enhanced the scaffolding validation prompt with explicit instructions and examples for text/numeric equivalence:

### Added Section 1: Critical Equivalence Rules
```
**CRITICAL: Accept text and numeric forms as equivalent**
- minus 2 = -2 = negative 2 = negative two
- five = 5
- zero = 0
- Focus on SEMANTIC MEANING, not exact string matching
```

### Added Section 2: Concrete Examples
```
EXAMPLES:
Question: What number do we get when we start at -3 and add 1?
- Student says minus 2 → CORRECT (equivalent to -2)
- Student says negative two → CORRECT (equivalent to -2)
- Student says -2 → CORRECT
- Student says 2 → INCORRECT (wrong sign)
```

### Updated Validation Criteria
Changed from:
```
- CORRECT: Demonstrates understanding, answer is accurate
```

To:
```
- CORRECT: Demonstrates understanding, answer is accurate (accept equivalent text/numeric forms)
```

---

## Expected Flow After Fix

**Input**: Student says "minus 2" in response to scaffolding question "What number do we get when we start at -3 and add 1?"

1. **AI Agent** calls `validate_scaffolding` tool with:
   - scaffolding_question: "What number do we get when we start at -3 and add 1?"
   - student_response: "minus 2"
   - problem_context: "What is -3 + 1?"

2. **Tool: Validate Scaffolding**:
   - LLM sees enhanced prompt with equivalence rules and examples
   - Recognizes "minus 2" = "-2"
   - Returns: `{"status": "correct", "reasoning": "Student correctly identified -2 using text form"}`

3. **AI Agent**:
   - Tool result shows `correct: true`
   - Returns: `{"category": "scaffold_progress", "is_main_problem_attempt": false, "confidence": 0.9}`

4. **Route to**: "Response: Scaffold Progress"

5. **Tutor response**: Acknowledges correct answer and asks next scaffolding step OR guides back to main problem

---

## Testing

To verify the fix works, test with the same conversation flow:

### Test Case 1: Text negative number
```bash
# Turn 1: Student gives wrong answer, tutor starts scaffolding
curl -X POST http://localhost:5678/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_123",
    "session_id": "test_scaffolding_text",
    "message": "1",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 1?",
      "correct_answer": "-2"
    }
  }'

# Turn 2: Student answers scaffolding question with text form
curl -X POST http://localhost:5678/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_123",
    "session_id": "test_scaffolding_text",
    "message": "minus 2",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 1?",
      "correct_answer": "-2"
    }
  }'
```

**Expected result for Turn 2**:
- `category: "scaffold_progress"`
- `is_main_problem_attempt: false`
- Tutor acknowledges and asks next step (not repeating same question)

### Test Case 2: Other text forms
Test variations:
- "negative 2" → should classify as scaffold_progress
- "negative two" → should classify as scaffold_progress
- "minus two" → should classify as scaffold_progress

### Test Case 3: Wrong sign
- Student says "2" (missing negative) → should classify as stuck (correctly identifies as wrong)

---

## Files Modified

- `/Users/Vlad/Dev/MinS/ai-tutor-poc/2-prototype/workflow-production-ready.json` (line 195)
  - Node: "Tool: Validate Scaffolding"
  - Updated validation prompt with equivalence rules and examples
  - Added CRITICAL section for text/numeric equivalence
  - Added EXAMPLES section demonstrating correct validation

---

## Related Issues

### Similar to BUG-FIX-WRITTEN-NUMBERS.md
This bug is conceptually similar to the earlier written numbers bug, but occurs at a different stage:
- **Earlier bug**: LLM extraction was "helpfully correcting" student answers
- **This bug**: LLM validation was too strict with text forms

Both required explicit instructions about literal extraction/semantic equivalence.

### Other text forms this should now handle:
- "negative five" → -5
- "minus ten" → -10
- "positive two" or "two" → 2
- Mixed forms like "the answer is minus 2" → -2

All should now be validated correctly with semantic understanding rather than string matching.

---

## Commit Message

```
fix: handle text number forms in scaffolding validation

Scaffolding validation was too strict with text representations,
classifying "minus 2" as incorrect when it's equivalent to "-2".
Added explicit instructions and examples to accept semantic equivalence
between text and numeric forms (minus 2 = -2 = negative two).

Fixes: Student saying "minus 2" gets stuck loop instead of progressing
```

---

## Impact

This fix ensures:
1. Students can express answers naturally in text form
2. Scaffolding progresses smoothly when students give correct answers
3. No stuck loops when students use text number representations
4. Consistent behavior between main problem extraction and scaffolding validation
