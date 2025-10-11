# Bug Fix: Written Numbers Misclassification

**Date**: October 9, 2025
**Bug**: Student input "one" was classified as "correct" when the answer is "2"
**Expected**: Should be classified as "wrong_operation"

---

## Root Cause

The LLM extraction prompt (in "LLM: Extract Intent & Value" node) had an ambiguity that caused GPT-4o-mini to be "too helpful":

### What was happening:
1. Student says "one"
2. LLM sees:
   - Problem: "What is -3 + 5?"
   - Student's Message: "one"
3. LLM calculates -3 + 5 = 2 (it knows math)
4. LLM thinks: "The student probably meant to say 'two' since that's the correct answer"
5. LLM **helpfully "corrects"** the extraction: `{"extracted_value": 2}` instead of 1
6. Code verification: `2 == 2` → classified as "correct"

### Why this happened:
The prompt said "Extract the numeric value (convert written numbers to digits)" but didn't explicitly say **"extract EXACTLY what the student said, NOT what you think they meant"**.

GPT-4o-mini has a bias toward being helpful, so it was inferring intent rather than literally extracting.

---

## The Fix

Added a **CRITICAL EXTRACTION RULE** section to the prompt:

```
**CRITICAL EXTRACTION RULE**:
Extract EXACTLY what the student SAID, NOT what you think they MEANT.
- If student says "one", extract 1 (even if the correct answer is 2)
- If student says "eight", extract 8 (even if the correct answer is 2)
- DO NOT "correct" the student's answer - extract their stated value literally
- Your job is extraction, NOT evaluation of correctness
```

Also added negative examples to reinforce this:

```
Student: "one" (Problem: "What is -3 + 5?")
→ {"is_answer": true, "category": "answer", "extracted_value": 1, ...}

Student: "eight" (Problem: "What is -3 + 5?")
→ {"is_answer": true, "category": "answer", "extracted_value": 8, ...}
```

The examples now show the problem context in parentheses, making it crystal clear that even when the correct answer is 2, "one" should extract as 1.

---

## Expected Flow After Fix

**Input**: `{message: "one", current_problem: {text: "What is -3 + 5?", correct_answer: "2"}}`

1. **LLM Extract**: `{is_answer: true, extracted_value: 1}`
2. **Code Verify**:
   - `diff = |1 - 2| = 1`
   - `threshold = max(0.4, 0.3) = 0.4`
   - `1 > 0.4` → `finalCategory = 'wrong_operation'`
3. **Route to**: "Response: Wrong Operation"
4. **Tutor response**: Socratic question to address misconception

---

## Testing

To verify the fix works, test with:

```bash
curl -X POST http://localhost:5678/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_123",
    "session_id": "test_written_numbers",
    "message": "one",
    "current_problem": {
      "id": "neg_add_1",
      "text": "What is -3 + 5?",
      "correct_answer": "2"
    }
  }'
```

**Expected result**:
- `category: "wrong_operation"`
- `is_main_problem_attempt: true`
- Tutor asks a clarifying question about the operation

---

## Files Modified

- `/Users/Vlad/Dev/MinS/ai-tutor-poc/2-prototype/workflow-production-ready.json` (line 137)
  - Node: "LLM: Extract Intent & Value"
  - Added CRITICAL EXTRACTION RULE section
  - Updated examples with problem context

---

## Related Issues

This same issue could occur with other written numbers:
- "two" when correct answer is 5
- "ten" when correct answer is 2
- "zero" when correct answer is 8

All should now be handled correctly with the explicit extraction rule.

---

## Commit Message

```
fix: prevent LLM from "correcting" student's written number answers

The LLM was inferring intent (student says "one" but means "two")
rather than literally extracting the stated value. Added explicit
instruction to extract EXACTLY what student said, NOT what we think
they meant. Added negative examples to reinforce literal extraction.

Fixes: Student input "one" classified as correct when answer is "2"
```
