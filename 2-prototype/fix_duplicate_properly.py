#!/usr/bin/env python3
"""
Properly remove duplicate detection block - keep only ONE instance.
"""

import json
import re

def fix_duplicate(workflow):
    """Remove duplicate detection logic, keeping only one."""

    for node in workflow['nodes']:
        if node['name'] == 'Prepare Agent Context':
            code = node['parameters']['jsCode']

            # Pattern to match the entire detection block
            pattern = r'// ===== SCAFFOLDING CONCEPTUAL ANSWER DETECTION =====.*?(?=\n\nreturn \[\{|return \[\{)'

            matches = list(re.finditer(pattern, code, re.DOTALL))
            count = len(matches)

            print(f'Found {count} detection blocks')

            if count > 1:
                # Remove all but the LAST occurrence (closest to return)
                # We want to keep the one just before the return statement
                for match in matches[:-1]:  # Remove all except last
                    code = code[:match.start()] + code[match.end():]

                node['parameters']['jsCode'] = code
                print(f"✓ Removed {count-1} duplicate detection block(s)")
                print("  - Kept the last block (just before return)")
                return True
            elif count == 1:
                print("✓ Only one block found - no duplicates")
                return True
            else:
                print("✗ No detection blocks found")
                return False

    print("✗ ERROR: Could not find Prepare Agent Context node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print("Fixing duplicates...")
    success = fix_duplicate(workflow)

    if success:
        print(f"\nWriting fixed workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("✓ Done!")

        # Verify
        with open(output_file, 'r') as f:
            w = json.load(f)
        for node in w['nodes']:
            if node['name'] == 'Prepare Agent Context':
                code = node['parameters']['jsCode']
                count = code.count('let detectedScaffoldingAnswer')
                print(f"\nVerification: Variable declared {count} time(s)")
                if count == 1:
                    print("✓ SUCCESS")
                else:
                    print("✗ FAILED")
    else:
        print("\n✗ Fix failed")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
