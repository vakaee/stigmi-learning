# Extending to New Questions - Genericity Guide

**Version**: 1.0
**Date**: October 18, 2025
**Status**: Production-Ready
**Branch**: `feature/unified-response-node`

---

## Table of Contents

1. [Overview](#overview)
2. [Three-Tier Genericity Model](#three-tier-genericity-model)
3. [Tier 1: Works Out-of-Box](#tier-1-works-out-of-box)
4. [Tier 2: Configuration Required](#tier-2-configuration-required)
5. [Tier 3: New Validators Needed](#tier-3-new-validators-needed)
6. [Extension Examples](#extension-examples)
7. [Testing New Questions](#testing-new-questions)
8. [Migration Checklist](#migration-checklist)

---

## Overview

The Option A architecture is designed for **configuration-driven extensibility**. This guide explains:

- What types of questions work immediately (no changes needed)
- What types require configuration updates (no workflow changes)
- What types require new validators (workflow modifications)

---

## Three-Tier Genericity Model

### Tier 1: Works Out-of-Box
**Zero changes needed** - just add questions to your problem database

**Supported**:
- Basic arithmetic (addition, subtraction, multiplication, division)
- Negative numbers
- Decimals
- Simple word problems that reduce to arithmetic

**Why it works**:
- ERROR_DETECTORS covers all 4 arithmetic operations
- Numeric Verifier handles any numeric comparison
- Content Feature Extractor extracts numbers from text

**Example**:
```json
{
  "id": "arith_mult_1",
  "type": "math_arithmetic_multiplication",
  "text": "What is -4 × 3?",
  "correct_answer": "-12"
}
```

**No workflow changes** - system handles this immediately.

---

### Tier 2: Configuration Required
**Add patterns to registries** - no workflow changes needed

**Supported** (with config):
- Fractions
- Geometry (area, perimeter)
- Percentages
- Simple algebra (one-step equations)
- Order of operations
- New conceptual scaffolding questions

**Why configuration**:
- Need new ERROR_DETECTORS for error patterns
- Need new SEMANTIC_PATTERNS for conceptual validation
- Workflow structure remains unchanged

**Example**:
```json
{
  "id": "frac_add_1",
  "type": "math_fractions_addition",
  "text": "What is 1/4 + 1/2?",
  "correct_answer": "3/4"
}
```

**Configuration needed** (in `config_registries.js`):
```javascript
ERROR_DETECTORS['math_fractions_addition'] = (frac1, frac2) => [
  // Common errors
  (frac1.num + frac2.num) + '/' + (frac1.den + frac2.den), // Add num and den
  (frac1.num + frac2.num) + '/' + frac1.den,               // Forgot to find LCD
  // ... more patterns
];
```

---

### Tier 3: New Validators Needed
**Workflow modifications required** - add new validator nodes

**Examples**:
- Multiple choice questions
- Multi-step algebra (2+ operations)
- Fill-in-the-blank (multiple answers)
- Graphing/visual problems
- Open-ended conceptual questions

**Why new validators**:
- Different validation logic (not numeric comparison)
- New routing patterns
- Different state transitions

**Example**:
```json
{
  "id": "mcq_1",
  "type": "multiple_choice",
  "text": "Which operation gives a negative result? A) 3+5 B) -3+5 C) 3-5 D) -3-5",
  "correct_answer": "D"
}
```

**New validator needed**: Multiple Choice Validator

---

## Tier 1: Works Out-of-Box

### Arithmetic Operations

All four basic operations work immediately:

**Addition**:
```json
{"text": "What is -3 + 5?", "correct_answer": "2", "type": "math_arithmetic_addition"}
{"text": "What is 7.5 + 2.3?", "correct_answer": "9.8", "type": "math_arithmetic_addition"}
```

**Subtraction**:
```json
{"text": "What is 10 - 15?", "correct_answer": "-5", "type": "math_arithmetic_subtraction"}
{"text": "What is 3.2 - 1.8?", "correct_answer": "1.4", "type": "math_arithmetic_subtraction"}
```

**Multiplication**:
```json
{"text": "What is -4 × 3?", "correct_answer": "-12", "type": "math_arithmetic_multiplication"}
{"text": "What is 0.5 × 6?", "correct_answer": "3", "type": "math_arithmetic_multiplication"}
```

**Division**:
```json
{"text": "What is 15 ÷ 3?", "correct_answer": "5", "type": "math_arithmetic_division"}
{"text": "What is -20 ÷ 4?", "correct_answer": "-5", "type": "math_arithmetic_division"}
```

### Word Problems (Arithmetic)

```json
{
  "text": "Sarah has $5. She spends $8. How much does she have now?",
  "correct_answer": "-3",
  "type": "math_arithmetic_subtraction"
}
```

**Why it works**: Content Feature Extractor extracts numbers (5, 8), student answer is numeric.

### Error Detection

The system automatically detects these errors:

**Forgot negatives**: -3 + 5, student says "8"
- ERROR_DETECTORS: `[Math.abs(-3) + Math.abs(5)] = [8]`
- Category: wrong_operation

**Wrong operation**: -3 + 5, student says "-8"
- ERROR_DETECTORS: `[-3 - 5] = [-8]`
- Category: wrong_operation

**Close answer**: -3 + 5, student says "1.8"
- Diff: |1.8 - 2| = 0.2 < 20% of 2
- Category: close

---

## Tier 2: Configuration Required

### Fractions

**Step 1**: Add ERROR_DETECTORS

```javascript
// In config_registries.js

ERROR_DETECTORS['math_fractions_addition'] = (frac1, frac2) => {
  // Parse fractions: "1/4" → {num: 1, den: 4}
  const f1 = parseFraction(frac1);
  const f2 = parseFraction(frac2);

  return [
    // Error 1: Added numerators and denominators separately
    `${f1.num + f2.num}/${f1.den + f2.den}`,  // 1/4 + 1/2 → 2/6

    // Error 2: Added numerators, kept first denominator
    `${f1.num + f2.num}/${f1.den}`,  // 1/4 + 1/2 → 2/4

    // Error 3: Found LCD but forgot to multiply numerators
    `${f1.num + f2.num}/${lcm(f1.den, f2.den)}`,  // 1/4 + 1/2 → 2/4

    // Error 4: Decimal answer (forgot to convert back)
    String((f1.num / f1.den) + (f2.num / f2.den))  // 0.75
  ];
};
```

**Step 2**: Add SEMANTIC_PATTERNS (for scaffolding)

```javascript
SEMANTIC_PATTERNS['math_fractions_lcd'] = {
  patterns: [{
    questionPatterns: ['same denominator', 'common denominator'],
    expectedKeywords: {
      'yes': ['yes', 'same', 'equal', 'common'],
      'no': ['no', 'different', 'not same']
    }
  }]
};
```

**Step 3**: Update problem format

```json
{
  "id": "frac_add_1",
  "type": "math_fractions_addition",
  "text": "What is 1/4 + 1/2?",
  "correct_answer": "3/4",
  "metadata": {
    "frac1": "1/4",
    "frac2": "1/2"
  }
}
```

**No workflow changes needed** - Enhanced Numeric Verifier calls ERROR_DETECTORS['math_fractions_addition'].

---

### Geometry (Area/Perimeter)

**Step 1**: Add ERROR_DETECTORS

```javascript
ERROR_DETECTORS['math_geometry_rectangle_area'] = (length, width) => [
  // Error 1: Calculated perimeter instead
  2 * (length + width),

  // Error 2: Added instead of multiplied
  length + width,

  // Error 3: Forgot one dimension
  length,
  width
];
```

**Step 2**: Add SEMANTIC_PATTERNS

```javascript
SEMANTIC_PATTERNS['math_geometry_formula_identification'] = {
  patterns: [{
    questionPatterns: ['area or perimeter', 'area formula'],
    expectedKeywords: {
      'area': ['area', 'multiply', 'length times width', 'l × w'],
      'perimeter': ['perimeter', 'add', 'around']
    }
  }]
};
```

**Step 3**: Update Enhanced Numeric Verifier to parse problem metadata

```javascript
// In Enhanced Numeric Verifier
const problemType = input.current_problem.type;
const metadata = input.current_problem.metadata || {};

if (problemType === 'math_geometry_rectangle_area') {
  const errorDetector = ERROR_DETECTORS[problemType];
  const errors = errorDetector(metadata.length, metadata.width);
  // ... rest of validation
}
```

**Example problem**:
```json
{
  "id": "geom_area_1",
  "type": "math_geometry_rectangle_area",
  "text": "A rectangle is 5 cm long and 3 cm wide. What is its area?",
  "correct_answer": "15",
  "metadata": {
    "length": 5,
    "width": 3
  }
}
```

---

### Percentages

**Step 1**: Add ERROR_DETECTORS

```javascript
ERROR_DETECTORS['math_percentages_of_number'] = (percent, number) => [
  // Error 1: Forgot to divide by 100
  percent * number,  // 25% of 80 → 2000 instead of 20

  // Error 2: Divided instead of multiplied
  number / percent,  // 25% of 80 → 3.2

  // Error 3: Got decimal, didn't convert
  (percent / 100) * number  // Might get 20.0 instead of 20
];
```

**Example**:
```json
{
  "id": "pct_1",
  "type": "math_percentages_of_number",
  "text": "What is 25% of 80?",
  "correct_answer": "20",
  "metadata": {
    "percent": 25,
    "number": 80
  }
}
```

---

### Simple Algebra (One-Step Equations)

**Step 1**: Add ERROR_DETECTORS

```javascript
ERROR_DETECTORS['math_algebra_one_step'] = (equation, operation, operand) => {
  // For "x + 5 = 12", operation = "+", operand = 5

  if (operation === '+') {
    return [
      12 + 5,   // Added instead of subtracted
      5 - 12,   // Reversed order
      12 * 5,   // Multiplied
      12 / 5    // Divided
    ];
  }
  // ... other operations
};
```

**Step 2**: Add problem format

```json
{
  "id": "alg_1",
  "type": "math_algebra_one_step",
  "text": "Solve for x: x + 5 = 12",
  "correct_answer": "7",
  "metadata": {
    "operation": "+",
    "operand": 5,
    "result": 12
  }
}
```

---

## Tier 3: New Validators Needed

### Multiple Choice Questions

**Problem**: Student answer is "A", "B", "C", or "D" (not numeric).

**Solution**: Create Multiple Choice Validator

**Step 1**: Create new validator node

```javascript
// Multiple Choice Validator (Code node)
const input = $input.first().json;
const studentAnswer = (input.student_message || '').toUpperCase().trim();
const correctAnswer = input.current_problem.correct_answer.toUpperCase();

// Normalize: "A", "a", "option A", "choice A" → "A"
const normalized = studentAnswer.match(/[ABCD]/)?.[0] || studentAnswer;

if (normalized === correctAnswer) {
  return {
    json: {
      ...input,
      category: 'correct',
      is_main_problem_attempt: true,
      confidence: 1.0
    }
  };
} else {
  return {
    json: {
      ...input,
      category: 'wrong_answer',
      is_main_problem_attempt: true,
      confidence: 1.0,
      selected_option: normalized
    }
  };
}
```

**Step 2**: Update Content-Based Router

```javascript
// Add routing for multiple choice
if (messageType === 'answer_attempt' && problemType === 'multiple_choice') {
  route = 'multiple_choice_validator';
} else if (messageType === 'answer_attempt') {
  // ... existing numeric routing
}
```

**Step 3**: Add to Route by Content Type switch

Add 5th output: `multiple_choice_validator`

**Step 4**: Update Response: Unified with new category

```javascript
// In Response: Unified prompt
: $json.category == 'wrong_answer' ?
  'Student selected wrong multiple choice option: ' + $json.selected_option + '...'
```

---

### Fill-in-the-Blank (Multiple Answers)

**Problem**: Student needs to provide 2+ answers (e.g., "What are the factors of 12? ___ and ___")

**Solution**: Create Multi-Answer Validator

**Step 1**: Create validator

```javascript
// Multi-Answer Validator
const input = $input.first().json;
const studentAnswers = input.extracted_answers || [];  // Feature Extractor provides array
const correctAnswers = input.current_problem.correct_answers || [];  // Array of correct answers

const allCorrect = correctAnswers.every(ans =>
  studentAnswers.some(sAns => Math.abs(parseFloat(sAns) - parseFloat(ans)) < 0.001)
);

const someCorrect = correctAnswers.some(ans =>
  studentAnswers.some(sAns => Math.abs(parseFloat(sAns) - parseFloat(ans)) < 0.001)
);

if (allCorrect && studentAnswers.length === correctAnswers.length) {
  return {json: {...input, category: 'correct'}};
} else if (someCorrect) {
  return {json: {...input, category: 'partial', correct_count: studentAnswers.length}};
} else {
  return {json: {...input, category: 'wrong_answer'}};
}
```

**Step 2**: Update Content Feature Extractor prompt

```
If the question asks for multiple answers, extract all numbers mentioned:
{"extracted_answers": [1, 2, 3, 4, 6, 12], "message_type": "answer_attempt"}
```

---

### Open-Ended Conceptual Questions

**Problem**: "Explain why -3 + 5 = 2" (no single correct answer, need LLM evaluation)

**Solution**: Create Conceptual Answer Evaluator (LLM-based)

**Step 1**: Create LLM evaluator node

```javascript
// Node: Conceptual Answer Evaluator (OpenAI)
// Temperature: 0.1 (deterministic grading)

Prompt:
You are evaluating a student's explanation for correctness.

Problem: {{$json.current_problem.text}}
Correct Answer: {{$json.current_problem.correct_answer}}
Student Explanation: {{$json.student_message}}

Evaluate if the student's explanation demonstrates understanding of the concept.

Return JSON:
{
  "category": "correct" | "partially_correct" | "incorrect",
  "key_concepts_mentioned": [...],
  "missing_concepts": [...],
  "confidence": 0.0-1.0
}
```

**Step 2**: Add routing

```javascript
// In Content-Based Router
if (messageType === 'conceptual_explanation' && problemType === 'open_ended') {
  route = 'conceptual_answer_evaluator';
}
```

---

## Extension Examples

### Example 1: Adding Fractions Support

**Goal**: Support fraction addition questions

**Steps**:

1. Add ERROR_DETECTORS pattern (see Tier 2 above)
2. Add SEMANTIC_PATTERNS for scaffolding
3. Update Enhanced Numeric Verifier to handle fraction parsing
4. Test with exemplar questions

**Files modified**:
- `config_registries.js` (add patterns)
- Enhanced Numeric Verifier node (add fraction parsing)

**Workflow changes**: None

**Testing**:
```bash
curl -X POST /webhook/tutor/message -d '{
  "student_id": "test",
  "session_id": "test",
  "message": "2/6",
  "current_problem": {
    "id": "frac_1",
    "type": "math_fractions_addition",
    "text": "What is 1/4 + 1/2?",
    "correct_answer": "3/4",
    "metadata": {"frac1": "1/4", "frac2": "1/2"}
  }
}'
```

**Expected**: Category: wrong_operation (2/6 is in ERROR_DETECTORS)

---

### Example 2: Adding Chemistry pH Problems

**Goal**: Support pH calculation questions

**Steps**:

1. Add ERROR_DETECTORS:
```javascript
ERROR_DETECTORS['chemistry_ph_calculation'] = (h_concentration) => [
  7 - h_concentration,           // Reversed pH scale
  -Math.log10(h_concentration),  // Forgot negative sign
  Math.log(h_concentration),     // Used ln instead of log10
  h_concentration                // Didn't take log at all
];
```

2. Add SEMANTIC_PATTERNS:
```javascript
SEMANTIC_PATTERNS['chemistry_acid_base'] = {
  patterns: [{
    questionPatterns: ['acid or base', 'acidic or basic'],
    expectedKeywords: {
      'acid': ['acid', 'acidic', 'pH < 7', 'low pH'],
      'base': ['base', 'basic', 'pH > 7', 'high pH']
    }
  }]
};
```

3. Update Enhanced Numeric Verifier to calculate pH errors:
```javascript
if (problemType === 'chemistry_ph_calculation') {
  const h_conc = metadata.h_concentration;
  const errors = ERROR_DETECTORS[problemType](h_conc);
  // ... validation
}
```

**Files modified**:
- `config_registries.js`
- Enhanced Numeric Verifier node

**Workflow changes**: None

---

### Example 3: Adding History Timeline Questions

**Goal**: Support "Was event X before or after year Y?" questions

**Steps**:

1. This is Tier 3 (needs new validator for date comparison)

2. Create Timeline Validator:
```javascript
const input = $input.first().json;
const eventYear = input.current_problem.metadata.event_year;
const referenceYear = input.current_problem.metadata.reference_year;
const studentAnswer = input.student_message.toLowerCase();

const correctAnswer = eventYear < referenceYear ? 'before' : 'after';

if (studentAnswer.includes(correctAnswer)) {
  return {json: {...input, category: 'correct'}};
} else {
  return {json: {...input, category: 'wrong_answer'}};
}
```

3. Add routing logic

4. Update Response: Unified

**Files modified**:
- workflow-production-ready.json (add Timeline Validator node)
- Content-Based Router (add routing)
- Route by Content Type (add output)

**Workflow changes**: Yes (new node + connections)

---

## Testing New Questions

### Test Checklist

For each new question type:

1. **Content Feature Extractor Test**
   - Does it correctly extract message_type?
   - Does it extract numeric_value / keywords correctly?

2. **Routing Test**
   - Does Content-Based Router route correctly?
   - Does correct validator execute?

3. **Validation Test**
   - Correct answer → category: correct ✓
   - Close answer → category: close ✓
   - Operation error → category: wrong_operation ✓
   - Random wrong → category: stuck ✓

4. **Response Generation Test**
   - Response is pedagogically appropriate
   - Response references numbers from problem
   - Response adapts to attempt count

5. **Scaffolding Test**
   - After 2 wrong attempts, scaffolding initiates
   - Scaffolding question is relevant
   - Correct scaffolding answer → scaffold_progress
   - Scaffolding heuristic works (if numeric)

6. **Teach-Back Test**
   - Correct answer triggers teach-back
   - Explanation acknowledged appropriately
   - "I don't know" provides solution

### Test Template

```javascript
// Test: [Question Type] - [Scenario]

const testRequest = {
  student_id: "test_student",
  session_id: "test_session",
  message: "[student answer]",
  current_problem: {
    id: "test_[type]_1",
    type: "[problem_type]",
    text: "[problem text]",
    correct_answer: "[correct answer]",
    metadata: { /* ... */ }
  }
};

// Expected response
{
  output: "[expected tutor response]",
  metadata: {
    category: "[expected category]",
    confidence: [0.0-1.0],
    // ...
  }
}
```

---

## Migration Checklist

### For Tier 1 (Out-of-Box)
- [ ] Add questions to problem database
- [ ] Verify `type` field matches existing ERROR_DETECTORS key
- [ ] Test with correct, close, wrong, and operation error answers
- [ ] Verify scaffolding works

### For Tier 2 (Configuration)
- [ ] Add ERROR_DETECTORS pattern to `config_registries.js`
- [ ] Add SEMANTIC_PATTERNS for scaffolding (if needed)
- [ ] Update validator to parse metadata (if needed)
- [ ] Import updated workflow to n8n
- [ ] Test all validation scenarios
- [ ] Test scaffolding scenarios
- [ ] Test teach-back

### For Tier 3 (New Validators)
- [ ] Design new validator logic
- [ ] Create validator node in workflow
- [ ] Update Content-Based Router with new routing logic
- [ ] Add output to Route by Content Type switch
- [ ] Update Response: Unified with new category handlers
- [ ] Create connections
- [ ] Import workflow to n8n
- [ ] Test all scenarios
- [ ] Update documentation
- [ ] Create migration guide for production

---

## Summary

**Tier 1** (Arithmetic): Add questions → works immediately
**Tier 2** (Configured): Add patterns → test → deploy
**Tier 3** (New validators): Design → implement → test → deploy

The system's architecture prioritizes **Tier 2 extensibility** - most new math subjects can be added via configuration without workflow changes.

For questions outside mathematics, **Tier 3** validators are likely needed, but the core orchestration pattern (Content Feature Extractor → Router → Validator → Response) remains the same.

**Recommendation**: Start with Tier 1 and 2 extensions to validate the architecture before attempting Tier 3 modifications.
