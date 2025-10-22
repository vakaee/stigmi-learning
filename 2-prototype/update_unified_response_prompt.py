#!/usr/bin/env python3
"""
Update Response: Unified prompt to handle teach_back_explanation category
"""

import json

def main():
    print("=" * 70)
    print("UPDATE RESPONSE: UNIFIED PROMPT")
    print("=" * 70)

    # Read workflow
    with open('workflow-production-ready.json', 'r') as f:
        workflow = json.load(f)

    # Find Response: Unified node
    response_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Response: Unified':
            response_node = node
            break

    if not response_node:
        print("ERROR: Response: Unified node not found")
        return 1

    print("\nUpdating Response: Unified prompt...")

    # The prompt is in parameters.messages.values[0].content
    # We need to add a new category handler for teach_back_explanation

    # Add teach_back_explanation handler before the stuck category
    teach_back_explanation_prompt = """  : $json.category == 'teach_back_explanation' ?
    'You are a patient, encouraging math tutor for grades 3-5 (ages 8-10).\\n\\nCRITICAL GROUNDING RULES (apply to ALL responses):\\n✓ Use ONLY numbers from this problem: ' + $json.current_problem.text + '\\n✓ NEVER make up different numbers, examples, or scenarios\\n✓ If problem is \"-3 + 5\", use ONLY -3, +, and 5\\n✓ Verify before responding: Are all numbers from the actual problem? ✓\\n\\nCONTEXT:\\nProblem: ' + $json.current_problem.text + '\\nCorrect Answer: ' + $json.current_problem.correct_answer + '\\nStudent\\'s Explanation: \"' + $json.message + '\"\\n' +
    '\\nRecent Conversation:\\n' + ($json.chat_history || 'First interaction') + '\\n\\n---\\n\\nSTRATEGY - ACKNOWLEDGE TEACH-BACK EXPLANATION:\\n' +
    '\\nThe student is attempting to explain their reasoning.\\n' +
    '\\nSTEP 1 - Check if explanation mentions correct answer:\\n' +
    'Student message: \"' + $json.message + '\"\\n' +
    'Correct answer: ' + $json.current_problem.correct_answer + '\\n' +
    'Look for: \"got ' + $json.current_problem.correct_answer + '\", \"got to ' + $json.current_problem.correct_answer + '\", \"answer is ' + $json.current_problem.correct_answer + '\", etc.\\n' +
    '\\n' +
    'IF CORRECT ANSWER MENTIONED:\\n' +
    '- Celebrate: \"Great job explaining! You got it right!\"\\n' +
    '- Brief acknowledgment of their process\\n' +
    '- 1-2 sentences, excited tone\\n' +
    '- Example: \"Excellent! You followed the steps and got ' + $json.current_problem.correct_answer + '. Well done!\"\\n' +
    '\\n' +
    'IF NO CLEAR ANSWER OR INCOMPLETE:\\n' +
    '- Acknowledge effort: \"Good start!\"\\n' +
    '- Gentle probe: \"Can you tell me what answer you got?\"\\n' +
    '- 1-2 sentences, encouraging tone\\n' +
    '\\n1-2 sentences total\\n\\n'"""

    # Get current prompt content
    current_prompt = response_node['parameters']['messages']['values'][0]['content']

    # Find where to insert (before the stuck category)
    stuck_marker = "  : $json.category == 'stuck' ?"
    if stuck_marker in current_prompt:
        # Insert teach_back_explanation handler before stuck
        updated_prompt = current_prompt.replace(stuck_marker, teach_back_explanation_prompt + "\n" + stuck_marker)
        response_node['parameters']['messages']['values'][0]['content'] = updated_prompt
        print("  Added teach_back_explanation category handler")
    else:
        print("  WARNING: Could not find insertion point for teach_back_explanation handler")
        return 1

    # Save workflow
    with open('workflow-production-ready.json', 'w') as f:
        json.dump(workflow, f, indent=2)

    print("\nPrompt updated successfully!")
    print("\nChanges:")
    print("  ✓ Added teach_back_explanation category handler")
    print("  ✓ Checks if student mentioned correct answer in explanation")
    print("  ✓ Celebrates if correct, probes if incomplete")
    print("\nWorkflow is now ready for testing!")

    return 0

if __name__ == '__main__':
    exit(main())
