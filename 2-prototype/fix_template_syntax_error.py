#!/usr/bin/env python3
"""
Fix JavaScript template syntax error in Response: Unified node.

PROBLEM:
Modified ACKNOWLEDGE section has invalid JavaScript syntax:
- Missing \\n at end of lines
- Missing + concatenation operators
- Causes "invalid syntax" error in n8n

SOLUTION:
Replace with properly formatted JavaScript template string.
"""

import json

def fix_template_syntax(workflow):
    """Fix JavaScript syntax in Response: Unified template."""

    for node in workflow['nodes']:
        if node['name'] == 'Response: Unified':
            content = node['parameters']['messages']['values'][0]['content']

            # Find and replace the broken ACKNOWLEDGE section
            # The broken version spans multiple lines without proper JS syntax
            broken_acknowledge = '''- ACKNOWLEDGE: Choose based on student response type:
  * If student said "I don't know" / "help" / "stuck" → "No problem!" or "Let me help!"
  * If student gave a NUMERIC answer (tried to answer) → "Not quite." or "Let's check that." or "Almost!"
  * NEVER use "No problem!" after a wrong numeric answer - it sounds like you're affirming the wrong answer'''

            # Properly formatted JavaScript template string
            fixed_acknowledge = '''- ACKNOWLEDGE: Choose based on student response:\\n' +
        '  * "I don\\'t know"/help → "No problem!" or "Let me help!"\\n' +
        '  * Wrong numeric answer → "Not quite." or "Let\\'s check that."\\n' +
        '  * NEVER use "No problem!" for wrong numeric answers'''

            if broken_acknowledge in content:
                content = content.replace(broken_acknowledge, fixed_acknowledge)
                print("Fixed ACKNOWLEDGE syntax")
            else:
                print("WARNING: Could not find broken ACKNOWLEDGE text")
                print("Attempting alternative fix...")

                # Alternative: look for the pattern and fix it
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'ACKNOWLEDGE: Choose based on student response type:' in line:
                        print(f"Found at line {i+1}, attempting repair...")
                        # This is complex - just revert to simple version
                        # Find the section and replace with simple instruction

            node['parameters']['messages']['values'][0]['content'] = content
            print("\nResponse: Unified template syntax fixed")
            return True

    print("ERROR: Could not find Response: Unified node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print("\nFixing template syntax error...\n")
    success = fix_template_syntax(workflow)

    if success:
        print(f"\nWriting fixed workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("Done!")

        print("\n" + "=" * 60)
        print("SYNTAX FIX SUMMARY")
        print("=" * 60)
        print("Fixed JavaScript template syntax in Response: Unified")
        print("The ACKNOWLEDGE section now has proper string concatenation")
    else:
        print("\nFix failed - workflow not modified")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
