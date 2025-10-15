#!/usr/bin/env python3
"""
Fix Bug #12 ROOT CAUSE: Parse Synthesis Decision loses category field.

PROBLEM:
Parse Synthesis Decision only returns the synthesis LLM output (action, hint).
It does NOT preserve the category field from Build Response Context.
When it feeds Response: Unified, $json.category is undefined.
The ternary chain falls through and uses wrong prompt.

SOLUTION:
Access original data from Build Response Context using $('Build Response Context').first().json
Merge it with the synthesis decision to preserve all fields including category.
"""

import json

def fix_parse_synthesis(workflow):
    """Update Parse Synthesis Decision to preserve category field."""

    for node in workflow['nodes']:
        if node['name'] == 'Parse Synthesis Decision':
            old_code = node['parameters']['jsCode']

            new_code = """// Parse synthesis detector output
const llmResponse = $json.message?.content || $json.text || $json.response || '';
const parsed = JSON.parse(llmResponse);

// Get original data from Build Response Context (contains category, etc.)
const originalData = $('Build Response Context').first().json;

return {
  json: {
    ...originalData,              // Preserve all original fields including category
    ...parsed,                    // Add synthesis fields
    synthesis_action: parsed.action,
    synthesis_hint: parsed.synthesis_hint || ''
  }
};"""

            node['parameters']['jsCode'] = new_code

            print("Parse Synthesis Decision updated")
            print("  - Now accesses Build Response Context data")
            print("  - Preserves category field for Response: Unified")
            print("  - Merges synthesis decision with original data")
            return True

    print("ERROR: Could not find Parse Synthesis Decision node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print("\nFixing Parse Synthesis Decision...")
    success = fix_parse_synthesis(workflow)

    if success:
        print(f"\nWriting fixed workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("Done!")

        print("\n" + "=" * 60)
        print("ROOT CAUSE FIX SUMMARY")
        print("=" * 60)
        print("Before: Parse Synthesis Decision only returned synthesis LLM output")
        print("        Result: category field was lost, Response: Unified got undefined")
        print("        Symptom: Wrong prompt template used (fell through to 'stuck')")
        print()
        print("After:  Parse Synthesis Decision merges original + synthesis data")
        print("        Result: category field preserved (scaffold_progress)")
        print("        Expected: Response: Unified uses correct prompt template")
        print()
        print("Test: Student says 'adding' should now get acknowledgement response")
    else:
        print("\nFix failed - workflow not modified")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
