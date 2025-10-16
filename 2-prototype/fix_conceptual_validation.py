#!/usr/bin/env python3
"""
Fix conceptual answer validation bug.

PROBLEM:
Question: "When we see +, are we adding or subtracting?"
Student: "subtracting" (WRONG)
System: "Yes!" and classifies as scaffold_progress

ROOT CAUSE:
AI Agent has shortcut logic:
- If detected_scaffolding_answer = true (keyword detected)
- Automatically classify as "scaffold_progress"
- NEVER validates if the keyword is CORRECT

SOLUTION:
Remove the automatic classification shortcut.
Force AI Agent to validate ALL answers for correctness, including conceptual ones.
"""

import json

def fix_ai_agent_validation(workflow):
    """Remove keyword shortcut, add proper validation logic."""

    for node in workflow['nodes']:
        if node['name'] == 'AI Agent':
            system_msg = node['parameters']['options']['systemMessage']

            # Find and replace the dangerous shortcut logic
            old_shortcut = """IMPORTANT: Two types of scaffolding answers to check:

1. KEYWORD ANSWERS (detected_scaffolding_answer flag):
   If detected_scaffolding_answer is true:
   - Student said operation/concept keywords ("adding", "right", etc.)
   - Classify as "scaffold_progress"
   - Set is_main_problem_attempt: false

2. NUMERIC ANSWERS (check manually):
   If student gave a NUMBER during scaffolding:
   - Extract the number from: "{{ $json.student_message }}"
   - Compare to main answer: {{ $json.current_problem.correct_answer }}
   - If MATCH → "scaffold_progress" (they solved it!)
   - If NO MATCH → "stuck" (they're working on sub-steps, likely wrong)
   - DEFAULT: When uncertain → "stuck"


Context:
- detected_scaffolding_answer: {{ $json.detected_scaffolding_answer }}
- Student said: "{{ $json.student_message }}"
- Scaffolding question: "{{ $json.scaffolding_last_question }}"
- Main problem: {{ $json.current_problem.text }}
- Correct answer: {{ $json.current_problem.correct_answer }}

DECISION PROCESS (follow this order):

STEP 1: ALWAYS call validate_scaffolding tool first
This tool provides the scaffolding question and student response for semantic analysis."""

            new_validation = """Context:
- Student said: "{{ $json.student_message }}"
- Scaffolding question: "{{ $json.scaffolding_last_question }}"
- Main problem: {{ $json.current_problem.text }}
- Correct answer: {{ $json.current_problem.correct_answer }}

CRITICAL: ALL answers must be validated for CORRECTNESS, not just detected as keywords.

DECISION PROCESS (follow this order):

STEP 1: ALWAYS call validate_scaffolding tool first
This tool provides the scaffolding question and student response for semantic analysis.

After calling the tool, YOU must evaluate semantic correctness using your reasoning:
- Question: "When we see +, are we adding or subtracting?"
  * Student: "adding" → CORRECT (+ means addition)
  * Student: "subtracting" → WRONG (+ does not mean subtraction)

- Question: "Which direction is right on the number line?"
  * Student: "right" → CORRECT
  * Student: "left" → WRONG

- Question: "What does -3 mean?"
  * Student: "negative 3" or "3 left of zero" → CORRECT
  * Student: "positive 3" → WRONG

DO NOT blindly accept keyword presence as correctness.
VALIDATE that the keyword is the CORRECT answer to the question."""

            if old_shortcut in system_msg:
                system_msg = system_msg.replace(old_shortcut, new_validation)
                print("Removed dangerous keyword shortcut")
            else:
                print("WARNING: Could not find exact shortcut text - may need manual update")
                print("Searching for partial match...")

                # Try partial replacement
                if "KEYWORD ANSWERS (detected_scaffolding_answer flag)" in system_msg:
                    # Find the section and remove it
                    start = system_msg.find("IMPORTANT: Two types of scaffolding answers")
                    if start != -1:
                        end = system_msg.find("STEP 1: ALWAYS call validate_scaffolding tool first")
                        if end != -1:
                            before = system_msg[:start]
                            after = system_msg[end:]
                            system_msg = before + new_validation[new_validation.find("STEP 1:"):]
                            print("Applied partial fix")

            node['parameters']['options']['systemMessage'] = system_msg
            print("\nAI Agent validation logic updated")
            return True

    print("ERROR: Could not find AI Agent node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print("\nFixing conceptual answer validation...\n")
    success = fix_ai_agent_validation(workflow)

    if success:
        print(f"\nWriting updated workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("Done!")

        print("\n" + "=" * 60)
        print("CONCEPTUAL VALIDATION FIX SUMMARY")
        print("=" * 60)
        print("Before: Keyword detection → automatic scaffold_progress")
        print("        'subtracting' detected → 'Yes!' (no validation)")
        print()
        print("After:  Keyword detection → semantic validation required")
        print("        'subtracting' to 'are we adding?' → WRONG → stuck")
        print("        'adding' to 'are we adding?' → CORRECT → scaffold_progress")
        print()
        print("Test cases:")
        print("  Q: 'When we see +, are we adding or subtracting?'")
        print("  1. Student: 'adding' → CORRECT → scaffold_progress")
        print("  2. Student: 'subtracting' → WRONG → stuck")
        print("  3. Student: 'plus' → CORRECT → scaffold_progress")
    else:
        print("\nFix failed - workflow not modified")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
