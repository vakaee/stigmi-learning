#!/usr/bin/env python3
"""
Build Option A Workflow - Replaces dual classification with unified configurable flow

This script:
1. Removes old classification nodes (AI Agent, Switch: Scaffolding Active, etc.)
2. Adds new configurable nodes (Content Feature Extractor, Enhanced Numeric Verifier, etc.)
3. Updates all connections to create single classification path
4. Maintains all existing session management and response generation nodes
"""

import json
import uuid

def generate_uuid():
    """Generate n8n-compatible UUID"""
    return str(uuid.uuid4())

def create_content_feature_extractor_node():
    """Create Content Feature Extractor (OpenAI) node"""
    return {
        "parameters": {
            "modelId": {
                "__rl": True,
                "value": "gpt-4o-mini",
                "mode": "list",
                "cachedResultName": "gpt-4o-mini"
            },
            "messages": {
                "values": [
                    {
                        "content": """=`You are a content feature extractor for a tutoring system.

Problem Type: {{ $json.current_problem.type || 'math_arithmetic' }}
Problem: {{ $json.current_problem.text }}
Correct Answer: {{ $json.current_problem.correct_answer }}
Student Message: "{{ $json.student_message }}"

Extract these features:

1. MESSAGE TYPE:
   - answer_attempt: Contains numeric answer
   - conceptual_response: Contains conceptual keywords (operations, directions, concepts)
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
   Extract: adding, subtracting, multiplying, dividing, plus, minus, times,
   right, left, up, down, negative, positive, zero, number line

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

CRITICAL: Extract what student SAID, not what you think they MEANT.`"""
                    }
                ]
            },
            "options": {
                "temperature": 0.1,
                "maxTokens": 200
            }
        },
        "id": generate_uuid(),
        "name": "Content Feature Extractor",
        "type": "@n8n/n8n-nodes-langchain.openAi",
        "typeVersion": 1.3,
        "position": [1100, 300],
        "credentials": {
            "openAiApi": {
                "id": "PLACEHOLDER_OPENAI_CRED_ID",
                "name": "OpenAI account"
            }
        }
    }

def create_content_router_node():
    """Create Content-Based Router (Code) node"""
    js_code = """// Content-Based Router
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
    const correctValue = parseFloat(String(correctAnswer).replace(/[^0-9.\\-]/g, ''));

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
};"""

    return {
        "parameters": {
            "jsCode": js_code
        },
        "id": generate_uuid(),
        "name": "Content-Based Router",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1300, 300]
    }

def create_enhanced_numeric_verifier_node():
    """Create Enhanced Numeric Verifier (Code) node"""

    # Read the config file to embed it (since n8n Code nodes can't require external files in cloud)
    with open('config_registries.js', 'r') as f:
        config_code = f.read()

    # Extract just the ERROR_DETECTORS object
    start = config_code.find('const ERROR_DETECTORS = {')
    end = config_code.find('// ============================================================================', start + 1)
    error_detectors_code = config_code[start:end].strip()

    js_code = f"""// Enhanced Numeric Verifier with Configurable Error Detection

// Embedded configuration (ERROR_DETECTORS)
{error_detectors_code}

const input = $input.first().json;
const studentValue = input.numeric_value;
const correctAnswer = input.current_problem.correct_answer;
const problemText = input.current_problem.text;
const problemType = input.current_problem.type || 'math_arithmetic';

// Parse correct answer
let correctValue;
try {{
  correctValue = parseFloat(String(correctAnswer).replace(/[^0-9.\\-]/g, ''));
  if (isNaN(correctValue)) {{
    throw new Error('Cannot parse correct answer');
  }}
}} catch (error) {{
  return {{
    json: {{
      category: 'stuck',
      is_main_problem_attempt: true,
      confidence: 0.5,
      reasoning: `Cannot verify: ${{error.message}}`
    }}
  }};
}}

// Validate numeric value
if (studentValue === null || isNaN(studentValue)) {{
  return {{
    json: {{
      category: 'stuck',
      is_main_problem_attempt: true,
      confidence: 0.8,
      reasoning: 'Could not extract valid numeric value'
    }}
  }};
}}

// Calculate difference
const diff = Math.abs(studentValue - correctValue);

// Check if correct
if (diff < 0.001) {{
  return {{
    json: {{
      category: 'correct',
      is_main_problem_attempt: true,
      confidence: 1.0,
      reasoning: `Student answered ${{studentValue}}, correct!`
    }}
  }};
}}

// Check if close (within 20% threshold)
const percentThreshold = Math.abs(correctValue * 0.2);
const closeThreshold = Math.max(percentThreshold, 0.3);

if (diff <= closeThreshold) {{
  return {{
    json: {{
      category: 'close',
      is_main_problem_attempt: true,
      confidence: 0.9,
      reasoning: `Student answered ${{studentValue}}, close to ${{correctValue}} (diff: ${{diff.toFixed(2)}})`
    }}
  }};
}}

// Check if plausible operation error (using configuration)
// Parse operation and numbers from problem
const match = problemText.match(/([\\-\\d.]+)\\s*([+\\-*/])\\s*([\\-\\d.]+)/);

if (match) {{
  const num1 = parseFloat(match[1]);
  const operation = match[2];
  const num2 = parseFloat(match[3]);

  // Map operation to detector
  const operationMap = {{
    '+': 'math_arithmetic_addition',
    '-': 'math_arithmetic_subtraction',
    '*': 'math_arithmetic_multiplication',
    '/': 'math_arithmetic_division'
  }};

  const detectorKey = operationMap[operation];
  const errorDetector = ERROR_DETECTORS[detectorKey];

  if (errorDetector) {{
    // Get possible errors from configuration
    const possibleErrors = errorDetector(num1, num2, operation);

    // Check if student's answer matches any plausible error
    const isOperationError = possibleErrors.some(errorValue =>
      Math.abs(studentValue - errorValue) < 0.001
    );

    if (isOperationError) {{
      return {{
        json: {{
          category: 'wrong_operation',
          is_main_problem_attempt: true,
          confidence: 0.95,
          reasoning: `Student answered ${{studentValue}}, likely operation misconception`
        }}
      }};
    }}
  }}
}}

// Not correct, not close, not operation error → stuck
return {{
  json: {{
    category: 'stuck',
    is_main_problem_attempt: true,
    confidence: 0.85,
    reasoning: `Student answered ${{studentValue}}, not close to ${{correctValue}}, doesn't match operation errors`
  }}
}};"""

    return {
        "parameters": {
            "jsCode": js_code
        },
        "id": generate_uuid(),
        "name": "Enhanced Numeric Verifier",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1500, 200]
    }

def create_semantic_validator_node():
    """Create Semantic Validator (Code) node"""

    # Read config to extract SEMANTIC_PATTERNS
    with open('config_registries.js', 'r') as f:
        config_code = f.read()

    start = config_code.find('const SEMANTIC_PATTERNS = {')
    end = config_code.find('// ============================================================================\n// SUBJECT CONFIGURATION')
    patterns_code = config_code[start:end].strip()

    js_code = f"""// Semantic Validator - Configurable Pattern Matching

// Embedded configuration (SEMANTIC_PATTERNS)
{patterns_code}

const input = $input.first().json;
const studentMessage = (input.student_message || '').toLowerCase();
const scaffoldingQuestion = (input.scaffolding_last_question || '').toLowerCase();
const keywords = input.keywords || [];
const problemText = input.current_problem.text || '';

let isCorrect = false;
let reasoning = '';
let needsLLMValidation = false;

// Try to match against configured patterns
patternLoop: for (const [patternType, patternConfig] of Object.entries(SEMANTIC_PATTERNS)) {{
  for (const pattern of patternConfig.patterns) {{
    // Check if scaffolding question matches this pattern
    const questionMatches = pattern.questionPatterns.some(qp =>
      scaffoldingQuestion.includes(qp.toLowerCase())
    );

    if (!questionMatches) continue;

    // Pattern matched - now validate student response

    if (pattern.expectedKeywords) {{
      // Pattern has conditional expected keywords
      let expectedSet = [];
      let wrongSet = [];

      // For operation identification: check what operation is in the problem
      if (patternType === 'math_operation_identification') {{
        if (problemText.includes('+') && !problemText.includes('+ -')) {{
          expectedSet = pattern.expectedKeywords['+'];
          wrongSet = pattern.wrongKeywords['+'];
        }} else if (problemText.includes('-') && !problemText.includes('+ -')) {{
          expectedSet = pattern.expectedKeywords['-'];
          wrongSet = pattern.wrongKeywords['-'];
        }}
      }}
      // For direction identification
      else if (patternType === 'math_direction_identification') {{
        if (problemText.match(/\\+\\s*\\d/) || scaffoldingQuestion.includes('positive')) {{
          expectedSet = pattern.expectedKeywords['positive'];
          wrongSet = pattern.wrongKeywords['positive'];
        }} else if (problemText.match(/\\-\\s*\\d/) || scaffoldingQuestion.includes('negative')) {{
          expectedSet = pattern.expectedKeywords['negative'];
          wrongSet = pattern.wrongKeywords['negative'];
        }}
      }}

      if (expectedSet.length > 0) {{
        const hasCorrect = keywords.some(kw => expectedSet.includes(kw));
        const hasWrong = keywords.some(kw => wrongSet.includes(kw));

        if (hasCorrect && !hasWrong) {{
          isCorrect = true;
          reasoning = 'Student correctly identified concept';
        }} else if (hasWrong) {{
          isCorrect = false;
          reasoning = 'Student gave incorrect answer';
        }} else {{
          // Ambiguous - needs LLM
          needsLLMValidation = true;
        }}

        break patternLoop;
      }}
    }}
  }}
}}

// If no pattern matched or ambiguous, use LLM fallback
if (needsLLMValidation || reasoning === '') {{
  return {{
    json: {{
      ...input,
      _needs_llm_validation: true
    }}
  }};
}}

// Return classification
if (isCorrect) {{
  return {{
    json: {{
      category: 'scaffold_progress',
      is_main_problem_attempt: false,
      confidence: 0.95,
      reasoning: reasoning
    }}
  }};
}} else {{
  return {{
    json: {{
      category: 'stuck',
      is_main_problem_attempt: false,
      confidence: 0.9,
      reasoning: reasoning
    }}
  }};
}}"""

    return {
        "parameters": {
            "jsCode": js_code
        },
        "id": generate_uuid(),
        "name": "Semantic Validator",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1500, 400]
    }

print("Building Option A workflow...")
print("Script created. Ready to run workflow transformation.")
