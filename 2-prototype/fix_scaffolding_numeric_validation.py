#!/usr/bin/env python3
"""
Fix Bug #13: AI Agent affirms wrong numeric answers during scaffolding.

PROBLEM:
Student: "I think we'd land at 5" (wrong, correct is 2)
Tutor: "Yes! That's right!" (should catch the error)
Category: scaffold_progress (should be stuck/wrong)

ROOT CAUSE:
The AI Agent has a permissive DEFAULT rule that bypasses math validation:
"DEFAULT: If answer shows ANY relevant understanding → category: 'scaffold_progress'"

SOLUTION:
1. Remove the permissive DEFAULT rule
2. Make CRITICAL MATH VALIDATION step mandatory
3. Add explicit handling for incorrect numeric answers
4. Emphasize NEVER affirm wrong answers
"""

import json

def fix_ai_agent_validation(workflow):
    """Strengthen AI Agent's numeric answer validation during scaffolding."""

    for node in workflow['nodes']:
        if node['name'] == 'AI Agent':
            system_msg = node['parameters']['options']['systemMessage']

            # Find and remove the problematic DEFAULT rule
            old_default = '''4. Classification decision:
   - If answer addresses scaffolding question correctly → category: "scaffold_progress"
   - If "I don't know" or genuinely confused → category: "stuck"
   - DEFAULT: If answer shows ANY relevant understanding → category: "scaffold_progress"'''

            new_decision = '''4. Classification decision:
   - If answer addresses scaffolding question correctly → category: "scaffold_progress"
   - If answer is NUMERIC but INCORRECT (doesn't match calculated answer) → category: "stuck"
   - If "I don't know" or genuinely confused → category: "stuck"
   - If answer shows relevant conceptual understanding (non-numeric) → category: "scaffold_progress"

   CRITICAL: NEVER classify as scaffold_progress if student gave wrong numeric answer.
   ALWAYS validate numeric answers against the calculated correct answer first.'''

            if old_default in system_msg:
                system_msg = system_msg.replace(old_default, new_decision)
                print("Updated classification decision rules")
            else:
                print("WARNING: Could not find exact DEFAULT rule text")
                print("Attempting alternative update...")

                # Try updating just the DEFAULT line
                if '- DEFAULT: If answer shows ANY relevant understanding → category: "scaffold_progress"' in system_msg:
                    system_msg = system_msg.replace(
                        '- DEFAULT: If answer shows ANY relevant understanding → category: "scaffold_progress"',
                        '''- If answer is NUMERIC but INCORRECT → category: "stuck"
   - If answer shows relevant conceptual understanding (non-numeric) → category: "scaffold_progress"

   CRITICAL: NEVER classify as scaffold_progress if student gave wrong numeric answer.'''
                    )
                    print("Updated DEFAULT rule via alternative method")

            # Strengthen the CRITICAL MATH VALIDATION section
            old_validation_intro = '''**CRITICAL MATH VALIDATION STEP**:
If the scaffolding question contains a mathematical calculation (e.g., "what is -3 + 1?", "add 3 to -3", "what happens when we add 2?"):'''

            new_validation_intro = '''**CRITICAL MATH VALIDATION STEP** (MANDATORY FOR NUMERIC ANSWERS):
If the scaffolding question asks for a numeric answer OR student gives a number:

YOU MUST VALIDATE THE ANSWER. Follow these steps:'''

            if old_validation_intro in system_msg:
                system_msg = system_msg.replace(old_validation_intro, new_validation_intro)
                print("Strengthened CRITICAL MATH VALIDATION requirement")

            # Update the comparison logic
            old_comparison = '''3. Compare the student's extracted answer to your calculated answer
   - If they match → student is CORRECT → category: "scaffold_progress"
   - If they don't match → student is incorrect → category: "stuck"'''

            new_comparison = '''3. Compare the student's extracted answer to your calculated answer
   - If they match → student is CORRECT → category: "scaffold_progress"
   - If they don't match → student is INCORRECT → category: "stuck"

   NEVER say "Yes! That's right!" if the numbers don't match.
   NEVER affirm a wrong answer, even if it shows partial understanding.'''

            if old_comparison in system_msg:
                system_msg = system_msg.replace(old_comparison, new_comparison)
                print("Added explicit NO-AFFIRMATION rule for wrong answers")

            # Add examples of WRONG scaffolding answers
            examples_section = '''
EXAMPLES OF CORRECT VS INCORRECT SCAFFOLDING ANSWERS:

Scaffolding Q: "If we start at -3 and move 5 steps right, where do we land?"
Correct answer: 2 (calculation: -3+5 = 2)
- Student: "2" → CORRECT → scaffold_progress → "Yes! We land at 2..."
- Student: "5" → WRONG → stuck → "Not quite. Let's count together: -2, -1, 0, 1, 2..."
- Student: "8" → WRONG → stuck → "That's not quite right. Remember we START at -3..."

Scaffolding Q: "What is -3 + 1?"
Correct answer: -2
- Student: "-2" or "negative 2" → CORRECT → scaffold_progress
- Student: "-4" → WRONG → stuck
- Student: "4" → WRONG → stuck

CRITICAL RULE: If the numbers don't match, classification MUST be "stuck", NOT "scaffold_progress".
'''

            # Insert examples before the "If SCAFFOLDING RESPONSE:" section
            marker = 'If SCAFFOLDING RESPONSE:'
            if marker in system_msg:
                system_msg = system_msg.replace(marker, examples_section + '\n' + marker)
                print("Added examples of correct vs incorrect scaffolding answers")

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

    print("\nFixing AI Agent scaffolding numeric validation...\n")
    success = fix_ai_agent_validation(workflow)

    if success:
        print(f"\nWriting updated workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("Done!")

        print("\n" + "=" * 60)
        print("BUG #13 FIX SUMMARY")
        print("=" * 60)
        print("Before: AI Agent used permissive DEFAULT rule")
        print("        'Any relevant understanding → scaffold_progress'")
        print("        Result: Wrong answers like '5' were affirmed")
        print()
        print("After:  Mandatory validation for numeric answers")
        print("        'If numeric but INCORRECT → stuck'")
        print("        Added examples and NO-AFFIRMATION rule")
        print()
        print("Test case:")
        print("  Q: 'If we start at -3 and move 5 steps right, where do we land?'")
        print("  Student: 'I think we'd land at 5'")
        print("  Expected: 'Not quite. Let's count together...' (category: stuck)")
    else:
        print("\nFix failed - workflow not modified")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
