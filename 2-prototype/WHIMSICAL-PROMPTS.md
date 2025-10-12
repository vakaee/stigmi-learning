# Whimsical AI Prompts for Stigmi Workflow Diagrams

Copy-paste these prompts into Whimsical AI to recreate each workflow diagram. Each prompt is designed to match the ASCII diagrams exactly.

---

## 1. Main Architecture Overview (Complete End-to-End Flow)

```
Create a vertical flowchart with rounded rectangle nodes and directional arrows.

Start at the top with a wide box labeled "WEBHOOK / CHAT TRIGGER" with subtitle "Input: {student_id, session_id, message, current_problem: {id, text, ans}}".

Below that, connect vertically to:
- "Normalize Input" with subtitle "(Chat/Webhook adapter)"
- "Redis: Get Session" with subtitle "(Load or initialize)"
- "Load Session" with subtitle "(Merge + validate)"
- "Prepare Agent Context" with subtitle "(Detect scaffolding)"

From "Prepare Agent Context", create TWO parallel branches:

LEFT BRANCH (Non-Scaffolding):
- "LLM: Extract Intent" with subtitle "(Answer vs Question)"
- "Code: Verify Answer" with subtitle "(20% threshold logic)"
- "Parse Classification" with subtitle "(Merge LLM + code)"

RIGHT BRANCH (Scaffolding):
- "Is Scaffolding Active?" (diamond decision node)
- Arrow labeled "YES (scaffolding)" to "AI Agent" with subtitle "(Tool-based validation)" and sub-bullets:
  * "Tools:"
  * "- Verify Main Answer"
  * "- Validate Scaffolding"
  * "Context: $json (workflow)"
- "Parse Agent Output" with subtitle "(Strategy 0-5 extraction)"

Both branches merge into:
- "Build Response Context" with subtitle "(Format chat history)"
- "Route by Category" with subtitle "(6-way switch node)"

From "Route by Category", create 7 horizontal branches leading to:
- "Correct (Teach Back)"
- "Close (Probe)"
- "Wrong Operation (Clarify)"
- "Conceptual (Teach)"
- "Stuck (Scaffold)"
- "Off-Topic (Redirect)"
- "Scaffold Progress"

All 7 branches merge back to:
- "Update Session & Format" with subtitle "(State transitions)"
- "Redis: Save Session"
- "Webhook Response" with subtitle "{output, _debug, ...}"

Color scheme:
- Entry/exit nodes: Blue
- Processing nodes: Gray
- LLM nodes: Green
- Decision nodes: Yellow
- Response nodes: Purple
- Storage nodes: Orange
```

---

## 2. Non-Scaffolding Classification Path

```
Create a vertical flowchart showing the non-scaffolding classification pipeline.

Top node: "Prepare Agent Context" (gray rounded rectangle)

Arrow down labeled "Non-Scaffolding Path" to:

"LLM: Extract Intent & Value" (green rounded rectangle)
- Subtitle: "GPT-4o-mini"
- Sub-bullets:
  * "Determines: is_answer vs question"
  * "Extracts numeric value"
  * "CRITICAL: Extract what student SAID, not MEANT"

Arrow down to:

"Code: Verify Answer" (blue rounded rectangle)
- Subtitle: "20% Threshold Logic"
- Formula box below:
  * "diff = |student - correct|"
  * "threshold = max(0.3, |correct * 0.2|)"
  * "if diff < 0.001: 'correct'"
  * "elif diff <= threshold: 'close'"
  * "else: 'wrong_operation'"

Arrow down to:

"Parse Classification" (gray rounded rectangle)
- Subtitle: "Merge LLM + Code Results"
- Output: "{category, is_main_problem_attempt, confidence, reasoning}"

Arrow down to:

"Format for Routing" (gray rounded rectangle)

Arrow down to:

"Build Response Context" (gray rounded rectangle)

Color scheme:
- Processing: Gray
- LLM: Green
- Verification: Blue
```

---

## 3. Scaffolding Classification Path

```
Create a vertical flowchart showing the scaffolding path with AI Agent and tools.

Top node: "Prepare Agent Context" (gray rounded rectangle)

Arrow down to:

"Is Scaffolding Active?" (yellow diamond decision node)

Arrow labeled "YES" pointing right to:

"AI Agent" (large green rounded rectangle)
- Subtitle: "GPT-4o-mini with Tools"
- Left side connected boxes (tools):
  * "Tool: Verify Main Answer" (small blue box)
    - Reads from: $json.student_message
    - Returns: "correct" | "close" | "wrong_operation"
  * "Tool: Validate Scaffolding" (small blue box)
    - Reads from: $json.scaffolding_last_question
    - Returns: validation guidelines for agent
- Right side connected box:
  * "Window Buffer Memory" (small orange box)
    - "Last 15 turns per problem"

Main AI Agent box contains:
- "STEP 1: Detect Intent"
  * "Main problem attempt?"
  * "Scaffolding response?"
- "STEP 2: Call Appropriate Tool"
- "Returns: {category, is_main_problem_attempt, confidence, reasoning}"

Arrow down from AI Agent to:

"Parse Agent Output" (purple rounded rectangle)
- Subtitle: "Multi-Strategy Extraction"
- Bullet points:
  * "Strategy 0: Unwrap __structured__output"
  * "Strategy 1: Direct object fields"
  * "Strategy 2-5: Fallback patterns"

Arrow down to:

"Build Response Context" (gray rounded rectangle)

Add note box to the right:
"CRITICAL: Tools read from workflow context ($json), NOT OpenAI function parameters"

Color scheme:
- Decision: Yellow
- AI Agent: Green
- Tools: Blue
- Parsing: Purple
- Context: Gray
- Memory: Orange
```

---

## 4. Response Routing (7-Way Switch)

```
Create a flowchart showing the routing logic from classification to response generation.

Top node: "Build Response Context" (gray rounded rectangle)

Arrow down to:

"Route by Category" (large yellow hexagon)
- Subtitle: "7-way switch based on category field"

From the hexagon, create 7 arrows pointing down and slightly spread out horizontally to:

Row 1 (left to right):
1. "Response: Correct" (purple rounded rectangle)
   - Subtitle: "TEACH-BACK"
   - "Celebrate + ask for explanation"

2. "Response: Close" (purple rounded rectangle)
   - Subtitle: "PROBE"
   - "Gentle questions, escalate on attempt 3+"

3. "Response: Wrong Operation" (purple rounded rectangle)
   - Subtitle: "CLARIFY"
   - "Address misconception, teach on attempt 3+"

Row 2 (left to right):
4. "Response: Conceptual" (purple rounded rectangle)
   - Subtitle: "CONCEPT"
   - "Teach with examples, end with check question"

5. "Response: Stuck" (purple rounded rectangle)
   - Subtitle: "SCAFFOLD"
   - "Break into tiny steps, more help on attempt 3+"

6. "Response: Off-Topic" (purple rounded rectangle)
   - Subtitle: "REDIRECT"
   - "Politely refocus on problem"

7. "Response: Scaffold Progress" (purple rounded rectangle)
   - Subtitle: "ACKNOWLEDGE"
   - "Praise + ask next scaffolding step"

All 7 arrows converge back down to:

"Update Session & Format Response" (gray rounded rectangle)

Color scheme:
- Routing: Yellow
- Response nodes: Purple
- Processing: Gray
```

---

## 5. Correct Response Flow (Teach-Back)

```
Create a detailed flowchart showing the "correct" response path and teach-back initiation.

Top node: "Route by Category" (yellow hexagon)

Arrow labeled "category = 'correct'" down to:

"Response: Correct" (large purple rounded rectangle)
- Subtitle: "GPT-4o-mini - Teach-Back Method"
- Contains decision tree:

  Branching logic:
  "Is scaffolding_active?"

  YES branch:
  - "Celebrate scaffolding success"
  - "Ask: How did you put pieces together?"
  - "Reference scaffolding steps from chat history"

  NO branch:
  - "Check: attempt_count = 1?"
    * YES: "First try! Ask to walk through thinking"
    * NO: "Worked through it! Ask how they figured it out"

Prompt template box on right:
"Template Variables:"
- $json.current_problem.text
- $json.message (student's answer)
- $json.is_scaffolding_active
- $json.attempt_count
- $json.chat_history

Output format:
"1-2 sentences: Brief celebration + explanation request"

Arrow down to:

"Update Session & Format Response" (gray rounded rectangle)
- State transition box:
  * "teach_back.active = true"
  * "teach_back.awaiting_explanation = true"
  * "If was scaffolding: scaffolding.active = false"

Arrow down to:

"Save to Redis" (orange rounded rectangle)

Color scheme:
- Routing: Yellow
- Response: Purple
- State management: Gray
- Storage: Orange
```

---

## 6. Close Response Flow (Gentle Probe with Escalation)

```
Create a flowchart showing the "close" response path with attempt-based escalation.

Top node: "Route by Category" (yellow hexagon)

Arrow labeled "category = 'close'" down to:

"Response: Close" (large purple rounded rectangle)
- Subtitle: "GPT-4o-mini - Socratic Probing"
- Contains escalation logic:

  "Attempt-Based Strategy:"

  Three parallel paths based on attempt_count:

  Path 1 (attempt = 1):
  Box: "GENTLE PROBE"
  - "Point to what's close about their answer"
  - "Ask probing question to help spot small error"
  - "Example: 'You're very close! What about the sign?'"

  Path 2 (attempt = 2):
  Box: "EXPLICIT HINT"
  - "Give more direct hint about where error is"
  - "Example: 'Think about whether we're adding or subtracting'"

  Path 3 (attempt >= 3):
  Box: "TEACH + FINISH"
  - "Walk through one step explicitly"
  - "Then let them finish"
  - "Example: 'Let's start at -3. Now add 5...'"

Prompt constraints box on right:
"Rules:"
- "1-2 sentences maximum"
- "Ask, don't tell (unless attempt 3+)"
- "Use ONLY the numbers from original problem"
- "DO NOT give final answer"

Arrow down to:

"Update Session & Format Response" (gray rounded rectangle)
- "No state transitions for 'close'"
- "attempt_count incremented"

Arrow down to:

"Save to Redis" (orange rounded rectangle)

Color scheme:
- Routing: Yellow
- Response: Purple
- Escalation paths: Light purple with borders
- State management: Gray
- Storage: Orange
```

---

## 7. Wrong Operation Flow (Misconception Clarification)

```
Create a flowchart showing the "wrong_operation" response path with misconception handling.

Top node: "Route by Category" (yellow hexagon)

Arrow labeled "category = 'wrong_operation'" down to:

"Response: Wrong Operation" (large purple rounded rectangle)
- Subtitle: "GPT-4o-mini - Address Misconception"
- Contains escalation logic:

  "Attempt-Based Strategy:"

  Three parallel paths:

  Path 1 (attempt = 1):
  Box: "CLARIFYING QUESTION"
  - "Ask about the operation or concept"
  - "Example: 'When we add a positive number to a negative, which direction do we move?'"

  Path 2 (attempt = 2):
  Box: "DIRECT HINT"
  - "Give more explicit hint about operation"
  - "Example: 'Adding means moving to the right on the number line'"

  Path 3 (attempt >= 3):
  Box: "TEACH CONCEPT"
  - "Teach concept directly with example"
  - "Use SAME numbers from original problem"
  - "Then ask them to try"
  - "Example: 'Start at -3. Adding 5 means moving 5 steps right...'"

Critical rules box on right:
"GROUNDING RULES:"
- "Use EXACT numbers from problem"
- "Do NOT create easier examples"
- "Explain THIS operation with THESE numbers"
- "Real-world examples must use same numbers"
- "Check chat history to avoid repeating"

Arrow down to:

"Update Session & Format Response" (gray rounded rectangle)
- "No state transitions for 'wrong_operation'"
- "attempt_count incremented"

Arrow down to:

"Save to Redis" (orange rounded rectangle)

Color scheme:
- Routing: Yellow
- Response: Purple
- Teaching paths: Light purple with borders
- State management: Gray
- Storage: Orange
```

---

## 8. Stuck/Scaffolding Initiation Flow

```
Create a flowchart showing the "stuck" response path and scaffolding initiation.

Top node: "Route by Category" (yellow hexagon)

Arrow labeled "category = 'stuck'" down to:

Decision diamond: "Is scaffolding already active?"

Two branches:

LEFT BRANCH (scaffolding NOT active):
"Response: Stuck - INITIATE SCAFFOLDING" (large purple rounded rectangle)
- Subtitle: "Break Problem into Smaller Steps"
- Contains:

  "Attempt-Based Scaffolding Depth:"

  Attempt 1:
  - "Start with very first step"
  - "Example: 'What does -3 mean on a number line?'"

  Attempt 2:
  - "Give first step, ask for second"
  - "Example: 'We start at -3. What happens when we add?'"

  Attempt 3+:
  - "Walk through most steps, leave only final step"
  - "Example: 'We start at -3, move right 5 steps, where do we land?'"

State transition box:
"scaffolding.active = true"
"scaffolding.depth = 1"
"scaffolding.last_question = response"

RIGHT BRANCH (scaffolding IS active):
"Response: Stuck - CONTINUE SCAFFOLDING" (large purple rounded rectangle)
- Subtitle: "Student Didn't Get Scaffolding Question"
- Contains:

  "Scaffolding Repair Strategies:"

  Option 1:
  - "Re-phrase same scaffolding question more simply"

  Option 2:
  - "Break into even smaller sub-question"
  - "Make more concrete"

State transition box:
"scaffolding.active = true (stays active)"
"scaffolding.last_question = response (updated)"
"scaffolding.depth unchanged"

Critical rules box spanning both branches:
"GROUNDING RULES:"
- "Break down THIS problem with THESE numbers"
- "Do NOT create simpler problem"
- "Each step must use actual problem numbers"
- "Check chat history for already-asked steps"

Both branches merge to:

"Update Session & Format Response" (gray rounded rectangle)

Arrow down to:

"Save to Redis" (orange rounded rectangle)

Special note on right:
"Scaffolding Progress:" (small box)
"If student answers scaffolding correctly → category = 'scaffold_progress'"
"Routes to separate response node that acknowledges + asks next step"

Color scheme:
- Routing: Yellow
- Decision: Yellow diamond
- Response: Purple
- State transitions: Light gray boxes
- State management: Gray
- Storage: Orange
```

---

## Styling Guidelines for All Diagrams

**General Layout:**
- Vertical flow (top to bottom) for main paths
- Horizontal expansion only for parallel branches or multiple outputs
- Consistent node spacing (use Whimsical's "Distribute vertically" feature)

**Node Shapes:**
- Rectangles with rounded corners: Processing nodes, response nodes
- Diamonds: Decision nodes
- Hexagons: Routing/switch nodes
- Rectangles (sharp corners): Data/state boxes

**Color Palette:**
- Blue (#4A90E2): Entry points, verification nodes
- Green (#7ED321): LLM nodes, AI Agent
- Yellow (#F5A623): Decision nodes, routing
- Purple (#BD10E0): Response generation nodes
- Orange (#FF6B6B): Storage nodes (Redis)
- Gray (#9B9B9B): Standard processing nodes
- Light variations: Sub-components, state boxes

**Text Formatting:**
- Node titles: Bold, 14-16pt
- Subtitles: Italic, 11pt, gray
- Bullet points: 10pt
- Arrow labels: 9pt, italic

**Arrow Style:**
- Solid arrows: Primary flow
- Dashed arrows: Optional/conditional flow
- Label critical decision paths ("YES", "NO", condition values)

**Boxes and Annotations:**
- Use dotted border rectangles for notes/annotations
- Use solid border rectangles for state transition details
- Position notes to the right of main flow when possible

---

## Tips for Whimsical AI

1. **Start simple**: Paste the prompt, let Whimsical generate, then refine
2. **Iterate**: After generation, use natural language to adjust:
   - "Move node X to the right of Y"
   - "Make the AI Agent box larger"
   - "Connect Tool boxes to AI Agent with dashed lines"
3. **Use frames**: Group related sections (e.g., "Non-Scaffolding Path frame")
4. **Export**: Export as PNG at 2x resolution for documentation

---

**Created**: October 12, 2025
**Purpose**: Exact recreation of ASCII workflow diagrams in Whimsical
**Maintained By**: AI Development Team
