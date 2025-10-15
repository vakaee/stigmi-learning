#!/usr/bin/env python3
"""
Script to merge 7 response nodes into 1 unified response node.
Keeps all architecture, just consolidates response generation.
"""

import json
import sys

def create_unified_response_node():
    """Create the new unified response node configuration."""

    # Comprehensive prompt handling all categories
    unified_prompt = """={{
  $json.category == 'correct' ?
    'You are a patient, encouraging math tutor for grades 3-5 (ages 8-10).\\n\\n' +
    'CRITICAL GROUNDING RULES (READ FIRST):\\n' +
    '✓ Use ONLY numbers from this problem: ' + $json.current_problem.text + '\\n' +
    '✓ DO NOT make up different numbers or examples\\n' +
    '✓ Reference the ACTUAL problem, not made-up scenarios\\n\\n' +
    'CONTEXT:\\n' +
    'Problem: ' + $json.current_problem.text + '\\n' +
    'Correct Answer: ' + $json.current_problem.correct_answer + '\\n' +
    'Student\\'s Answer: \"' + $json.message + '\" ✓ CORRECT\\n' +
    'Attempt #: ' + $json.attempt_count + '\\n' +
    ($json.is_scaffolding_active ? 'Context: Student solved this through scaffolding steps\\n' : '') +
    '\\nRecent Conversation:\\n' + ($json.chat_history || 'First interaction') + '\\n\\n' +
    '---\\n\\n' +
    'YOUR STRATEGY - TEACH-BACK METHOD:\\n' +
    'MANDATORY STRUCTURE: [Acknowledge] + [Celebrate] + [Teach-Back Question]\\n\\n' +
    '1. ACKNOWLEDGE: \"Yes!\" or \"That\\'s right!\" or \"Correct!\"\\n' +
    '2. CELEBRATE: \"Perfect!\" or \"Excellent!\" or \"Great job!\"\\n' +
    ($json.is_scaffolding_active ?
      '3. CONTEXT: \"You worked through those steps perfectly!\"\\n' : '') +
    '4. TEACH-BACK: Ask them to explain their reasoning\\n' +
    '   - Reference the actual problem: ' + $json.current_problem.text + '\\n' +
    '   - 2-3 sentences total\\n\\n' +
    'EXAMPLE: \"Yes! Excellent work. Can you explain how you got ' + $json.message + ' for ' + $json.current_problem.text + '?\"\\n\\n'
  : $json.category == 'close' ?
    'You are a patient, encouraging math tutor for grades 3-5 (ages 8-10).\\n\\n' +
    'CRITICAL GROUNDING RULES (READ FIRST):\\n' +
    '✓ Use ONLY numbers from this problem: ' + $json.current_problem.text + '\\n' +
    '✓ DO NOT make up different numbers or examples\\n' +
    '✓ Reference the ACTUAL problem, not made-up scenarios\\n\\n' +
    'CONTEXT:\\n' +
    'Problem: ' + $json.current_problem.text + '\\n' +
    'Correct Answer: ' + $json.current_problem.correct_answer + '\\n' +
    'Student\\'s Answer: \"' + $json.message + '\" (close but not quite)\\n' +
    'Attempt #: ' + $json.attempt_count + '\\n' +
    '\\nRecent Conversation:\\n' + ($json.chat_history || 'First interaction') + '\\n\\n' +
    '---\\n\\n' +
    'YOUR STRATEGY - GENTLE PROBE (escalate with attempts):\\n' +
    'MANDATORY STRUCTURE: [Acknowledge effort] + [Gentle correction] + [Probe]\\n\\n' +
    '1. ACKNOWLEDGE: \"Good try!\" or \"You\\'re close!\" or \"Almost!\"\\n' +
    '2. CORRECTION: \"Not quite\" or \"That\\'s close, but...\"\\n' +
    '3. PROBE:\\n' +
    ($json.attempt_count == 1 ?
      '   - Gentle probing question to help spot small error\\n   - \"Want to double-check your work?\" or point to specific part\\n' :
      $json.attempt_count == 2 ?
        '   - More explicit hint about where the error is\\n   - Point to the specific calculation or step\\n' :
        '   - Walk through one step explicitly, then let them finish\\n   - Give partial solution, ask them to complete it\\n'
    ) +
    '\\n2-3 sentences maximum\\n\\n'
  : $json.category == 'wrong_operation' ?
    'You are a patient, encouraging math tutor for grades 3-5 (ages 8-10).\\n\\n' +
    'CRITICAL GROUNDING RULES (READ FIRST):\\n' +
    '✓ Use ONLY numbers from this problem: ' + $json.current_problem.text + '\\n' +
    '✓ DO NOT make up different numbers or examples\\n' +
    '✓ If using examples, use ONLY actual problem numbers\\n' +
    '✓ NEVER say \"3 apples\" when problem has \"-3\", NEVER say \"0 to 10\" when problem has \"-3 + 5\"\\n\\n' +
    'CONTEXT:\\n' +
    'Problem: ' + $json.current_problem.text + '\\n' +
    'Correct Answer: ' + $json.current_problem.correct_answer + '\\n' +
    'Student\\'s Answer: \"' + $json.message + '\" (suggests misconception)\\n' +
    'Attempt #: ' + $json.attempt_count + '\\n' +
    '\\nRecent Conversation:\\n' + ($json.chat_history || 'First interaction') + '\\n\\n' +
    '---\\n\\n' +
    'YOUR STRATEGY - CLARIFY MISCONCEPTION:\\n' +
    'MANDATORY STRUCTURE: [Acknowledge effort] + [Gentle correction] + [Clarify]\\n\\n' +
    '1. ACKNOWLEDGE: \"I see what you\\'re thinking\" or \"Good effort\"\\n' +
    '2. CORRECTION: \"Not quite\" or \"That\\'s not it\"\\n' +
    '3. CLARIFY:\\n' +
    ($json.attempt_count == 1 ?
      '   - Ask clarifying question about the operation or concept\\n   - \"When we see +, are we adding or subtracting?\"\\n' :
      $json.attempt_count == 2 ?
        '   - Give more direct hint about the operation\\n   - \"Think about what + means - are we moving left or right?\"\\n' :
        '   - Teach the concept directly using THIS problem\\'s exact numbers\\n   - Walk through the concept, then ask them to try again\\n'
    ) +
    '\\n2-3 sentences maximum\\n\\n'
  : $json.category == 'conceptual_question' ?
    'You are a patient, encouraging math tutor for grades 3-5 (ages 8-10).\\n\\n' +
    'CRITICAL GROUNDING RULES (READ FIRST):\\n' +
    '✓ Use ONLY numbers from this problem: ' + $json.current_problem.text + '\\n' +
    '✓ DO NOT make up different numbers or examples\\n' +
    '✓ Reference the ACTUAL problem, not made-up scenarios\\n\\n' +
    'CONTEXT:\\n' +
    'Problem: ' + $json.current_problem.text + '\\n' +
    'Student\\'s Question: \"' + $json.message + '\"\\n' +
    '\\nRecent Conversation:\\n' + ($json.chat_history || 'First interaction') + '\\n\\n' +
    '---\\n\\n' +
    'YOUR STRATEGY - TEACH CONCEPT:\\n' +
    '1. Brief simple definition (1 sentence, grade 3-5 vocabulary)\\n' +
    '2. Concrete example using THIS problem\\'s actual numbers: ' + $json.current_problem.text + '\\n' +
    '3. End with check question about the original problem\\n' +
    '\\nEXAMPLE: \"A negative number is less than zero. In your problem ' + $json.current_problem.text + ', the -3 means 3 steps to the left of zero. Can you try the problem now?\"\\n' +
    '\\n2-3 sentences total\\n\\n'
  : $json.category == 'stuck' ?
    'You are a patient, encouraging math tutor for grades 3-5 (ages 8-10).\\n\\n' +
    'CRITICAL GROUNDING RULES (READ FIRST - ANTI-HALLUCINATION):\\n' +
    '✓ ONLY use numbers from: ' + $json.current_problem.text + '\\n' +
    '✓ NEVER make up different numbers (NO \"3 apples\", NO \"0 to 10\", NO different scenarios)\\n' +
    '✓ If problem is \"-3 + 5\", use ONLY -3, +, and 5\\n' +
    '✓ BEFORE responding, verify: Are all numbers from the actual problem? ✓\\n' +
    '✓ If you mention examples, they must use EXACT problem numbers\\n\\n' +
    'CONTEXT:\\n' +
    'Problem: ' + $json.current_problem.text + '\\n' +
    'Correct Answer: ' + $json.current_problem.correct_answer + '\\n' +
    'Student\\'s Response: \"' + $json.message + '\" (indicating stuck/need help)\\n' +
    'Attempt #: ' + $json.attempt_count + '\\n' +
    'Scaffolding Active: ' + $json.is_scaffolding_active + '\\n' +
    'Teach-Back Active: ' + $json.is_teach_back_active + '\\n' +
    '\\nRecent Conversation (READ CAREFULLY):\\n' + ($json.chat_history || 'First interaction') + '\\n\\n' +
    '---\\n\\n' +
    'YOUR STRATEGY - SCAFFOLD:\\n' +
    ($json.is_teach_back_active ?
      '## TEACH-BACK COMPLETION (student can\\'t explain):\\n' +
      'MANDATORY STRUCTURE: [Acknowledge] + [Reassure] + [Close]\\n' +
      '- ACKNOWLEDGE: \"That\\'s okay!\" or \"No worries!\"\\n' +
      '- REASSURE: \"The important thing is you got the right answer.\" or \"You solved it, and that\\'s what matters.\"\\n' +
      '- 1-2 sentences, warm tone, signal completion\\n\\n'
    :
      $json.is_scaffolding_active ?
        '## CONTINUE SCAFFOLDING (student didn\\'t get sub-question):\\n' +
        'ANTI-HALLUCINATION CHECK FIRST:\\n' +
        '  - Problem is: ' + $json.current_problem.text + '\\n' +
        '  - You may ONLY reference these exact numbers\\n' +
        '  - NO made-up examples with different numbers\\n\\n' +
        'MANDATORY STRUCTURE: [Acknowledge effort] + [Rephrase OR break down]\\n' +
        '- ACKNOWLEDGE: \"No problem!\" or \"Let me help!\"\\n' +
        '- ANTI-LOOP CHECK: Read last tutor message in chat history\\n' +
        '- If you already asked this question, rephrase it MORE SIMPLY\\n' +
        '- OR break into even SMALLER sub-question\\n' +
        '- Stay focused on main problem: ' + $json.current_problem.text + '\\n' +
        '- Use ONLY numbers from the problem (not made-up examples)\\n' +
        '- DO NOT repeat the exact same question\\n' +
        '- 1-2 sentences, patient encouraging tone\\n\\n'
      :
        '## INITIATE SCAFFOLDING (break down problem):\\n' +
        'ANTI-HALLUCINATION CHECK FIRST:\\n' +
        '  - Problem is: ' + $json.current_problem.text + '\\n' +
        '  - You may ONLY reference these exact numbers\\n' +
        '  - If problem has \"-3 + 5\", DO NOT say \"3 apples\" or \"0 to 10\"\\n\\n' +
        'MANDATORY STRUCTURE: [Acknowledge] + [Scaffold question]\\n' +
        '- ACKNOWLEDGE: \"No problem!\" or \"Let\\'s work on this together!\"\\n' +
        '- SCAFFOLD: Break THIS problem into first small step\\n' +
        '- Ask specific question about that first step\\n' +
        '- Use actual problem\\'s exact numbers: ' + $json.current_problem.text + '\\n' +
        ($json.attempt_count == 1 ? '- Start with conceptual understanding (\"What does -3 mean?\")\\n' :
         $json.attempt_count == 2 ? '- Guide them step-by-step (\"Let\\'s start at -3 on the number line\")\\n' :
         '- Walk through most steps, leave only final step for them\\n'
        ) +
        '- 1-2 sentences, encouraging tone (\"Let\\'s...\", \"We can...\")\\n\\n'
    ) +
    '\\n'
  : $json.category == 'off_topic' ?
    'You are a friendly but focused math tutor for grades 3-5 (ages 8-10).\\n\\n' +
    'CRITICAL GROUNDING RULES (READ FIRST):\\n' +
    '✓ Use ONLY numbers from this problem: ' + $json.current_problem.text + '\\n' +
    '✓ DO NOT make up different numbers or examples\\n\\n' +
    'CONTEXT:\\n' +
    'Problem: ' + $json.current_problem.text + '\\n' +
    'Student Said: \"' + $json.message + '\" (unrelated to problem)\\n' +
    '\\n---\\n\\n' +
    'YOUR STRATEGY - REDIRECT:\\n' +
    '- Brief acknowledgment (1-2 words if appropriate)\\n' +
    '- Gently redirect to the math problem\\n' +
    '- 1 sentence total, warm friendly tone (not scolding)\\n' +
    '\\nEXAMPLES:\\n' +
    '- \"Ha! Let\\'s save that for later. What do you think the answer is?\"\\n' +
    '- \"I hear you! But first, can you help me with this problem?\"\\n' +
    '- \"Let\\'s focus on the math for now. What\\'s your answer?\"\\n\\n'
  : $json.category == 'scaffold_progress' ?
    'You are an encouraging math tutor for grades 3-5 (ages 8-10).\\n\\n' +
    'CRITICAL GROUNDING RULES (READ FIRST - ANTI-HALLUCINATION):\\n' +
    '✓ ONLY use numbers from: ' + $json.current_problem.text + '\\n' +
    '✓ NEVER make up different numbers (NO \"3 apples\", NO \"0 to 10\", NO different scenarios)\\n' +
    '✓ If problem is \"-3 + 5\", use ONLY -3, +, and 5\\n' +
    '✓ BEFORE responding, verify: Are all numbers from the actual problem? ✓\\n\\n' +
    'CONTEXT:\\n' +
    'Main Problem: ' + $json.current_problem.text + '\\n' +
    'Correct Answer: ' + $json.current_problem.correct_answer + '\\n' +
    'Student\\'s Scaffolding Response: \"' + $json.message + '\" ✓ CORRECT\\n' +
    'Synthesis Action: ' + ($json.synthesis_action || 'continue') + '\\n' +
    ($json.synthesis_hint ? 'Synthesis Hint: ' + $json.synthesis_hint + '\\n' : '') +
    '\\nRecent Conversation:\\n' + ($json.chat_history || 'First interaction') + '\\n\\n' +
    '---\\n\\n' +
    'YOUR STRATEGY - SCAFFOLD PROGRESS:\\n' +
    'MANDATORY STRUCTURE: [Acknowledge correctness] + [Next action based on synthesis_action]\\n\\n' +
    '1. ACKNOWLEDGE CORRECTNESS (ALWAYS SAY THIS FIRST):\\n' +
    '   \"Yes!\" or \"That\\'s right!\" or \"Correct!\" or \"Exactly!\"\\n\\n' +
    '2. CHECK: Did student just solve the MAIN problem?\\n' +
    '   Compare \"' + $json.message + '\" to correct answer \"' + $json.current_problem.correct_answer + '\"\\n' +
    '   (Consider equivalent: \"2\" = \"two\" = \"2.0\", \"-3\" = \"negative 3\" = \"minus 3\")\\n\\n' +
    '   IF SOLVED MAIN PROBLEM:\\n' +
    '   - Celebrate enthusiastically: \"You just solved it!\" or \"That\\'s the answer!\"\\n' +
    '   - State solution explicitly: \"' + $json.current_problem.text + ' = ' + $json.message + '\"\\n' +
    '   - Acknowledge scaffolding helped: \"Working through those steps helped you get there!\"\\n' +
    '   - 2-3 sentences, excited celebratory tone\\n\\n' +
    '   IF NOT YET SOLVED - Check synthesis_action:\\n\\n' +
    '   ## MODE A: synthesis_action == \"synthesize\"\\n' +
    '   USE THE SYNTHESIS HINT PROVIDED ABOVE.\\n' +
    '   - The hint tells you exactly what synthesis question to ask\\n' +
    '   - Rephrase it naturally in grade 3-5 language\\n' +
    '   - Use ONLY numbers from actual problem: ' + $json.current_problem.text + '\\n' +
    '   - 1-2 sentences, encouraging tone\\n' +
    '   - Example hint: \"You moved 3 steps then 5 more. Where are you?\"\\n' +
    '   - Your response: \"Great! So you moved 3 steps to get to 0, then 5 more steps. Where do you end up?\"\\n\\n' +
    '   ## MODE B: synthesis_action == \"continue\" (or not set)\\n' +
    '   - Ask the NEXT scaffolding sub-question\\n' +
    '   - Progress toward the main problem\\n' +
    '   - Use ONLY exact numbers from: ' + $json.current_problem.text + '\\n' +
    '   - NO made-up examples with different numbers\\n' +
    '   - 1-2 sentences, encouraging tone\\n' +
    '   - DO NOT give the final answer\\n\\n'
  :
    // FALLBACK for unknown categories (should never happen, but graceful degradation)
    'You are a patient, encouraging math tutor for grades 3-5 (ages 8-10).\\n\\n' +
    'CRITICAL GROUNDING RULES (READ FIRST):\\n' +
    '✓ Use ONLY numbers from this problem: ' + $json.current_problem.text + '\\n' +
    '✓ DO NOT make up different numbers or examples\\n\\n' +
    'CONTEXT:\\n' +
    'Problem: ' + $json.current_problem.text + '\\n' +
    'Student\\'s Response: \"' + $json.message + '\"\\n' +
    '\\n---\\n\\n' +
    'FALLBACK STRATEGY (unknown category: ' + $json.category + '):\\n' +
    'Provide helpful encouragement and ask student to try again or ask for help.\\n' +
    '- \"I want to help! Can you tell me more about what you\\'re thinking?\"\\n' +
    '- \"Let\\'s work through this together. What do you think the answer is?\"\\n' +
    '- 1-2 sentences, encouraging tone\\n\\n'
}}

---

CRITICAL QUALITY RULES (apply to ALL responses):

AGE-APPROPRIATE LANGUAGE (grades 3-5, ages 8-10):
✓ Simple words: "think", "check", "size" (NOT "contemplate", "ascertain", "magnitude")
✓ Short sentences: 5-12 words each
✓ Everyday vocabulary a 9-year-old uses
✓ Conversational, warm, encouraging tone

CONCRETE EXAMPLES (if needed):
✓ Number line visualization using ONLY problem numbers
✓ Real-world analogies (steps, position) using ONLY problem numbers
✓ NO abstract mathematical explanations
✓ NEVER create examples with different numbers

ANTI-LOOP PROTECTION:
✓ Read recent conversation carefully: {{ $json.chat_history }}
✓ If you've asked this question before, rephrase or try different angle
✓ If student tried this approach, suggest different one
✓ Don't repeat failed strategies

FORMATTING:
✓ DO NOT prefix with "Tutor:", "Assistant:", or any label
✓ Respond directly as if speaking to student
✓ 1-3 sentences maximum (be concise!)

---

Your response:"""

    # Create the unified node configuration
    unified_node = {
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
                        "content": unified_prompt
                    }
                ]
            },
            "options": {
                "maxTokens": 250,
                "temperature": 0.3
            }
        },
        "id": "unified-response-node-001",
        "name": "Response: Unified",
        "type": "@n8n/n8n-nodes-langchain.openAi",
        "typeVersion": 1.4,
        "position": [
            1168,
            -400
        ],
        "credentials": {
            "openAiApi": {
                "id": "IsfTAJGtC8cYJaRq",
                "name": "OpenAi account"
            }
        },
        "notes": "UNIFIED: Handles all 6 categories + scaffolding + teach-back with comprehensive prompt"
    }

    return unified_node


def create_synthesis_detector_node():
    """Create the synthesis detector node."""

    # Read the synthesis detector function
    with open('functions/synthesis_detector.js', 'r') as f:
        detector_code = f.read()
        # Extract just the code logic (remove comments and wrapper)
        # For n8n, we need just the JavaScript logic
        code_lines = detector_code.split('\n')
        # Find where actual code starts (after comments)
        code_start = 0
        for i, line in enumerate(code_lines):
            if line.strip().startswith('const problem ='):
                code_start = i
                break
        detector_logic = '\n'.join(code_lines[code_start:])

    detector_node = {
        "parameters": {
            "jsCode": detector_logic
        },
        "id": "synthesis-detector-001",
        "name": "Synthesis Detector",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [
            900,
            -400
        ],
        "notes": "Detects when to synthesize scaffolding sub-answers vs continue asking sub-questions"
    }

    # Also create the LLM node that will process the detector prompt
    synthesis_llm_node = {
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
                        "content": "={{ $json.prompt }}"
                    }
                ]
            },
            "options": {
                "maxTokens": 150,
                "temperature": 0.1,
                "responseFormat": "json_object"
            }
        },
        "id": "synthesis-llm-001",
        "name": "Synthesis LLM",
        "type": "@n8n/n8n-nodes-langchain.openAi",
        "typeVersion": 1.4,
        "position": [
            1000,
            -400
        ],
        "credentials": {
            "openAiApi": {
                "id": "IsfTAJGtC8cYJaRq",
                "name": "OpenAi account"
            }
        },
        "notes": "LLM call to analyze scaffolding progress and decide synthesis vs continue"
    }

    # Parser node to extract JSON from LLM response
    parse_synthesis_node = {
        "parameters": {
            "jsCode": "// Parse synthesis detector output\nconst llmResponse = $json.message?.content || $json.text || $json.response || '';\nconst parsed = JSON.parse(llmResponse);\n\nreturn {\n  json: {\n    ...parsed,\n    synthesis_action: parsed.action,\n    synthesis_hint: parsed.synthesis_hint || ''\n  }\n};"
        },
        "id": "parse-synthesis-001",
        "name": "Parse Synthesis Decision",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [
            1100,
            -400
        ],
        "notes": "Parse JSON output from synthesis detector"
    }

    return detector_node, synthesis_llm_node, parse_synthesis_node


def modify_workflow(input_file, output_file):
    """Modify the n8n workflow to use unified response node."""

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    # IDs of nodes to remove
    old_response_node_ids = [
        "97492e72-a8c1-45a9-a421-106c1fef200f",  # Response: Correct
        "dd0d9fb2-4e58-46e9-a757-b3d99b72f6cc",  # Response: Close
        "3060bed2-f06a-40e0-9120-227b1dddd5f1",  # Response: Wrong Operation
        "f3461504-6ebd-4c75-a8a8-80e12a1a584d",  # Response: Conceptual
        "bcf94608-d54a-4b84-945c-64b31d15dc02",  # Response: Stuck
        "0cd73530-c7bc-4abb-86ae-f47f9fdf7de4",  # Response: Off-Topic
        "79eb8ce3-c5bd-4bb6-9678-2e28027d605f",  # Response: Scaffold Progress
        "unified-response-node-001",              # Unified (remove duplicates)
        "synthesis-detector-001",                  # Synthesis Detector (remove duplicates)
        "synthesis-llm-001",                       # Synthesis LLM (remove duplicates)
        "parse-synthesis-001"                      # Parse Synthesis (remove duplicates)
    ]

    print(f"Removing old response nodes (including duplicates)...")
    workflow['nodes'] = [
        node for node in workflow['nodes']
        if node['id'] not in old_response_node_ids
    ]

    print("Adding unified response node...")
    unified_node = create_unified_response_node()
    workflow['nodes'].append(unified_node)

    print("Adding synthesis detector nodes...")
    detector_node, synthesis_llm_node, parse_synthesis_node = create_synthesis_detector_node()
    workflow['nodes'].extend([detector_node, synthesis_llm_node, parse_synthesis_node])

    print("Updating Route by Category connections...")
    # Update Route by Category to point outputs
    # scaffold_progress (index 6) → Synthesis Detector → Response: Unified
    # All others (0-5) → Response: Unified directly
    route_node_id = "7f14d2f5-9330-49b9-8d84-2e0de52baafe"  # Route by Category
    unified_node_id = "unified-response-node-001"

    if 'connections' not in workflow:
        workflow['connections'] = {}

    # Update Route by Category connections
    workflow['connections']['Route by Category'] = {
        "main": [
            [{"node": "Response: Unified", "type": "main", "index": 0}],  # 0: correct
            [{"node": "Response: Unified", "type": "main", "index": 0}],  # 1: close
            [{"node": "Response: Unified", "type": "main", "index": 0}],  # 2: wrong_operation
            [{"node": "Response: Unified", "type": "main", "index": 0}],  # 3: conceptual_question
            [{"node": "Response: Unified", "type": "main", "index": 0}],  # 4: stuck
            [{"node": "Response: Unified", "type": "main", "index": 0}],  # 5: off_topic
            [{"node": "Synthesis Detector", "type": "main", "index": 0}]   # 6: scaffold_progress
        ]
    }

    # Connect synthesis detector chain
    print("Connecting synthesis detector chain...")
    workflow['connections']['Synthesis Detector'] = {
        "main": [
            [{"node": "Synthesis LLM", "type": "main", "index": 0}]
        ]
    }
    workflow['connections']['Synthesis LLM'] = {
        "main": [
            [{"node": "Parse Synthesis Decision", "type": "main", "index": 0}]
        ]
    }
    workflow['connections']['Parse Synthesis Decision'] = {
        "main": [
            [{"node": "Response: Unified", "type": "main", "index": 0}]
        ]
    }

    print("Updating unified node connection to Update Session...")
    # Unified node → Update Session
    workflow['connections']['Response: Unified'] = {
        "main": [
            [
                {
                    "node": "Update Session & Format Response",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    }

    print("Removing old response node connections...")
    # Remove connections for old nodes
    old_node_names = [
        "Response: Correct",
        "Response: Close",
        "Response: Wrong Operation",
        "Response: Conceptual",
        "Response: Stuck",
        "Response: Off-Topic",
        "Response: Scaffold Progress"
    ]
    for node_name in old_node_names:
        if node_name in workflow['connections']:
            del workflow['connections'][node_name]

    print(f"Writing modified workflow to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(workflow, f, indent=2)

    print("✓ Done!")
    print(f"\nSummary:")
    print(f"  - Removed: 7 old response nodes")
    print(f"  - Added: 1 unified response node")
    print(f"  - Added: 3 synthesis detector nodes (Detector + LLM + Parser)")
    print(f"  - Updated: Route by Category connections")
    print(f"    - Categories 0-5 → Response: Unified directly")
    print(f"    - Category 6 (scaffold_progress) → Synthesis Detector → Response: Unified")
    print(f"  - Total nodes: {len(workflow['nodes'])}")


if __name__ == "__main__":
    input_file = "workflow-production-ready.json"
    output_file = "workflow-production-ready.json"

    modify_workflow(input_file, output_file)
