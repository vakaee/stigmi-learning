#!/usr/bin/env python3
"""
Fix Bug #12: Scaffolding conceptual answers not being recognized.

When student answers a clarifying question like "are we adding or subtracting?"
with "we are adding", the AI Agent doesn't recognize it as scaffold_progress.

Solution: Add pattern detection for common scaffolding conceptual answers
BEFORE routing to AI Agent. If scaffolding is active and message matches
operation/concept keywords, pre-classify as scaffold_progress.
"""

import json

def add_scaffolding_answer_detection(workflow):
    """Add pattern detection for scaffolding conceptual answers."""

    for node in workflow['nodes']:
        if node['name'] == 'Build Response Context':
            old_code = node['parameters']['jsCode']

            # Add detection logic before return statement
            new_code = old_code.replace(
                'return [{',
                '''// DETECT COMMON SCAFFOLDING CONCEPTUAL ANSWERS
// If scaffolding is active and student gives operation/concept keyword,
// override classification to scaffold_progress (prevents misclassification)
let finalCategory = classification.category;
let overrideReason = null;

if (context.is_scaffolding_active && !classification.is_main_problem_attempt) {
  const msg = context.student_message.toLowerCase().trim();

  // Operation keywords (answering "are we adding or subtracting?")
  const operationKeywords = [
    'adding', 'add', 'subtracting', 'subtract', 'multiplying', 'multiply',
    'dividing', 'divide', 'plus', 'minus', 'times'
  ];

  // Direction keywords (answering "left or right?")
  const directionKeywords = [
    'left', 'right', 'up', 'down', 'forward', 'backward'
  ];

  // Position keywords (answering "where are we?")
  const positionKeywords = [
    'positive', 'negative', 'zero', 'above zero', 'below zero'
  ];

  // Concept keywords (answering "what does it mean?")
  const conceptKeywords = [
    'bigger', 'smaller', 'more', 'less', 'greater', 'fewer'
  ];

  // Check if message contains ANY of these keywords
  const allKeywords = [...operationKeywords, ...directionKeywords, ...positionKeywords, ...conceptKeywords];
  const containsKeyword = allKeywords.some(kw => {
    // Match standalone word or as part of phrase like "we are adding"
    return msg.includes(kw) || msg.includes('we are ' + kw) || msg.includes('we\\'re ' + kw);
  });

  if (containsKeyword) {
    finalCategory = 'scaffold_progress';
    overrideReason = 'Detected scaffolding conceptual answer with keyword match';
  }
}

return [{'''
            )

            # Update the category field to use finalCategory
            new_code = new_code.replace(
                '    category: classification.category,',
                '''    category: finalCategory,
    _original_category: classification.category,
    _override_reason: overrideReason,'''
            )

            node['parameters']['jsCode'] = new_code

            print("✓ Updated Build Response Context node")
            print("  - Added scaffolding conceptual answer detection")
            print("  - Detects: operations (adding/subtracting), directions (left/right), positions, concepts")
            print("  - Overrides classification to 'scaffold_progress' when scaffolding active")
            return True

    print("✗ ERROR: Could not find Build Response Context node")
    return False


def main():
    input_file = 'workflow-production-ready.json'
    output_file = 'workflow-production-ready.json'

    print(f"Reading workflow from {input_file}...")
    with open(input_file, 'r') as f:
        workflow = json.load(f)

    print("Adding scaffolding answer detection...")
    success = add_scaffolding_answer_detection(workflow)

    if success:
        print(f"\nWriting updated workflow to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        print("✓ Done!")
        print("\nFix Summary:")
        print("  - Scaffolding conceptual answers now detected by pattern matching")
        print("  - Keywords: adding, subtracting, left, right, positive, negative, etc.")
        print("  - When detected, automatically classified as 'scaffold_progress'")
        print("  - Fixes Bug #12: 'we are adding' now recognized correctly")
    else:
        print("\n✗ Fix failed - workflow not modified")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
