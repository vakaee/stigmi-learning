#!/usr/bin/env python3
"""
Fix scaffolding state not being set when non-stuck categories ask scaffolding questions.

Bug: Update Session only sets scaffolding.active = true for category 'stuck',
but other categories (like 'wrong_operation') can also ask scaffolding questions.

Fix: Add heuristic detection to identify scaffolding questions by content, not category.
"""

import json

def fix_update_session_node(workflow):
    """Add scaffolding question detection to Update Session node."""

    for node in workflow['nodes']:
        if node['name'] == 'Update Session & Format Response':
            old_code = node['parameters']['jsCode']

            # Find where state transitions start
            # We need to add detection BEFORE "// STATE TRANSITIONS"

            new_code = old_code.replace(
                '// STATE TRANSITIONS',
                '''// DETECT SCAFFOLDING QUESTIONS (regardless of category)
// This prevents bug where wrong_operation/close/etc ask scaffolding questions
// but don't set scaffolding.active = true
const isScaffoldingQuestion = response.includes('?') && (
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
);

// STATE TRANSITIONS'''
            )

            # Now update the scaffolding state management section
            # Replace the first scaffolding activation condition
            new_code = new_code.replace(
                '''// 1. SCAFFOLDING STATE MANAGEMENT
if (category === 'stuck' && !contextData.is_scaffolding_active && !contextData.is_teach_back_active) {
  session.current_problem.scaffolding = {
    active: true,
    depth: 1,
    last_question: response
  };
}''',
                '''// 1. SCAFFOLDING STATE MANAGEMENT
// Activate scaffolding if response is a scaffolding question (detected heuristically)
if (isScaffoldingQuestion && !contextData.is_scaffolding_active && !contextData.is_teach_back_active) {
  session.current_problem.scaffolding = {
    active: true,
    depth: 1,
    last_question: response
  };
}'''
            )

            node['parameters']['jsCode'] = new_code
            print(f"✓ Updated 'Update Session & Format Response' node")
            print(f"  - Added scaffolding question detection (25 patterns)")
            print(f"  - Changed activation from 'stuck only' to 'any scaffolding question'")
            return True

    print("✗ ERROR: Could not find 'Update Session & Format Response' node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print(f"Applying fix...")
    success = fix_update_session_node(workflow)

    if success:
        print(f"\nWriting updated workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("✓ Done!")
        print("\nFix Summary:")
        print("  - Scaffolding state now activated by content, not category")
        print("  - 25 patterns including: 'are we', 'can you picture', 'starting at', 'count up', etc.")
        print("  - This fixes bugs where scaffolding responses like 'adding' were misclassified")
        print("  - Fixes generic 'No problem!' acknowledgements for all responses")
    else:
        print("\n✗ Fix failed - workflow not modified")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
