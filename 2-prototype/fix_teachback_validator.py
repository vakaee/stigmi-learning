#!/usr/bin/env python3
"""
Fix teach-back validator to distinguish explanation attempts from help requests
"""

import json
import uuid

def create_teachback_validator(base_x, base_y):
    """Create a validator node specifically for teach-back responses"""
    return {
        "parameters": {
            "jsCode": """// Teach-Back Validator - Distinguish explanation attempts from help requests

const input = $input.first().json;
const studentMessage = (input.student_message || input.message || '').toLowerCase();
const numericValue = input.numeric_value;
const correctAnswer = input.current_problem.correct_answer;

// Parse correct answer
let correctValue;
try {
  correctValue = parseFloat(String(correctAnswer).replace(/[^0-9.\\-]/g, ''));
} catch (error) {
  correctValue = null;
}

// Detect help request patterns
const helpPatterns = [
  "i don't know",
  "i dont know",
  "don't know",
  "dont know",
  "not sure",
  "i'm not sure",
  "im not sure",
  "help me",
  "help",
  "i'm stuck",
  "im stuck",
  "stuck",
  "no idea",
  "i have no idea"
];

const isHelpRequest = helpPatterns.some(pattern => studentMessage.includes(pattern));

if (isHelpRequest) {
  return {
    json: {
      ...input,
      category: 'stuck',
      is_main_problem_attempt: false,
      confidence: 1.0,
      reasoning: 'Student requested help during teach-back'
    }
  };
}

// Detect explanation attempt patterns
const explanationPatterns = [
  'i followed',
  'i did',
  'i got',
  'because',
  'i think',
  'i used',
  'i started',
  'i moved',
  'i added',
  'i subtracted',
  'first',
  'then',
  'so',
  'steps',
  'from',
  'to'
];

const hasExplanationWords = explanationPatterns.some(pattern => studentMessage.includes(pattern));
const mentionsAnswer = numericValue !== null && correctValue !== null && Math.abs(numericValue - correctValue) < 0.001;

if (hasExplanationWords || mentionsAnswer) {
  return {
    json: {
      ...input,
      category: 'teach_back_explanation',
      is_main_problem_attempt: false,
      confidence: 0.9,
      reasoning: 'Student attempting to explain reasoning'
    }
  };
}

// Default: ambiguous, treat as stuck
return {
  json: {
    ...input,
    category: 'stuck',
    is_main_problem_attempt: false,
    confidence: 0.7,
    reasoning: 'Ambiguous teach-back response'
  }
};"""
        },
        "id": str(uuid.uuid4()),
        "name": "Teach-Back Validator",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [base_x + 600, base_y + 500],
        "notes": "Validates teach-back responses - distinguishes explanations from help requests"
    }

def update_router_code():
    """Update Content-Based Router to route teach-back appropriately"""
    return """// Content-Based Router - handle append mode from Merge
const inputs = $input.all();

// Identify which input is which
let loadSessionData, featureExtractorData;

for (const input of inputs) {
  const data = input.json;
  if (data.message && data.message.content) {
    // Content Feature Extractor (has OpenAI structure)
    featureExtractorData = data;
  } else if (data.session || data.current_problem) {
    // Load Session data
    loadSessionData = data;
  }
}

// Parse JSON from OpenAI
const jsonString = featureExtractorData.message.content;
const features = JSON.parse(jsonString);

const messageType = features.message_type;
const isScaffolding = loadSessionData.session?.current_problem?.scaffolding?.active || false;
const teachBackActive = loadSessionData.session?.current_problem?.teach_back?.active || false;

// Route based on message type and context
let route;

if (teachBackActive) {
  // During teach-back, distinguish help requests from explanation attempts
  if (messageType === 'help_request') {
    route = 'classify_stuck';
  } else {
    route = 'teach_back_validator';
  }
} else if (messageType === 'answer_attempt') {
  if (isScaffolding) {
    const numericValue = features.numeric_value;
    const correctAnswer = loadSessionData.current_problem.correct_answer;
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
} else {
  route = 'classify_stuck';
}

return {
  json: {
    ...loadSessionData,
    ...features,
    _route: route
  }
};"""

def main():
    print("=" * 70)
    print("FIX TEACH-BACK VALIDATOR")
    print("=" * 70)

    # Read workflow
    with open('workflow-production-ready.json', 'r') as f:
        workflow = json.load(f)

    # Build node mapping
    node_map = {node['name']: node for node in workflow['nodes']}

    # 1. Create Teach-Back Validator node
    print("\n1. Creating Teach-Back Validator node...")
    load_session = node_map.get('Load Session')
    if not load_session:
        print("ERROR: Load Session not found")
        return 1

    base_x, base_y = load_session['position']
    teachback_validator = create_teachback_validator(base_x, base_y)
    workflow['nodes'].append(teachback_validator)
    node_map[teachback_validator['name']] = teachback_validator
    print(f"  Created: {teachback_validator['name']} ({teachback_validator['id']})")

    # 2. Update Content-Based Router
    print("\n2. Updating Content-Based Router...")
    router = node_map.get('Content-Based Router')
    if router:
        router['parameters']['jsCode'] = update_router_code()
        print("  Updated routing logic to distinguish teach-back help requests from explanations")
    else:
        print("  WARNING: Content-Based Router not found")

    # 3. Update Route by Content Type switch to add teach_back_validator output
    print("\n3. Updating Route by Content Type switch...")
    route_switch = node_map.get('Route by Content Type')
    if route_switch:
        # Add new route condition
        new_route = {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "strict",
                    "version": 1
                },
                "conditions": [{
                    "leftValue": "={{$json._route}}",
                    "rightValue": "teach_back_validator",
                    "operator": {"type": "string", "operation": "equals"},
                    "id": str(uuid.uuid4())
                }],
                "combinator": "and"
            },
            "renameOutput": True,
            "outputKey": "teach_back_validator"
        }

        # Insert before the last route (teach_back_response becomes teach_back_validator)
        if 'rules' in route_switch['parameters'] and 'values' in route_switch['parameters']['rules']:
            routes = route_switch['parameters']['rules']['values']
            # Replace teach_back_response with teach_back_validator
            for route in routes:
                if route.get('outputKey') == 'teach_back_response':
                    route['outputKey'] = 'teach_back_validator'
                    route['conditions']['conditions'][0]['rightValue'] = 'teach_back_validator'
                    print("  Updated teach_back_response route to teach_back_validator")
                    break
        print("  Updated Route by Content Type switch")
    else:
        print("  WARNING: Route by Content Type not found")

    # 4. Update connections
    print("\n4. Updating connections...")
    connections = workflow.get('connections', {})

    # Route by Content Type → Teach-Back Validator
    if 'Route by Content Type' in connections:
        route_conns = connections['Route by Content Type']['main']
        # Find the teach_back_response output (now teach_back_validator) and update it
        if len(route_conns) >= 4:
            route_conns[3] = [{"node": "Teach-Back Validator", "type": "main", "index": 0}]
            print("  Updated Route by Content Type → Teach-Back Validator")

    # Teach-Back Validator → Build Response Context
    connections['Teach-Back Validator'] = {
        "main": [[{"node": "Build Response Context", "type": "main", "index": 0}]]
    }
    print("  Added Teach-Back Validator → Build Response Context")

    workflow['connections'] = connections

    # Save
    print("\n5. Saving workflow...")
    with open('workflow-production-ready.json', 'w') as f:
        json.dump(workflow, f, indent=2)

    print("\nWorkflow updated successfully!")
    print("\nChanges:")
    print("  ✓ Created Teach-Back Validator node")
    print("  ✓ Updated Content-Based Router to route teach-back appropriately")
    print("  ✓ Updated Route by Content Type switch")
    print("  ✓ Connected Teach-Back Validator to Build Response Context")
    print("\nNext: Update Response: Unified prompt to handle teach_back_explanation category")

    return 0

if __name__ == '__main__':
    exit(main())
