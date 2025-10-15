#!/usr/bin/env python3
"""
Simplify AI Agent validation to be more explicit and actionable.

PROBLEM:
Complex CRITICAL MATH VALIDATION section isn't being followed by LLM.
Student says "1?" (wrong, correct is 2) → Tutor says "Yes! That's right!"

ROOT CAUSE:
Asking LLM to calculate math, extract numbers, and compare is too complex.
LLMs are not reliable at multi-step math reasoning.

SOLUTION:
Replace complex validation with simple explicit rule at the very top:
- If scaffolding AND numeric answer AND doesn't match main answer → stuck
- Make this the FIRST check, before any other logic
"""

import json

def simplify_validation(workflow):
    """Simplify AI Agent validation to be more explicit."""

    for node in workflow['nodes']:
        if node['name'] == 'AI Agent':
            system_msg = node['parameters']['options']['systemMessage']

            # Remove the complex CRITICAL MATH VALIDATION section
            # Find it and replace with simple rule
            old_validation = '''**CRITICAL MATH VALIDATION STEP** (MANDATORY FOR NUMERIC ANSWERS):
If the scaffolding question asks for a numeric answer OR student gives a number:

YOU MUST VALIDATE THE ANSWER. Follow these steps:

1. FIRST, calculate the correct answer yourself step-by-step
   Example: "add 3 to -3" → -3 + 3 → Start at -3, move right 3 → arrive at 0 → answer is 0

2. Extract the student's numeric answer (handle variations):
   - "0", "zero", "we get 0", "it's zero" → all mean 0
   - "-2", "negative 2", "minus 2", "we get -2" → all mean -2

3. Compare the student's extracted answer to your calculated answer
   - If they match → student is CORRECT → category: "scaffold_progress"
   - If they don't match → student is INCORRECT → category: "stuck"

   NEVER say "Yes! That's right!" if the numbers don't match.
   NEVER affirm a wrong answer, even if it shows partial understanding.

4. ALWAYS verify your math calculation before judging the student's response'''

            new_validation = '''**NUMERIC SCAFFOLDING ANSWER CHECK** (DO THIS FIRST):

If scaffolding is active AND student gave a numeric answer:

1. Extract student's number from "{{ $json.student_message }}"
   ("1", "one", "1?", "I think 1" all mean 1)

2. Compare to main problem answer: {{ $json.current_problem.correct_answer }}

3. Decision:
   - Numbers MATCH → Student solved the main problem! → "scaffold_progress"
   - Numbers DON'T MATCH → Student answering sub-question → Check if correct for sub-question
     * If you can't verify sub-question correctness → DEFAULT to "stuck"
     * NEVER classify as "scaffold_progress" unless certain answer is correct

CRITICAL: When in doubt about correctness → classify as "stuck" (safe default)
NEVER say "Yes! That's right!" unless you are CERTAIN the answer is correct'''

            if old_validation in system_msg:
                system_msg = system_msg.replace(old_validation, new_validation)
                print("Replaced complex CRITICAL MATH VALIDATION")
            else:
                print("Could not find exact CRITICAL MATH VALIDATION text")
                # Try to find it by header
                if '**CRITICAL MATH VALIDATION STEP**' in system_msg:
                    # Find where it starts and ends
                    start_marker = '**CRITICAL MATH VALIDATION STEP**'
                    start_idx = system_msg.find(start_marker)

                    # Find the end (next section header or "If SCAFFOLDING RESPONSE:")
                    end_marker = 'If SCAFFOLDING RESPONSE:'
                    end_idx = system_msg.find(end_marker, start_idx)

                    if start_idx != -1 and end_idx != -1:
                        # Replace the entire section
                        old_section = system_msg[start_idx:end_idx]
                        system_msg = system_msg.replace(old_section, new_validation + '\n\n')
                        print("Replaced CRITICAL MATH VALIDATION via section replacement")

            # Also simplify the classification decision rules
            old_decision = '''4. Classification decision:
   - If answer addresses scaffolding question correctly → category: "scaffold_progress"
   - If answer is NUMERIC but INCORRECT (doesn't match calculated answer) → category: "stuck"
   - If "I don't know" or genuinely confused → category: "stuck"
   - If answer shows relevant conceptual understanding (non-numeric) → category: "scaffold_progress"

   CRITICAL: NEVER classify as scaffold_progress if student gave wrong numeric answer.
   ALWAYS validate numeric answers against the calculated correct answer first.'''

            new_decision = '''4. Classification decision:
   - If answer is NUMERIC and MATCHES main problem answer → "scaffold_progress" (solved it!)
   - If answer is NUMERIC but doesn't match → "stuck" (needs help with sub-steps)
   - If "I don't know" or confused → "stuck"
   - If conceptual answer (like "adding", "right") → Check if correct, then "scaffold_progress"

   DEFAULT SAFE RULE: When uncertain → classify as "stuck"
   NEVER classify as "scaffold_progress" unless answer is clearly correct'''

            if old_decision in system_msg:
                system_msg = system_msg.replace(old_decision, new_decision)
                print("Simplified classification decision rules")

            # Move the numeric check to the very top of the prompt
            # Find the detected_scaffolding_answer section and add explicit numeric check after it
            detected_flag_section = '''IMPORTANT: Check the context for a 'detected_scaffolding_answer' flag.
If detected_scaffolding_answer is true:
  - The student's response contains operation/concept keywords
  - You MUST classify as "scaffold_progress" (correct scaffolding answer)
  - Set is_main_problem_attempt: false
  - Return immediately without deep analysis'''

            enhanced_flag_section = '''IMPORTANT: Two types of scaffolding answers to check:

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
   - DEFAULT: When uncertain → "stuck"'''

            if detected_flag_section in system_msg:
                system_msg = system_msg.replace(detected_flag_section, enhanced_flag_section)
                print("Enhanced detected_scaffolding_answer section with numeric check")

            node['parameters']['options']['systemMessage'] = system_msg
            print("\nAI Agent validation simplified")
            return True

    print("ERROR: Could not find AI Agent node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print("\nSimplifying AI Agent validation logic...\n")
    success = simplify_validation(workflow)

    if success:
        print(f"\nWriting updated workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("Done!")

        print("\n" + "=" * 60)
        print("VALIDATION SIMPLIFICATION SUMMARY")
        print("=" * 60)
        print("Before: Complex multi-step CRITICAL MATH VALIDATION")
        print("        Asked LLM to calculate, extract, and compare")
        print("        Not followed reliably")
        print()
        print("After:  Simple explicit rules")
        print("        1. Extract student number")
        print("        2. Compare to main answer")
        print("        3. Match → progress, No match → stuck")
        print("        4. Default to stuck when uncertain")
        print()
        print("Test case:")
        print("  Main problem: What is -3 + 5? (answer: 2)")
        print("  Student: '1?' (during scaffolding)")
        print("  Expected: 1 ≠ 2 → stuck → 'Not quite...'")
    else:
        print("\nFix failed - workflow not modified")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
