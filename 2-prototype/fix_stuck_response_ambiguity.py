#!/usr/bin/env python3
"""
Fix stuck response template to distinguish between help-seeking vs wrong answers.

PROBLEM:
Student: "5" (wrong, correct is 2)
Response: "No problem! Let's think about it together..."

"No problem!" is ambiguous - sounds affirming rather than correcting.

ROOT CAUSE:
The stuck template uses "No problem!" for ALL stuck cases:
- When student says "I don't know" (appropriate)
- When student gives wrong number (inappropriate - needs correction)

SOLUTION:
Update the ACKNOWLEDGE instruction to use context-aware opening:
- If student says "I don't know" or help phrase → "No problem!"
- If student gives numeric answer → "Not quite." or "Let's check that."
"""

import json

def fix_stuck_acknowledgement(workflow):
    """Update stuck template to handle wrong numeric answers appropriately."""

    for node in workflow['nodes']:
        if node['name'] == 'Response: Unified':
            content = node['parameters']['messages']['values'][0]['content']

            # Find the stuck scaffolding section (line 126)
            old_acknowledge = '''- ACKNOWLEDGE: "No problem!" or "Let me help!"'''

            new_acknowledge = '''- ACKNOWLEDGE: Choose based on student response type:
  * If student said "I don't know" / "help" / "stuck" → "No problem!" or "Let me help!"
  * If student gave a NUMERIC answer (tried to answer) → "Not quite." or "Let's check that." or "Almost!"
  * NEVER use "No problem!" after a wrong numeric answer - it sounds like you're affirming the wrong answer'''

            if old_acknowledge in content:
                content = content.replace(old_acknowledge, new_acknowledge)
                print("Updated stuck ACKNOWLEDGE instruction")
            else:
                print("WARNING: Could not find exact ACKNOWLEDGE text")

            # Also add explicit instruction to correct wrong answers
            old_structure = '''- ANTI-LOOP CHECK: Read last tutor message in chat history
- If you already asked this question, rephrase it MORE SIMPLY
- OR break into even SMALLER sub-question'''

            new_structure = '''- ANTI-LOOP CHECK: Read last tutor message in chat history
- If you already asked this question, rephrase it MORE SIMPLY
- OR break into even SMALLER sub-question
- If student gave wrong numeric answer, gently correct it:
  * Example: "Not quite. Let's count together from -3: -2, -1, 0, 1, 2. Where do we land?"
  * DO NOT just repeat the question - show them how to get the correct answer'''

            if old_structure in content:
                content = content.replace(old_structure, new_structure)
                print("Added explicit correction instruction for wrong numeric answers")

            node['parameters']['messages']['values'][0]['content'] = content
            print("\nStuck response template updated")
            return True

    print("ERROR: Could not find Response: Unified node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print("\nFixing stuck response ambiguity...\n")
    success = fix_stuck_acknowledgement(workflow)

    if success:
        print(f"\nWriting updated workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("Done!")

        print("\n" + "=" * 60)
        print("STUCK RESPONSE FIX SUMMARY")
        print("=" * 60)
        print("Before: Used 'No problem!' for all stuck cases")
        print("        Sounded affirming even for wrong answers")
        print()
        print("After:  Context-aware acknowledgement")
        print("        'I don't know' → 'No problem!'")
        print("        Wrong number → 'Not quite. Let's count together...'")
        print()
        print("Test case:")
        print("  Q: 'Where do we land after moving 5 steps from -3?'")
        print("  Student: '5'")
        print("  Expected: 'Not quite. Let's count together from -3: -2, -1, 0, 1, 2...'")
    else:
        print("\nFix failed - workflow not modified")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
