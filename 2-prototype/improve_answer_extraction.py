#!/usr/bin/env python3
"""
Improve answer extraction for numeric scaffolding validation.

PROBLEM:
Student: "that's 5 steps and we get 2"
LLM extracts: "5" (first number, part of process)
Should extract: "2" (the actual answer)

ROOT CAUSE:
Extraction instruction is too simple - doesn't specify how to handle
multiple numbers in student response.

SOLUTION:
Add explicit instruction to look for ANSWER PHRASES, not just any number.
"""

import json

def improve_extraction(workflow):
    """Improve answer extraction logic in AI Agent."""

    for node in workflow['nodes']:
        if node['name'] == 'AI Agent':
            system_msg = node['parameters']['options']['systemMessage']

            # Find the numeric scaffolding check section
            old_extraction = '''1. Extract student's number from "{{ $json.student_message }}"
   ("1", "one", "1?", "I think 1" all mean 1)

2. Compare to main problem answer: {{ $json.current_problem.correct_answer }}'''

            new_extraction = '''1. Extract student's ANSWER (look for answer phrases, not process):

   ANSWER PHRASES to look for:
   - "we get X", "land on X", "it's X", "equals X", "is X"
   - "I think X", "X?" (when X is standalone)

   IGNORE process descriptions:
   - "5 steps" (that's process, not answer)
   - "move 5" (that's process, not answer)

   EXAMPLES:
   - "that's 5 steps and we get 2" → extract 2 (answer phrase "get 2")
   - "move 5 steps to reach 2" → extract 2 (answer phrase "reach 2")
   - "I think we get 5" → extract 5 (answer phrase "get 5")
   - "5?" → extract 5 (standalone number)
   - "I think 1" → extract 1 (answer phrase "think 1")

2. Compare extracted answer to main problem answer: {{ $json.current_problem.correct_answer }}'''

            if old_extraction in system_msg:
                system_msg = system_msg.replace(old_extraction, new_extraction)
                print("Improved answer extraction with phrase detection")
            else:
                print("Could not find exact extraction text")

            # Also improve the decision logic to be clearer about what "match" means
            old_decision = '''3. Decision:
   - Numbers MATCH → Student solved the main problem! → "scaffold_progress"
   - Numbers DON'T MATCH → Student answering sub-question → Check if correct for sub-question
     * If you can't verify sub-question correctness → DEFAULT to "stuck"
     * NEVER classify as "scaffold_progress" unless certain answer is correct'''

            new_decision = '''3. Decision based on comparison:

   IF EXTRACTED ANSWER MATCHES MAIN ANSWER:
   - Student just solved the main problem!
   - Classify: "scaffold_progress"
   - Example: Main answer is 2, student says "we get 2" → MATCH → celebrate!

   IF EXTRACTED ANSWER DOESN'T MATCH:
   - Student is working on sub-steps OR gave wrong answer
   - Classify: "stuck"
   - Example: Main answer is 2, student says "I think 5" → NO MATCH → help them

   CRITICAL: Focus on extracting the ANSWER, not process numbers
   "5 steps and we get 2" → answer is 2, NOT 5'''

            if old_decision in system_msg:
                system_msg = system_msg.replace(old_decision, new_decision)
                print("Clarified decision logic with answer focus")

            node['parameters']['options']['systemMessage'] = system_msg
            print("\nAnswer extraction improved")
            return True

    print("ERROR: Could not find AI Agent node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print("\nImproving answer extraction...\n")
    success = improve_extraction(workflow)

    if success:
        print(f"\nWriting updated workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("Done!")

        print("\n" + "=" * 60)
        print("ANSWER EXTRACTION IMPROVEMENT SUMMARY")
        print("=" * 60)
        print("Before: Extract any number from student message")
        print("        'that's 5 steps and we get 2' → extracted 5")
        print()
        print("After:  Extract ANSWER using phrase detection")
        print("        Look for: 'get 2', 'land on 2', 'it's 2'")
        print("        Ignore: '5 steps' (process description)")
        print("        'that's 5 steps and we get 2' → extract 2")
        print()
        print("Test cases:")
        print("  1. 'I think we get 5' → extract 5 → compare to 2 → stuck")
        print("  2. 'that's 5 steps and we get 2' → extract 2 → compare to 2 → progress!")
        print("  3. '1?' → extract 1 → compare to 2 → stuck")
    else:
        print("\nFix failed - workflow not modified")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
