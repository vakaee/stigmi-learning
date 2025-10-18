#!/usr/bin/env python3
"""
Complete workflow builder for Option A
Builds the entire new workflow JSON with all nodes and connections
"""

import json
import uuid

def main():
    print("=" * 70)
    print("BUILDING COMPLETE OPTION A WORKFLOW")
    print("=" * 70)

    # Read current workflow
    with open('workflow-production-ready.json', 'r') as f:
        workflow = json.load(f)

    print(f"\nCurrent workflow: {len(workflow['nodes'])} nodes")

    # Find existing OpenAI credential
    openai_cred_id = None
    for node in workflow['nodes']:
        if 'credentials' in node and 'openAiApi' in node['credentials']:
            openai_cred_id = node['credentials']['openAiApi']['id']
            break

    if not openai_cred_id:
        print("WARNING: No OpenAI credential found, using placeholder")
        openai_cred_id = "1"

    print(f"OpenAI credential ID: {openai_cred_id}")

    # Find key nodes for positioning
    load_session = next((n for n in workflow['nodes'] if n['name'] == 'Load Session'), None)
    if not load_session:
        print("ERROR: Load Session node not found")
        return 1

    base_x, base_y = load_session['position']
    print(f"Base position from Load Session: [{base_x}, {base_y}]")

    # Read config file
    with open('config_registries.js', 'r') as f:
        config_content = f.read()

    # Extract ERROR_DETECTORS (for Enhanced Numeric Verifier)
    start_idx = config_content.find('const ERROR_DETECTORS = {')
    end_idx = config_content.find('\n// ============================================================================\n// SEMANTIC PATTERN REGISTRY')
    error_detectors_code = config_content[start_idx:end_idx].strip()

    # Extract SEMANTIC_PATTERNS (for Semantic Validator)
    start_idx = config_content.find('const SEMANTIC_PATTERNS = {')
    end_idx = config_content.find('\n  // FUTURE: Add patterns for other subjects\n  // \'history_time_period\'')
    semantic_patterns_code = config_content[start_idx:end_idx].strip()

    print(f"\nExtracted config:")
    print(f"  ERROR_DETECTORS: {len(error_detectors_code)} chars")
    print(f"  SEMANTIC_PATTERNS: {len(semantic_patterns_code)} chars")

    #
    # CREATE NEW NODES
    #

    print("\n" + "=" * 70)
    print("CREATING NEW NODES")
    print("=" * 70)

    new_nodes = []

    # 1. Content Feature Extractor (OpenAI)
    print("\n1. Content Feature Extractor (OpenAI)")
    content_feature_extractor = {
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
        "id": str(uuid.uuid4()),
        "name": "Content Feature Extractor",
        "type": "@n8n/n8n-nodes-langchain.openAi",
        "typeVersion": 1.3,
        "position": [base_x + 200, base_y],
        "credentials": {
            "openAiApi": {
                "id": openai_cred_id,
                "name": "OpenAI account"
            }
        }
    }
    new_nodes.append(content_feature_extractor)
    print(f"  Created: {content_feature_extractor['name']} ({content_feature_extractor['id']})")

    # 2. Content-Based Router (Code)
    print("\n2. Content-Based Router (Code)")
    content_router = {
        "parameters": {
            "jsCode": """// Content-Based Router
const features = $input.first().json;
const context = $('Load Session').first().json;

const messageType = features.message_type;
const isScaffolding = context.is_scaffolding_active;
const isTeachBack = context.is_teach_back_active;

// Route based on message type and context
let route;

if (isTeachBack) {
  route = 'teach_back_response';
} else if (messageType === 'answer_attempt') {
  if (isScaffolding) {
    const numericValue = features.numeric_value;
    const correctAnswer = context.current_problem.correct_answer;
    const correctValue = parseFloat(String(correctAnswer).replace(/[^0-9.\\-]/g, ''));
    const diff = Math.abs(numericValue - correctValue);
    const threshold = Math.abs(correctValue * 0.5);
    const isLikelyMainProblem = diff < Math.max(threshold, 1);
    route = isLikelyMainProblem ? 'verify_numeric' : 'validate_conceptual';
  } else {
    route = 'verify_numeric';
  }
} else if (messageType === 'conceptual_response') {
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
};"""
        },
        "id": str(uuid.uuid4()),
        "name": "Content-Based Router",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [base_x + 400, base_y]
    }
    new_nodes.append(content_router)
    print(f"  Created: {content_router['name']} ({content_router['id']})")

    # 3. Enhanced Numeric Verifier (Code)
    print("\n3. Enhanced Numeric Verifier (Code)")

    numeric_verifier_code = f"""// Enhanced Numeric Verifier with Configurable Error Detection

// Embedded configuration
{error_detectors_code}

const input = $input.first().json;
const studentValue = input.numeric_value;
const correctAnswer = input.current_problem.correct_answer;
const problemText = input.current_problem.text;

// Parse correct answer
let correctValue;
try {{
  correctValue = parseFloat(String(correctAnswer).replace(/[^0-9.\\-]/g, ''));
  if (isNaN(correctValue)) throw new Error('Cannot parse correct answer');
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

// Check if close
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

// Check if plausible operation error
const match = problemText.match(/([\\-\\d.]+)\\s*([+\\-*/])\\s*([\\-\\d.]+)/);
if (match) {{
  const num1 = parseFloat(match[1]);
  const operation = match[2];
  const num2 = parseFloat(match[3]);

  const operationMap = {{
    '+': 'math_arithmetic_addition',
    '-': 'math_arithmetic_subtraction',
    '*': 'math_arithmetic_multiplication',
    '/': 'math_arithmetic_division'
  }};

  const detectorKey = operationMap[operation];
  const errorDetector = ERROR_DETECTORS[detectorKey];

  if (errorDetector) {{
    const possibleErrors = errorDetector(num1, num2, operation);
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

    enhanced_numeric_verifier = {
        "parameters": {
            "jsCode": numeric_verifier_code
        },
        "id": str(uuid.uuid4()),
        "name": "Enhanced Numeric Verifier",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [base_x + 600, base_y - 100]
    }
    new_nodes.append(enhanced_numeric_verifier)
    print(f"  Created: {enhanced_numeric_verifier['name']} ({enhanced_numeric_verifier['id']})")

    # 4. Semantic Validator (Code)
    print("\n4. Semantic Validator (Code)")

    semantic_validator_code = f"""// Semantic Validator - Configurable Pattern Matching

// Embedded configuration
{semantic_patterns_code}

const input = $input.first().json;
const studentMessage = (input.student_message || '').toLowerCase();
const scaffoldingQuestion = (input.scaffolding_last_question || '').toLowerCase();
const keywords = input.keywords || [];
const problemText = input.current_problem.text || '';

let isCorrect = false;
let reasoning = '';
let needsLLMValidation = false;

patternLoop: for (const [patternType, patternConfig] of Object.entries(SEMANTIC_PATTERNS)) {{
  for (const pattern of patternConfig.patterns) {{
    const questionMatches = pattern.questionPatterns.some(qp =>
      scaffoldingQuestion.includes(qp.toLowerCase())
    );

    if (!questionMatches) continue;

    if (pattern.expectedKeywords) {{
      let expectedSet = [];
      let wrongSet = [];

      if (patternType === 'math_operation_identification') {{
        if (problemText.includes('+') && !problemText.includes('+ -')) {{
          expectedSet = pattern.expectedKeywords['+'];
          wrongSet = pattern.wrongKeywords['+'];
        }} else if (problemText.includes('-') && !problemText.includes('+ -')) {{
          expectedSet = pattern.expectedKeywords['-'];
          wrongSet = pattern.wrongKeywords['-'];
        }}
      }} else if (patternType === 'math_direction_identification') {{
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
          needsLLMValidation = true;
        }}

        break patternLoop;
      }}
    }}
  }}
}}

if (needsLLMValidation || reasoning === '') {{
  return {{
    json: {{
      ...input,
      _needs_llm_validation: true
    }}
  }};
}}

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

    semantic_validator = {
        "parameters": {
            "jsCode": semantic_validator_code
        },
        "id": str(uuid.uuid4()),
        "name": "Semantic Validator",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [base_x + 600, base_y + 100]
    }
    new_nodes.append(semantic_validator)
    print(f"  Created: {semantic_validator['name']} ({semantic_validator['id']})")

    # 5. Classify Stuck (Code) - simple node for help requests
    print("\n5. Classify Stuck (Code)")
    classify_stuck = {
        "parameters": {
            "jsCode": """// Classify as stuck
const input = $input.first().json;

return {
  json: {
    category: 'stuck',
    is_main_problem_attempt: false,
    confidence: 1.0,
    reasoning: 'Student requested help'
  }
};"""
        },
        "id": str(uuid.uuid4()),
        "name": "Classify Stuck",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [base_x + 600, base_y + 300]
    }
    new_nodes.append(classify_stuck)
    print(f"  Created: {classify_stuck['name']} ({classify_stuck['id']})")

    # Add new nodes to workflow
    workflow['nodes'].extend(new_nodes)

    print(f"\n" + "=" * 70)
    print(f"New workflow: {len(workflow['nodes'])} nodes")
    print(f"Added {len(new_nodes)} new nodes")

    # Save updated workflow
    with open('workflow-production-ready.json', 'w') as f:
        json.dump(workflow, f, indent=2)

    print("\nWorkflow saved successfully!")
    print("\nNext: Update connections to wire the new flow")

    return 0

if __name__ == '__main__':
    exit(main())
