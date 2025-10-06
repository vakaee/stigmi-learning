/**
 * classify_answer_quality.js
 *
 * Stage 2a Triage: Answer Quality Classification
 * Rule-based classification after verification
 *
 * For use in n8n Function nodes
 */

/**
 * Classify answer quality based on verification result
 * This is Stage 2a triage - only called when student gave an answer
 *
 * @param {object} verificationResult - Result from verify_answer.js
 * @param {string} studentInput - Original student input (for pattern detection)
 * @param {string} correctAnswer - Expected answer
 * @returns {object} Classification result
 */
function classifyAnswerQuality(verificationResult, studentInput, correctAnswer) {
  // If verification succeeded and answer is correct
  if (verificationResult.correct) {
    return {
      category: "correct",
      confidence: 0.99,
      reasoning: "Answer matches expected value"
    };
  }

  // If answer is close (within 20% of correct answer)
  if (verificationResult.close) {
    return {
      category: "close",
      confidence: 0.95,
      reasoning: "Answer is within 20% of correct value (likely calculation error)"
    };
  }

  // All other wrong answers → wrong_operation
  // (Could add more sophisticated pattern detection here)
  return {
    category: "wrong_operation",
    confidence: 0.85,
    reasoning: "Answer is significantly wrong (conceptual error or wrong operation)"
  };
}

/**
 * Detect common operation errors (optional enhancement)
 * This can be used to improve classification confidence
 *
 * @param {string} studentInput - Student's answer
 * @param {string} problem - The problem text
 * @param {string} correctAnswer - Expected answer
 * @returns {object|null} Detected pattern or null
 */
function detectOperationError(studentInput, problem, correctAnswer) {
  // Example heuristics (can be expanded)

  // Pattern: Problem has + but student answer suggests they subtracted
  // e.g., "-3 + 5" → student answered "-8" (did -3 - 5)
  if (problem.includes('+') && studentInput.includes('-')) {
    const match = problem.match(/-?\\d+\\s*\\+\\s*-?\\d+/);
    if (match) {
      // Could verify this more precisely
      return {
        detected: true,
        pattern: "addition_as_subtraction",
        hint: "Check the operation sign - is it + or -?"
      };
    }
  }

  // Pattern: Ignored negative sign
  // e.g., problem "-3 + 5" but student treated as "3 + 5 = 8"
  const studentNum = parseFloat(studentInput);
  const correctNum = parseFloat(correctAnswer);
  if (!isNaN(studentNum) && !isNaN(correctNum)) {
    if (Math.abs(studentNum) === Math.abs(correctNum) && studentNum !== correctNum) {
      return {
        detected: true,
        pattern: "sign_error",
        hint: "Check the sign (+ or -) of your answer"
      };
    }
  }

  return null;
}

/**
 * Get category-specific metadata
 * Provides additional context for response generation
 *
 * @param {string} category - Classification category
 * @param {object} verificationResult - Verification result
 * @returns {object} Metadata for this category
 */
function getCategoryMetadata(category, verificationResult) {
  const metadata = {
    category: category,
    verification: verificationResult
  };

  switch (category) {
    case "correct":
      metadata.next_action = "teach_back";
      metadata.tone = "celebrating";
      break;

    case "close":
      metadata.next_action = "probe";
      metadata.tone = "encouraging";
      metadata.error_magnitude = "small";
      break;

    case "wrong_operation":
      metadata.next_action = "clarify";
      metadata.tone = "patient";
      metadata.error_magnitude = "significant";
      break;
  }

  return metadata;
}

/**
 * n8n Function Node usage:
 *
 * // Get verification result from previous node
 * const verification = $('Verify Answer').first().json;
 * const studentInput = $input.item.json.message;
 * const correctAnswer = $input.item.json.current_problem.correct_answer;
 *
 * // Classify answer quality
 * const classification = classifyAnswerQuality(
 *   verification,
 *   studentInput,
 *   correctAnswer
 * );
 *
 * // Optional: detect specific error patterns
 * const errorPattern = detectOperationError(
 *   studentInput,
 *   $input.item.json.current_problem.text,
 *   correctAnswer
 * );
 *
 * // Get metadata
 * const metadata = getCategoryMetadata(classification.category, verification);
 *
 * return {
 *   json: {
 *     category: classification.category,
 *     confidence: classification.confidence,
 *     reasoning: classification.reasoning,
 *     error_pattern: errorPattern,
 *     metadata: metadata
 *   }
 * };
 */

// For Node.js module export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    classifyAnswerQuality,
    detectOperationError,
    getCategoryMetadata
  };
}
