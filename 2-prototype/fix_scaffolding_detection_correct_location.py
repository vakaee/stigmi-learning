#!/usr/bin/env python3
"""
CORRECT FIX for Bug #12: Scaffolding conceptual answers not recognized.

Previous fix was in Build Response Context (too late - after AI Agent).
This fix adds detection to Prepare Agent Context (before AI Agent).

When scaffolding is active and student says operation keywords like "adding",
we set a flag that AI Agent uses to force classification as scaffold_progress.
"""

import json

def add_detection_to_prepare_agent_context(workflow):
    """Add scaffolding answer detection BEFORE AI Agent call."""

    for node in workflow['nodes']:
        if node['name'] == 'Prepare Agent Context':
            code = node['parameters']['jsCode']

            # Find the return statement at the end
            # Add detection logic before the final return

            # Look for the return statement
            if 'return [{' not in code:
                print("✗ ERROR: Could not find return statement")
                return False

            # Add detection logic before return
            detection_logic = '''
// ===== SCAFFOLDING CONCEPTUAL ANSWER DETECTION =====
// Detect operation/concept keywords BEFORE AI Agent call
// If detected, set flag to force scaffold_progress classification

let detectedScaffoldingAnswer = false;

if (scaffoldingState.active) {
  const msg = inputData.chatInput.toLowerCase().trim();

  // Operation keywords (answering "are we adding or subtracting?")
  const hasOperation = msg.includes('add') || msg.includes('subtract') ||
    msg.includes('multiply') || msg.includes('divide') ||
    msg.includes('plus') || msg.includes('minus') || msg.includes('times');

  // Direction keywords (answering "left or right?")
  const hasDirection = msg.includes('left') || msg.includes('right') ||
    msg.includes('up') || msg.includes('down');

  // Position keywords (answering "where are we?")
  const hasPosition = msg.includes('positive') || msg.includes('negative') ||
    msg.includes('zero');

  // Concept keywords (answering "what does it mean?")
  const hasConcept = msg.includes('bigger') || msg.includes('smaller') ||
    msg.includes('more') || msg.includes('less') ||
    msg.includes('greater') || msg.includes('fewer');

  if (hasOperation || hasDirection || hasPosition || hasConcept) {
    detectedScaffoldingAnswer = true;
  }
}

'''

            # Insert before the return statement
            code = code.replace(
                'return [{',
                detection_logic + 'return [{'
            )

            # Add the flag to the return object
            # Find where we return the json object and add the flag
            code = code.replace(
                '    _start_time: sessionData._start_time',
                '''    _start_time: sessionData._start_time,
    detected_scaffolding_answer: detectedScaffoldingAnswer'''
            )

            node['parameters']['jsCode'] = code

            print("✓ Updated Prepare Agent Context")
            print("  - Added scaffolding answer detection BEFORE AI Agent")
            print("  - Sets detected_scaffolding_answer flag when keywords found")
            print("  - Keywords: adding, subtracting, left, right, positive, negative, etc.")
            return True

    print("✗ ERROR: Could not find Prepare Agent Context node")
    return False


def update_ai_agent_to_check_flag(workflow):
    """Update AI Agent to check the detected_scaffolding_answer flag."""

    for node in workflow['nodes']:
        if node['name'] == 'AI Agent':
            system_msg = node['parameters']['options']['systemMessage']

            # Add instruction at the beginning to check the flag
            flag_check = '''
IMPORTANT: Check the context for a 'detected_scaffolding_answer' flag.
If detected_scaffolding_answer is true:
  - The student's response contains operation/concept keywords
  - You MUST classify as "scaffold_progress" (correct scaffolding answer)
  - Set is_main_problem_attempt: false
  - Return immediately without deep analysis

'''

            # Insert after the first line (which starts with =You or You)
            first_newline = system_msg.find('\n')
            if first_newline > 0:
                system_msg = system_msg[:first_newline+1] + '\n' + flag_check + system_msg[first_newline+1:]
                node['parameters']['options']['systemMessage'] = system_msg

                print("✓ Updated AI Agent")
                print("  - Added check for detected_scaffolding_answer flag")
                print("  - Will force scaffold_progress when flag is true")
                return True
            else:
                print("✗ ERROR: Could not find newline in prompt")
                return False

    print("✗ ERROR: Could not find AI Agent node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print("\n=== Applying CORRECT fix ===\n")

    print("Step 1: Add detection to Prepare Agent Context...")
    success1 = add_detection_to_prepare_agent_context(workflow)

    print("\nStep 2: Update AI Agent to check flag...")
    success2 = update_ai_agent_to_check_flag(workflow)

    if success1 and success2:
        print(f"\nWriting updated workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("✓ Done!")
        print("\n=== Fix Summary ===")
        print("Detection now happens BEFORE AI Agent (correct location)")
        print("Flow: Prepare Agent Context → sets flag → AI Agent → checks flag → scaffold_progress")
        print("\nTest case: 'we are adding' should now be recognized correctly")
    else:
        print("\n✗ Fix failed - workflow not modified")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
