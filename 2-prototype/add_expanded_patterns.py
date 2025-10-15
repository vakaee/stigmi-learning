#!/usr/bin/env python3
"""
Add the expanded scaffolding detection patterns back to Update Session node.
"""

import json

def add_expanded_patterns(workflow):
    """Add expanded patterns to isScaffoldingQuestion declaration."""

    for node in workflow['nodes']:
        if node['name'] == 'Update Session & Format Response':
            code = node['parameters']['jsCode']

            # Find the declaration and replace it with the expanded version
            old_pattern = '''const isScaffoldingQuestion = response.includes('?') && (
  response.toLowerCase().includes('are we') ||
  response.toLowerCase().includes('are you') ||
  response.toLowerCase().includes('can you') ||
  response.toLowerCase().includes('what does') ||
  response.toLowerCase().includes('what is') ||
  response.toLowerCase().includes('mean') ||
  response.toLowerCase().includes('think about') ||
  response.toLowerCase().includes('how many') ||
  response.toLowerCase().includes('how do') ||
  response.toLowerCase().includes('can you tell me') ||
  response.toLowerCase().includes('where is') ||
  response.toLowerCase().includes('where does') ||
  response.toLowerCase().includes('which direction') ||
  response.toLowerCase().includes("let's start") ||
  response.toLowerCase().includes("let's think")
);'''

            new_pattern = '''const isScaffoldingQuestion = response.includes('?') && (
  response.toLowerCase().includes('are we') ||
  response.toLowerCase().includes('are you') ||
  response.toLowerCase().includes('can you') ||
  response.toLowerCase().includes('what does') ||
  response.toLowerCase().includes('what is') ||
  response.toLowerCase().includes('mean') ||
  response.toLowerCase().includes('think about') ||
  response.toLowerCase().includes('how many') ||
  response.toLowerCase().includes('how do') ||
  response.toLowerCase().includes('can you tell me') ||
  response.toLowerCase().includes('where is') ||
  response.toLowerCase().includes('where does') ||
  response.toLowerCase().includes('which direction') ||
  response.toLowerCase().includes("let's start") ||
  response.toLowerCase().includes("let's think") ||
  response.toLowerCase().includes("can you picture") ||
  response.toLowerCase().includes("picture") ||
  response.toLowerCase().includes("imagine") ||
  response.toLowerCase().includes("visualize") ||
  response.toLowerCase().includes("climbing") ||
  response.toLowerCase().includes("moving") ||
  response.toLowerCase().includes("starting at") ||
  response.toLowerCase().includes("count up") ||
  response.toLowerCase().includes("count those") ||
  response.toLowerCase().includes("keep going")
);'''

            if old_pattern not in code:
                print("✗ ERROR: Could not find old pattern to replace")
                print("The code might already have the expanded patterns or be in a different format")
                return False

            new_code = code.replace(old_pattern, new_pattern)
            node['parameters']['jsCode'] = new_code

            print("✓ Added 10 expanded scaffolding detection patterns")
            print("  Total patterns: 25")
            return True

    print("✗ ERROR: Could not find Update Session node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print("Adding expanded patterns...")
    success = add_expanded_patterns(workflow)

    if success:
        print(f"\nWriting updated workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("✓ Done!")
    else:
        print("\n✗ No changes made")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
