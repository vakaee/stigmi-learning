# Option A Implementation Guide - Configurable Architecture

**Date**: October 17, 2025
**Version**: Option A+ (with configuration registries)
**Estimated Effort**: 2-3 days

---

## OVERVIEW

This guide implements Option A with **configuration over hardcoding** for extensibility.

**Key Principle**: New subjects/ages can be added via `config_registries.js` WITHOUT modifying workflow nodes.

---

## CONFIGURATION REGISTRIES

All configurable patterns are in: `/2-prototype/config_registries.js`

### Registries Available

1. **ERROR_DETECTORS**: Plausible operation error patterns by subject
2. **SEMANTIC_PATTERNS**: Keyword matching patterns for conceptual validation
3. **SUBJECT_CONFIG**: Validator selection and feature extraction per subject
4. **AGE_GROUP_CONFIG**: Response template customizations by age

### Adding New Subjects

```javascript
// In config_registries.js

// 1. Add error detector (if numeric subject)
ERROR_DETECTORS['chemistry_ph_calculation'] = (h_concentration) => {
  return [
    // Common pH calculation errors
  ];
};

// 2. Add semantic patterns (if conceptual validation needed)
SEMANTIC_PATTERNS['chemistry_acid_base'] = {
  patterns: [...]
};

// 3. Add subject config
SUBJECT_CONFIG['chemistry_ph'] = {
  validator: 'numeric',
  errorDetector: (problemText) => 'chemistry_ph_calculation',
  featureExtractor: {
    keywords: ['acid', 'base', 'neutral', 'pH'],
    concepts: ['hydrogen ion', 'concentration']
  }
};
```

**That's it.** No workflow changes needed.

---

## NODE IMPLEMENTATIONS

### Node 1: Content Feature Extractor (OpenAI)

**Purpose**: Extract all features needed for routing

**Type**: `@n8n/n8n-nodes-langchain.openAi`

**Prompt Template**:
```javascript
=`You are a content feature extractor for a tutoring system.

Problem Type: {{ $json.current_problem.type || 'math_arithmetic' }}
Problem: {{ $json.current_problem.text }}
Correct Answer: {{ $json.current_problem.correct_answer }}
Student Message: "{{ $json.student_message }}"
Age Group: {{ $json.age_group || 'grades_3-5' }}

${(() => {
  // Load configuration
  const configModule = require('./config_registries.js');
  const problemType = $json.current_problem.type || 'math_arithmetic';
  const extractConfig = configModule.getFeatureExtractionConfig(problemType);

  if (!extractConfig) {
    return 'Extract: message_type, numeric_value, keywords, confidence';
  }

  return `
FEATURE EXTRACTION FOR THIS SUBJECT:

Keywords to look for: ${extractConfig.keywords.join(', ')}
${extractConfig.directions ? 'Directions: ' + extractConfig.directions.join(', ') : ''}
${extractConfig.concepts ? 'Concepts: ' + extractConfig.concepts.join(', ') : ''}
`;
})()}

Extract these features:

1. MESSAGE TYPE:
   - answer_attempt: Contains numeric answer
   - conceptual_response: Contains conceptual keywords
   - question: Asks a question
   - help_request: "I don't know", "help me"
   - off_topic: Unrelated to problem

2. NUMERIC VALUE (if answer_attempt):
   - Extract the number from message
   - Convert written numbers: "two" → 2, "negative three" → -3
   - Handle expressions: "1/2" → 0.5
   - If multiple numbers, extract ANSWER (not process)
   Example: "that's 5 steps and we get 2" → extract 2

3. KEYWORDS (if conceptual_response):
   - Extract keywords from the list above that appear in student message
   - Include synonyms and variations

4. CONFIDENCE:
   - 0.9-1.0: Clear extraction
   - 0.7-0.9: Reasonably clear
   - 0.0-0.7: Ambiguous

Return ONLY valid JSON:
{
  "message_type": "answer_attempt" | "conceptual_response" | "question" | "help_request" | "off_topic",
  "numeric_value": number | null,
  "keywords": string[] | null,
  "confidence": number
}

CRITICAL: Extract what student SAID, not what you think they MEANT.`
```

**Settings**:
- Model: gpt-4o-mini
- Temperature: 0.1 (deterministic)
- Max tokens: 200

---

### Node 2: Content-Based Router (Code)

**Purpose**: Route to appropriate validator based on content

**Type**: `n8n-nodes-base.code`

**JavaScript**:
```javascript
// Content-Based Router
const features = $input.first().json;
const context = $('Load Session').first().json;

const messageType = features.message_type;
const isScaffolding = context.is_scaffolding_active;
const isTeachBack = context.is_teach_back_active;

// Route based on message type and context
let route;

if (isTeachBack) {
  // During teach-back, any response is explanation attempt
  route = 'teach_back_response';

} else if (messageType === 'answer_attempt') {
  // Numeric answer - check if main problem or scaffolding sub-answer

  if (isScaffolding) {
    // During scaffolding, check if looks like main problem attempt
    const numericValue = features.numeric_value;
    const correctAnswer = context.current_problem.correct_answer;
    const correctValue = parseFloat(String(correctAnswer).replace(/[^0-9.\-]/g, ''));

    // If number is reasonably close to correct answer, likely main problem attempt
    const diff = Math.abs(numericValue - correctValue);
    const threshold = Math.abs(correctValue * 0.5); // Within 50%
    const isLikelyMainProblem = diff < Math.max(threshold, 1);

    route = isLikelyMainProblem ? 'verify_numeric' : 'validate_conceptual';
  } else {
    route = 'verify_numeric';
  }

} else if (messageType === 'conceptual_response') {
  // Conceptual answer - needs semantic validation
  route = 'validate_conceptual';

} else if (messageType === 'question') {
  route = 'classify_question';

} else if (messageType === 'help_request') {
  route = 'classify_stuck';

} else {
  // off_topic or unknown
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

### Node 3: Enhanced Numeric Verifier (Code)

**Purpose**: Verify numeric answers AND detect operation errors using configuration

**Type**: `n8n-nodes-base.code`

**JavaScript**:
```javascript
// Enhanced Numeric Verifier with Configurable Error Detection
const input = $input.first().json;
const studentValue = input.numeric_value;
const correctAnswer = input.current_problem.correct_answer;
const problemText = input.current_problem.text;
const problemType = input.current_problem.type || 'math_arithmetic';

// Load configuration
const configModule = require('./config_registries.js');

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
      reasoning: `Cannot verify: ${error.message}`,
      _merged: true
    }
  };
}

// Validate numeric value
if (studentValue === null || isNaN(studentValue)) {
  return {
    json: {
      category: 'stuck',
      is_main_problem_attempt: true,
      confidence: 0.8,
      reasoning: 'Could not extract valid numeric value',
      _merged: true
    }
  };
}

// Calculate difference
const diff = Math.abs(studentValue - correctValue);

// Check if correct
if (diff < 0.001) {
  return {
    json: {
      category: 'correct',
      is_main_problem_attempt: true,
      confidence: 1.0,
      reasoning: `Student answered ${studentValue}, correct!`,
      _merged: true
    }
  };
}

// Check if close (within 20% threshold)
const percentThreshold = Math.abs(correctValue * 0.2);
const closeThreshold = Math.max(percentThreshold, 0.3);

if (diff <= closeThreshold) {
  return {
    json: {
      category: 'close',
      is_main_problem_attempt: true,
      confidence: 0.9,
      reasoning: `Student answered ${studentValue}, close to ${correctValue} (diff: ${diff.toFixed(2)})`,
      _merged: true
    }
  };
}

// Check if plausible operation error (using configuration)
const errorDetector = configModule.getErrorDetector(problemType, problemText);

if (errorDetector) {
  // Parse operation and numbers from problem
  const match = problemText.match(/([\-\d.]+)\s*([+\-*/])\s*([\-\d.]+)/);

  if (match) {
    const num1 = parseFloat(match[1]);
    const operation = match[2];
    const num2 = parseFloat(match[3]);

    // Get possible errors from configuration
    const possibleErrors = errorDetector(num1, num2, operation);

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
          reasoning: `Student answered ${studentValue}, likely operation misconception`,
          _merged: true
        }
      };
    }
  }
}

// Not correct, not close, not operation error → stuck
return {
  json: {
    category: 'stuck',
    is_main_problem_attempt: true,
    confidence: 0.85,
    reasoning: `Student answered ${studentValue}, not close to ${correctValue}, doesn't match operation errors`,
    _merged: true
  }
};
```

---

### Node 4: Semantic Validator (Code)

**Purpose**: Validate conceptual answers using configuration patterns

**Type**: `n8n-nodes-base.code`

**JavaScript**:
```javascript
// Semantic Validator - Configurable Pattern Matching
const input = $input.first().json;
const studentMessage = (input.student_message || '').toLowerCase();
const scaffoldingQuestion = (input.scaffolding_last_question || '').toLowerCase();
const keywords = input.keywords || [];
const problemText = input.current_problem.text || '';

// Load configuration
const configModule = require('./config_registries.js');
const problemType = input.current_problem.type || 'math_arithmetic';
const patterns = configModule.getSemanticPatterns(problemType);

let isCorrect = false;
let reasoning = '';
let needsLLMValidation = false;

// Try to match against configured patterns
patternLoop: for (const [patternType, patternConfig] of Object.entries(patterns)) {
  for (const pattern of patternConfig.patterns) {
    // Check if scaffolding question matches this pattern
    const questionMatches = pattern.questionPatterns.some(qp =>
      scaffoldingQuestion.includes(qp.toLowerCase())
    );

    if (!questionMatches) continue;

    // Pattern matched - now validate student response

    if (pattern.expectedKeywords) {
      // Pattern has conditional expected keywords (e.g., based on operation)
      // Determine which set of keywords to use

      let expectedSet = [];
      let wrongSet = [];

      // For operation identification: check what operation is in the problem
      if (patternType === 'math_operation_identification') {
        if (problemText.includes('+') && !problemText.includes('+ -')) {
          expectedSet = pattern.expectedKeywords['+'];
          wrongSet = pattern.wrongKeywords['+'];
        } else if (problemText.includes('-') && !problemText.includes('+ -')) {
          expectedSet = pattern.expectedKeywords['-'];
          wrongSet = pattern.wrongKeywords['-'];
        }
      }
      // For direction identification: check if positive or negative
      else if (patternType === 'math_direction_identification') {
        if (problemText.match(/\+\s*\d/) || scaffoldingQuestion.includes('positive')) {
          expectedSet = pattern.expectedKeywords['positive'];
          wrongSet = pattern.wrongKeywords['positive'];
        } else if (problemText.match(/\-\s*\d/) || scaffoldingQuestion.includes('negative')) {
          expectedSet = pattern.expectedKeywords['negative'];
          wrongSet = pattern.wrongKeywords['negative'];
        }
      }

      if (expectedSet.length > 0) {
        const hasCorrect = keywords.some(kw => expectedSet.includes(kw));
        const hasWrong = keywords.some(kw => wrongSet.includes(kw));

        if (hasCorrect && !hasWrong) {
          isCorrect = true;
          reasoning = `Student correctly identified concept`;
        } else if (hasWrong) {
          isCorrect = false;
          reasoning = `Student gave incorrect answer`;
        } else {
          // Ambiguous - needs LLM
          needsLLMValidation = true;
        }

        break patternLoop;
      }
    } else if (pattern.expectedKeywords && !pattern.wrongKeywords) {
      // Simple expected keywords list
      const hasExpected = keywords.some(kw =>
        pattern.expectedKeywords.includes(kw)
      );

      if (hasExpected) {
        isCorrect = true;
        reasoning = 'Student used expected keyword';
        break patternLoop;
      }
    }
  }
}

// If no pattern matched or ambiguous, use LLM fallback
if (needsLLMValidation || reasoning === '') {
  return {
    json: {
      ...input,
      _needs_llm_validation: true,
      _merged: false
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
      reasoning: reasoning,
      _merged: true
    }
  };
} else {
  return {
    json: {
      category: 'stuck',
      is_main_problem_attempt: false,
      confidence: 0.9,
      reasoning: reasoning,
      _merged: true
    }
  };
}
```

---

### Node 5: Semantic Validator LLM Fallback (OpenAI)

**Purpose**: Handle ambiguous conceptual answers that pattern matching can't determine

**Type**: `@n8n/n8n-nodes-langchain.openAi`

**Input Filter**: Only if `_needs_llm_validation === true`

**Prompt**:
```javascript
=`You validate conceptual answers to scaffolding questions.

Scaffolding Question: "{{ $json.scaffolding_last_question }}"
Student Response: "{{ $json.student_message }}"
Problem Context: {{ $json.current_problem.text }}

Is the student's response semantically CORRECT for this scaffolding question?

Examples:
Q: "What does -3 mean?"
- "negative 3" → correct
- "3 left of zero" → correct
- "positive 3" → WRONG

Q: "When we see +, are we adding or subtracting?"
- "adding" → correct
- "subtracting" → WRONG

Return ONLY valid JSON:
{
  "is_correct": true | false,
  "confidence": number,
  "reasoning": "brief explanation"
}`
```

**Post-Processing Code Node**:
```javascript
// Convert LLM fallback result to standard format
const llmResult = $input.first().json.message.content;
const parsed = JSON.parse(llmResult);
const context = $('Content-Based Router').first().json;

return {
  json: {
    category: parsed.is_correct ? 'scaffold_progress' : 'stuck',
    is_main_problem_attempt: false,
    confidence: parsed.confidence,
    reasoning: `LLM validation: ${parsed.reasoning}`,
    _merged: true
  }
};
```

---

### Node 6: Update Response: Unified for Age Groups

**Changes to existing node**: Make age group configurable

**Find this line** in Response: Unified:
```javascript
'You are a patient, encouraging math tutor for grades 3-5 (ages 8-10).'
```

**Replace with**:
```javascript
=${(() => {
  const configModule = require('./config_registries.js');
  const ageGroup = $json.age_group || 'grades_3-5';
  const ageConfig = configModule.getAgeGroupConfig(ageGroup);

  return `You are a patient, encouraging math tutor for ${ageConfig.label}.

LANGUAGE GUIDELINES:
- Vocabulary: ${ageConfig.vocabulary}
- Sentence length: ${ageConfig.sentenceLength}
- Examples: ${ageConfig.examples}`;
})()}
```

**Result**: Age group is now configurable via session `age_group` field.

---

## WORKFLOW CONNECTIONS

### Complete Flow

```
1. Webhook Trigger
   ↓
2. Normalize input
   ↓
3. Redis: Get Session
   ↓
4. Load Session
   ↓
5. Content Feature Extractor (NEW - OpenAI)
   ↓
6. Content-Based Router (NEW - Code)
   ↓
7. Switch on _route:
   ├─ verify_numeric → Enhanced Numeric Verifier (ENHANCED - Code)
   ├─ validate_conceptual → Semantic Validator (NEW - Code)
   │                       → (if _needs_llm_validation) → LLM Fallback (NEW - OpenAI)
   ├─ classify_question → (reuse existing Stage 2 LLM)
   ├─ classify_stuck → Simple Code (return {category: 'stuck'})
   └─ classify_other → (reuse existing Stage 2 LLM)
   ↓
8. Route by Category (KEEP - existing Switch)
   ↓
9. Response: Unified (UPDATED - age-aware)
   ↓
10. Update Session & Format Response
    ↓
11. Redis: Save Session
    ↓
12. Webhook Response
```

### Nodes to Remove

- [ ] AI Agent
- [ ] Tool: Verify Main Answer
- [ ] Tool: Validate Scaffolding
- [ ] Switch: Scaffolding Active?
- [ ] Prepare Agent Context
- [ ] Parse Agent Output
- [ ] Format for Routing
- [ ] LLM: Extract Intent & Value (replaced by Content Feature Extractor)
- [ ] Code: Verify Answer (replaced by Enhanced Numeric Verifier)

---

## TESTING CHECKLIST

### Unit Tests

- [ ] Content Feature Extractor extracts numeric values correctly
- [ ] Content Feature Extractor extracts keywords correctly
- [ ] Content-Based Router routes numeric answers to verify_numeric
- [ ] Content-Based Router routes conceptual to validate_conceptual
- [ ] Enhanced Numeric Verifier: correct answer → "correct"
- [ ] Enhanced Numeric Verifier: close answer → "close"
- [ ] Enhanced Numeric Verifier: operation error (8) → "wrong_operation"
- [ ] Enhanced Numeric Verifier: random wrong (45) → "stuck"
- [ ] Semantic Validator: "adding" → "scaffold_progress"
- [ ] Semantic Validator: "subtracting" (wrong) → "stuck"
- [ ] LLM Fallback handles ambiguous cases

### Integration Tests

**The "45" Conversation** (all 4 bugs should be fixed):

- [ ] Turn 1: "45" → stuck (not wrong_operation)
- [ ] Turn 2: "subtract" → stuck (validated as wrong)
- [ ] Turn 3: "adding" → scaffold_progress (not correct main problem)
- [ ] Turn 4: Provides solution (not false praise)

**Other Scenarios**:

- [ ] Correct answer triggers teach-back
- [ ] Operation error (8) triggers clarification
- [ ] Scaffolding progress continues correctly
- [ ] Main problem during scaffolding exits correctly

### Regression Tests

- [ ] All exemplar questions still work
- [ ] Session state unchanged
- [ ] Performance ≤ 3.5 seconds

---

## EXTENSION GUIDE

### Adding a New Subject

**Example: Adding Chemistry pH problems**

1. **Add error detector** (if numeric):
```javascript
// In config_registries.js
ERROR_DETECTORS['chemistry_ph_calculation'] = (h_concentration) => {
  return [
    // Common errors
    7 - h_concentration,  // Reversed scale
    -Math.log10(h_concentration) // Forgot negative sign
  ];
};
```

2. **Add semantic patterns** (if conceptual):
```javascript
SEMANTIC_PATTERNS['chemistry_acid_base'] = {
  patterns: [{
    questionPatterns: ['acid or base', 'acidic or basic'],
    expectedKeywords: {
      'ph_less_than_7': ['acid', 'acidic'],
      'ph_greater_than_7': ['base', 'basic', 'alkaline']
    },
    wrongKeywords: {
      'ph_less_than_7': ['base', 'basic'],
      'ph_greater_than_7': ['acid', 'acidic']
    }
  }]
};
```

3. **Add subject config**:
```javascript
SUBJECT_CONFIG['chemistry_ph'] = {
  validator: 'numeric',
  errorDetector: (problemText) => 'chemistry_ph_calculation',
  featureExtractor: {
    keywords: ['acid', 'base', 'pH', 'neutral', 'acidic', 'basic'],
    concepts: ['hydrogen ion', 'hydroxide', 'concentration']
  }
};
```

4. **Use in problems**:
```json
{
  "id": "chem_ph_1",
  "type": "chemistry_ph",
  "text": "If [H+] = 0.001 M, what is the pH?",
  "correct_answer": "3"
}
```

**No workflow changes needed.**

---

### Adding a New Age Group

```javascript
// In config_registries.js
AGE_GROUP_CONFIG['college'] = {
  label: 'college level',
  vocabulary: 'technical',
  sentenceLength: '15-25 words',
  scaffoldingDepth: 'minimal',
  examples: 'abstract and theoretical'
};
```

**Use in session**:
```json
{
  "student_id": "123",
  "age_group": "college"
}
```

**No workflow changes needed.**

---

## DEPLOYMENT

### Step 1: Commit Configuration
```bash
git add config_registries.js
git commit -m "Add configuration registries for extensible validation"
```

### Step 2: Test Configuration
```bash
node -e "const c = require('./config_registries.js'); console.log(c.getErrorDetector('math_arithmetic', 'What is -3 + 5?'))"
```

### Step 3: Backup Workflow
```bash
cp workflow-production-ready.json workflow-production-ready-backup.json
```

### Step 4: Build New Nodes in n8n
- Create each node according to specifications above
- Test each node individually
- Connect nodes according to flow diagram

### Step 5: Test Integration
- Run "45" conversation test
- Run regression tests
- Verify performance

### Step 6: Deploy
```bash
git add workflow-production-ready.json
git commit -m "Implement Option A: unified classification with configurable architecture"
git push
```

---

## ROLLBACK PLAN

If issues arise:

```bash
cp workflow-production-ready-backup.json workflow-production-ready.json
# Re-import to n8n
```

Session compatibility: ✓ (schema unchanged)

---

## SUCCESS CRITERIA

- [x] Configuration registries created
- [ ] All new nodes implemented
- [ ] All old nodes removed
- [ ] "45" conversation: all 4 turns correct
- [ ] Operation error detection: 8 → wrong_operation, 45 → stuck
- [ ] Semantic validation: "adding" correct, "subtracting" wrong
- [ ] No regressions
- [ ] Performance ≤ 3.5s
- [ ] Documentation complete

---

## NEXT STEPS

1. Review this implementation guide
2. Create new branch: `refactor/option-a-configurable`
3. Implement nodes in n8n following this guide
4. Test incrementally
5. Deploy when all tests pass

Ready to build?
