#!/usr/bin/env python3
"""
Remove duplicate detectedScaffoldingAnswer declaration from Prepare Agent Context.
The fix script ran twice, creating a duplicate.
"""

import json

def remove_duplicate(workflow):
    """Remove the duplicate detection logic."""

    for node in workflow['nodes']:
        if node['name'] == 'Prepare Agent Context':
            code = node['parameters']['jsCode']

            # Find the detection block
            detection_start = '// ===== SCAFFOLDING CONCEPTUAL ANSWER DETECTION ====='

            # Count occurrences
            count = code.count(detection_start)
            print(f'Detection blocks found: {count}')

            if count > 1:
                # Find the first occurrence and the second occurrence
                first_idx = code.find(detection_start)
                second_idx = code.find(detection_start, first_idx + 1)

                # Find the end of the first block (before the "return [{")
                # The block ends at the next "return [{"
                first_block_end = code.find('return [{', first_idx)

                # Remove the first block (keep the second one which is closer to return)
                code = code[:first_idx] + code[first_block_end:]

                node['parameters']['jsCode'] = code

                print("✓ Removed first duplicate detection block")
                print("  - Kept the second block (closer to return statement)")
                return True
            else:
                print("No duplicate found")
                return False

    print("✗ ERROR: Could not find Prepare Agent Context node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print("Removing duplicate detection logic...")
    success = remove_duplicate(workflow)

    if success:
        print(f"\nWriting fixed workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("✓ Done!")
    else:
        print("\n✗ No changes made")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
