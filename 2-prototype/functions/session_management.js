/**
 * session_management.js
 *
 * Session state management for AI tutor
 * Handles: session creation, turn tracking, attempt counting, memory window
 *
 * For use in n8n Function nodes
 */

/**
 * Initialize a new session
 *
 * @param {string} studentId - Student identifier
 * @param {string} sessionId - Session identifier
 * @param {object} initialProblem - First problem object
 * @returns {object} New session object
 */
function initializeSession(studentId, sessionId, initialProblem) {
  const now = new Date().toISOString();

  return {
    session_id: sessionId,
    student_id: studentId,
    created_at: now,
    last_active: now,
    ttl: 1800,  // 30 minutes in seconds

    current_problem: {
      id: initialProblem.id,
      text: initialProblem.text,
      correct_answer: initialProblem.correct_answer,
      attempt_count: 0,
      started_at: now
    },

    recent_turns: [],  // Last 5 turns for LLM context

    concepts_taught: [],

    stats: {
      total_turns: 0,
      total_latency_ms: 0,
      avg_latency_ms: 0,
      problems_attempted: 1,
      problems_solved: 0
    }
  };
}

/**
 * Update session with new turn
 *
 * @param {object} session - Current session object
 * @param {object} newTurn - New turn data
 * @param {object} currentProblem - Current problem (to detect problem changes)
 * @returns {object} Updated session object
 */
function updateSession(session, newTurn, currentProblem) {
  // Check if problem changed
  if (session.current_problem.id !== currentProblem.id) {
    // New problem - reset attempt count
    session.current_problem = {
      id: currentProblem.id,
      text: currentProblem.text,
      correct_answer: currentProblem.correct_answer,
      attempt_count: 0,
      started_at: new Date().toISOString()
    };

    session.stats.problems_attempted++;
  }

  // Increment attempt count if this turn was an answer attempt
  if (newTurn.is_answer) {
    session.current_problem.attempt_count++;
  }

  // Mark problem as solved if correct
  if (newTurn.category === 'correct') {
    session.stats.problems_solved++;
  }

  // Add turn to recent history
  session.recent_turns.push({
    turn_number: session.stats.total_turns + 1,
    timestamp: new Date().toISOString(),
    ...newTurn
  });

  // Trim to last 5 turns (memory window)
  if (session.recent_turns.length > 5) {
    session.recent_turns = session.recent_turns.slice(-5);
  }

  // Update metadata
  session.last_active = new Date().toISOString();
  session.stats.total_turns++;

  // Update latency stats
  if (newTurn.latency_ms) {
    session.stats.total_latency_ms += newTurn.latency_ms;
    session.stats.avg_latency_ms = Math.round(
      session.stats.total_latency_ms / session.stats.total_turns
    );
  }

  return session;
}

/**
 * Format chat history for LLM prompt
 *
 * @param {array} recentTurns - Array of recent turn objects
 * @returns {string} Formatted chat history string
 */
function formatChatHistoryForLLM(recentTurns) {
  if (!recentTurns || recentTurns.length === 0) {
    return "";
  }

  return recentTurns.map((turn, index) => {
    return `Turn ${index + 1}:\nStudent: "${turn.student_input}"\nTutor: "${turn.tutor_response}"`;
  }).join('\n\n');
}

/**
 * Get attempt count for current problem
 *
 * @param {object} session - Session object
 * @returns {number} Attempt count
 */
function getAttemptCount(session) {
  return session.current_problem.attempt_count || 0;
}

/**
 * Determine escalation level based on attempt count
 *
 * @param {number} attemptCount - Number of attempts
 * @returns {string} Escalation level (probe, hint, teach)
 */
function getEscalationLevel(attemptCount) {
  if (attemptCount <= 1) return "probe";      // Socratic question
  if (attemptCount === 2) return "hint";      // More explicit
  return "teach";                              // Direct instruction
}

/**
 * Add concept to taught concepts list
 *
 * @param {object} session - Session object
 * @param {string} concept - Concept identifier
 * @returns {object} Updated session
 */
function addTaughtConcept(session, concept) {
  if (!session.concepts_taught.includes(concept)) {
    session.concepts_taught.push(concept);
  }
  return session;
}

/**
 * n8n Function Node usage examples:
 *
 * // Get session (from workflow static data or Redis)
 * const sessionData = $('Get Session').first().json;
 * const session = sessionData.session || null;
 *
 * // If no session, initialize
 * if (!session) {
 *   const newSession = initializeSession(
 *     $input.item.json.student_id,
 *     $input.item.json.session_id,
 *     $input.item.json.current_problem
 *   );
 *   return { json: { session: newSession } };
 * }
 *
 * // Update session with new turn
 * const newTurn = {
 *   student_input: $input.item.json.message,
 *   is_answer: $input.item.json.is_answer,
 *   category: $input.item.json.category,
 *   verification: $input.item.json.verification,
 *   tutor_response: $input.item.json.response,
 *   latency_ms: $input.item.json.latency_ms
 * };
 *
 * const updatedSession = updateSession(
 *   session,
 *   newTurn,
 *   $input.item.json.current_problem
 * );
 *
 * return { json: { session: updatedSession } };
 *
 * // Format chat history for prompt
 * const chatHistory = formatChatHistoryForLLM(session.recent_turns);
 * return { json: { chat_history: chatHistory } };
 */

// For Node.js module export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initializeSession,
    updateSession,
    formatChatHistoryForLLM,
    getAttemptCount,
    getEscalationLevel,
    addTaughtConcept
  };
}
