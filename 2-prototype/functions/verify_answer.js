/**
 * verify_answer.js
 *
 * Answer verification function with edge case handling
 * Handles: decimals, fractions, expressions, written numbers, negatives
 *
 * For use in n8n Function nodes or standalone Node.js
 */

// Note: In n8n, math.js is available as 'math'
// For standalone use: const math = require('mathjs');

/**
 * Verify if student's answer matches the correct answer
 *
 * @param {string} studentInput - Raw student input
 * @param {string} correctAnswer - Expected answer (as string)
 * @returns {object} Verification result with correct/close flags
 */
function verifyAnswer(studentInput, correctAnswer) {
  try {
    // Normalize input
    let cleaned = studentInput.trim().toLowerCase();

    // Handle written numbers (basic cases)
    const numberWords = {
      'zero': '0',
      'one': '1',
      'two': '2',
      'three': '3',
      'four': '4',
      'five': '5',
      'six': '6',
      'seven': '7',
      'eight': '8',
      'nine': '9',
      'ten': '10',
      'negative': '-',
      'minus': '-'
    };

    // Replace written numbers with digits
    for (let [word, digit] of Object.entries(numberWords)) {
      const regex = new RegExp('\\b' + word + '\\b', 'g');
      cleaned = cleaned.replace(regex, digit);
    }

    // Remove extra spaces
    cleaned = cleaned.replace(/\s+/g, '');

    // Evaluate both as mathematical expressions
    const studentVal = math.evaluate(cleaned);
    const correctVal = math.evaluate(correctAnswer);

    // Handle fractions: convert to decimals for comparison
    const studentNum = convertToNumber(studentVal);
    const correctNum = convertToNumber(correctVal);

    // Calculate difference
    const diff = Math.abs(studentNum - correctNum);
    const tolerance = 0.001;  // For floating point comparison
    const closeThreshold = Math.abs(correctNum * 0.2);  // 20% of correct answer

    return {
      correct: diff < tolerance,
      close: diff >= tolerance && diff < closeThreshold,
      student_value: studentNum,
      correct_value: correctNum,
      difference: diff,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    // Could not parse as number/expression
    return {
      correct: false,
      close: false,
      error: "Could not parse as number or expression",
      error_message: error.message,
      raw_input: studentInput,
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * Convert math.js types to plain numbers
 * Handles fractions, complex numbers, etc.
 *
 * @param {*} value - Value from math.evaluate()
 * @returns {number} Plain JavaScript number
 */
function convertToNumber(value) {
  // If it's a fraction object from math.js
  if (typeof value === 'object' && value.n !== undefined && value.d !== undefined) {
    return value.n / value.d;
  }

  // If it's already a number
  if (typeof value === 'number') {
    return value;
  }

  // Try to convert to number
  return Number(value);
}

/**
 * n8n Function Node usage:
 *
 * const studentInput = $input.item.json.message;
 * const correctAnswer = $input.item.json.current_problem.correct_answer;
 *
 * const result = verifyAnswer(studentInput, correctAnswer);
 *
 * return {
 *   json: {
 *     ...result,
 *     student_input: studentInput,
 *     correct_answer: correctAnswer
 *   }
 * };
 */

// For Node.js module export (not used in n8n)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { verifyAnswer, convertToNumber };
}
