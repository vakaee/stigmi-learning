#!/usr/bin/env python3
"""
Fix duplicate isScaffoldingQuestion declaration in Update Session node.
The fix script was run twice, creating a duplicate declaration.
"""

import json

def remove_duplicate_declaration(workflow):
    """Remove the duplicate isScaffoldingQuestion declaration."""

    for node in workflow['nodes']:
        if node['name'] == 'Update Session & Format Response':
            code = node['parameters']['jsCode']

            # Split into lines
            lines = code.split('\n')

            # Find both declarations
            first_declaration_line = None
            second_declaration_line = None

            for i, line in enumerate(lines):
                if 'const isScaffoldingQuestion = response.includes' in line:
                    if first_declaration_line is None:
                        first_declaration_line = i
                    else:
                        second_declaration_line = i
                        break

            if second_declaration_line is None:
                print("No duplicate found - code is clean")
                return False

            print(f"Found duplicate at lines {first_declaration_line + 1} and {second_declaration_line + 1}")

            # Find the end of the second declaration (the closing );)
            end_line = second_declaration_line
            for i in range(second_declaration_line, len(lines)):
                if ');' in lines[i]:
                    end_line = i
                    break

            print(f"Removing lines {second_declaration_line + 1} to {end_line + 1}")

            # Remove the duplicate declaration and the blank line after it
            # Keep lines before second declaration, skip the declaration itself, keep lines after
            new_lines = lines[:second_declaration_line] + lines[end_line + 2:]

            new_code = '\n'.join(new_lines)
            node['parameters']['jsCode'] = new_code

            print("✓ Removed duplicate isScaffoldingQuestion declaration")
            return True

    print("✗ ERROR: Could not find Update Session node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print("Fixing duplicate declaration...")
    success = remove_duplicate_declaration(workflow)

    if success:
        print(f"\nWriting fixed workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("✓ Done! Workflow fixed.")
    else:
        print("\n✗ No changes made")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
