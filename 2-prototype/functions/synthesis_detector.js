/**
 * Synthesis Detector - Determines if scaffolding should synthesize or continue
 *
 * PURPOSE: Prevent loops by detecting when student has answered enough sub-questions
 * to warrant synthesis (combining answers into final solution).
 *
 * INPUT:
 *   - current_problem: {text, correct_answer}
 *   - message: Student's latest scaffolding response (already validated as correct)
 *   - chat_history: Recent conversation turns
 *
 * OUTPUT (JSON):
 *   {
 *     action: "synthesize" | "continue",
 *     reason: "explanation of decision",
 *     sub_answers: ["3", "5"],  // collected sub-answers
 *     synthesis_hint: "You moved 3 steps then 5 more. Where are you now?"
 *   }
 */

// n8n code node format
const problem = $json.current_problem.text;
const correctAnswer = $json.current_problem.correct_answer;
const studentMessage = $json.message;
const chatHistory = $json.chat_history || '';

// Build prompt for synthesis detection
const prompt = `You are a scaffolding progress analyzer for a math tutor.

CONTEXT:
Main Problem: ${problem}
Correct Answer: ${correctAnswer}
Student's Latest Response: "${studentMessage}" (validated as correct scaffolding answer)

Recent Conversation:
${chatHistory}

---

YOUR TASK: Decide if it's time to SYNTHESIZE (combine sub-answers) or CONTINUE SCAFFOLDING.

SYNTHESIS CRITERIA:
✓ Student has answered 2+ related sub-questions correctly
✓ Sub-answers can be combined to reach final answer
✓ Tutor is repeating questions (same semantic meaning, different wording)
✓ Student gave same answer twice (indicates loop)

CONTINUE CRITERIA:
✓ Only 1 sub-answer collected so far
✓ Current sub-answer doesn't connect to previous ones
✓ More intermediate steps needed before synthesis

---

ANALYSIS STEPS:

1. EXTRACT SUB-ANSWERS from chat history:
   - Look for student responses that were acknowledged as correct
   - Identify what each sub-answer represents (e.g., "3 steps", "common denominator 4")

2. CHECK FOR LOOPS:
   - Did tutor ask essentially the same question twice?
   - Did student give the same answer twice?
   - Example: "How many steps from 0 to 5?" then "Count steps to 5" = SAME QUESTION

3. EVALUATE READINESS:
   - Can sub-answers be combined to reach the final answer?
   - Example: Sub-answers "3" and "5" for problem "-3 + 5" → YES, synthesize
   - Example: Only one sub-answer → NO, continue

4. GENERATE SYNTHESIS HINT (if synthesizing):
   - Number line: "You moved X steps then Y more. Where are you now?"
   - Fractions: "You have X/Y + Z/Y. What's the numerator?"
   - Word problem: "A has X, gets Y. What's the total?"

---

OUTPUT FORMAT (valid JSON only):

{
  "action": "synthesize" OR "continue",
  "reason": "brief explanation of decision",
  "sub_answers": ["array", "of", "collected", "sub", "answers"],
  "synthesis_hint": "specific question to ask (only if action=synthesize, else empty string)"
}

EXAMPLES:

Example 1 - SYNTHESIZE:
Problem: "-3 + 5 = ?"
Sub-answers: ["3 steps from -3 to 0", "5 steps from 0 to 5"]
Output: {
  "action": "synthesize",
  "reason": "Student answered both sub-questions (3 and 5), ready to combine for final position",
  "sub_answers": ["3", "5"],
  "synthesis_hint": "You moved 3 steps right to get to 0, then 5 more steps right. Where do you end up?"
}

Example 2 - CONTINUE:
Problem: "1/4 + 1/2 = ?"
Sub-answers: ["4" (common denominator)]
Output: {
  "action": "continue",
  "reason": "Only one sub-answer (common denominator), still need to convert fractions",
  "sub_answers": ["4"],
  "synthesis_hint": ""
}

Example 3 - SYNTHESIZE (loop detected):
Problem: "-3 + 5 = ?"
Last tutor question: "How many steps from 0 to 5?"
Student answer: "5"
Previous occurrence: Tutor asked "Count steps to 5" and student said "5 steps"
Output: {
  "action": "synthesize",
  "reason": "Loop detected - tutor asking same question with different wording, student already answered",
  "sub_answers": ["3", "5"],
  "synthesis_hint": "Great! You found 3 steps and 5 steps. Now put them together - where do you land?"
}

---

NOW ANALYZE THE CONTEXT ABOVE AND OUTPUT VALID JSON:`;

// Return the prompt for the LLM call
return {
  json: {
    prompt: prompt,
    current_problem: $json.current_problem,
    message: studentMessage,
    chat_history: chatHistory
  }
};
