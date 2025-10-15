#!/usr/bin/env python3
"""
Strengthen AI Agent's scaffolding validation for conceptual answers.

Makes it explicitly clear that operation/concept keywords (adding, subtracting, etc.)
should be classified as scaffold_progress.
"""

import json

def strengthen_scaffolding_validation(workflow):
    """Update AI Agent to be more explicit about conceptual answers."""

    for node in workflow['nodes']:
        if node['name'] == 'AI Agent':
            system_msg = node['parameters']['options']['systemMessage']

            # Find the scaffolding response section
            old_section = '''3. Be FLEXIBLE with answer formats:
   * Numeric: "5", "five", "5 spaces", "five spaces" all mean the same
   * Directional: "right", "to the right", "move right" all mean the same
   * Position: "-3", "negative 3", "minus 3", "3 left of zero" all mean the same'''

            new_section = '''3. Be FLEXIBLE with answer formats:
   * Numeric: "5", "five", "5 spaces", "five spaces" all mean the same
   * Directional: "right", "to the right", "move right" all mean the same
   * Position: "-3", "negative 3", "minus 3", "3 left of zero" all mean the same
   * Conceptual: "adding", "we are adding", "we're adding" all mean the same
   * Operations: "subtract", "subtracting", "take away" all mean the same'''

            if old_section in system_msg:
                system_msg = system_msg.replace(old_section, new_section)
                node['parameters']['options']['systemMessage'] = system_msg
                print("✓ Updated AI Agent scaffolding validation")
                print("  - Added explicit handling for conceptual/operation answers")
                print("  - Examples: 'adding', 'we are adding', 'subtracting'")
                return True
            else:
                print("✗ Could not find expected scaffolding section")
                return False

    print("✗ ERROR: Could not find AI Agent node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print("Strengthening AI Agent scaffolding validation...")
    success = strengthen_scaffolding_validation(workflow)

    if success:
        print(f"\nWriting updated workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("✓ Done!")
    else:
        print("\n✗ Fix failed - workflow not modified")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
