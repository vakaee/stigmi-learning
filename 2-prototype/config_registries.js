/**
 * Configuration Registries for Extensible Tutor Architecture
 *
 * This file contains all configurable patterns, validators, and error detectors.
 * To add new subjects or problem types, add entries to these registries WITHOUT modifying core workflow logic.
 */

// ============================================================================
// ERROR DETECTOR REGISTRY
// ============================================================================
// Used by Enhanced Numeric Verifier to detect plausible operation errors

const ERROR_DETECTORS = {
  /**
   * Math: Addition
   * Common errors: forgot negatives, subtracted instead, absolute values
   */
  'math_arithmetic_addition': (num1, num2, operation) => {
    return [
      Math.abs(num1) + Math.abs(num2),      // Forgot negatives: |-3| + |5| = 8
      num1 - num2,                           // Subtracted instead: -3 - 5 = -8
      Math.abs(num1 - num2),                 // Absolute value of subtract: |-3 - 5| = 8
      -(num1 + num2)                         // Wrong sign: -(-3 + 5) = -2
    ];
  },

  /**
   * Math: Subtraction
   * Common errors: added instead, forgot negatives, wrong order
   */
  'math_arithmetic_subtraction': (num1, num2, operation) => {
    return [
      num1 + num2,                           // Added instead: -3 + 5 = 2
      Math.abs(num1) + Math.abs(num2),      // Added absolutes: |-3| + |5| = 8
      num2 - num1,                           // Reversed order: 5 - (-3) = 8
      Math.abs(num1 - num2)                 // Absolute value: |-3 - 5| = 8
    ];
  },

  /**
   * Math: Multiplication
   * Common errors: added instead, forgot negatives, wrong sign rules
   */
  'math_arithmetic_multiplication': (num1, num2, operation) => {
    return [
      num1 + num2,                           // Added instead: -3 + 5 = 2
      Math.abs(num1 * num2),                // Forgot negative sign: |-3 * 5| = 15
      -(num1 * num2)                         // Wrong sign: -(-3 * 5) = -15
    ];
  },

  /**
   * Math: Division
   * Common errors: multiplied instead, inverted, wrong sign
   */
  'math_arithmetic_division': (num1, num2, operation) => {
    if (num2 === 0) return []; // Avoid division by zero
    return [
      num1 * num2,                           // Multiplied instead: -3 * 5 = -15
      num2 / num1,                           // Inverted: 5 / -3 = -1.67
      Math.abs(num1 / num2),                // Forgot sign: |-3 / 5| = 0.6
      -(num1 / num2)                         // Wrong sign: -(-3 / 5) = 0.6
    ];
  }

  // FUTURE: Add detectors for other subjects
  // 'chemistry_ph_calculation': (h_concentration) => [...],
  // 'physics_force_calculation': (mass, acceleration) => [...],
  // etc.
};

// ============================================================================
// SEMANTIC PATTERN REGISTRY
// ============================================================================
// Used by Semantic Validator to match student responses to expected answers

const SEMANTIC_PATTERNS = {
  /**
   * Math: Operation identification (addition vs subtraction)
   */
  'math_operation_identification': {
    patterns: [
      {
        // Pattern: "When we see +, are we adding or subtracting?"
        questionPatterns: ['adding or subtracting', 'add or subtract'],
        expectedKeywords: {
          '+': ['adding', 'add', 'plus', 'addition', 'sum'],
          '-': ['subtracting', 'subtract', 'minus', 'subtraction', 'difference']
        },
        wrongKeywords: {
          '+': ['subtracting', 'subtract', 'minus', 'subtraction'],
          '-': ['adding', 'add', 'plus', 'addition']
        }
      }
    ]
  },

  /**
   * Math: Direction on number line
   */
  'math_direction_identification': {
    patterns: [
      {
        // Pattern: "Which direction do we move for +5?"
        questionPatterns: ['direction', 'which way', 'right or left'],
        expectedKeywords: {
          'positive': ['right', 'to the right', 'rightward', 'forward'],
          'negative': ['left', 'to the left', 'leftward', 'backward']
        },
        wrongKeywords: {
          'positive': ['left', 'to the left', 'leftward'],
          'negative': ['right', 'to the right', 'rightward']
        }
      }
    ]
  },

  /**
   * Math: Negative number understanding
   */
  'math_negative_number_concept': {
    patterns: [
      {
        // Pattern: "What does -3 mean?"
        questionPatterns: ['what does -', 'what is -', 'negative number'],
        expectedKeywords: ['negative', 'less than zero', 'below zero', 'left of zero'],
        wrongKeywords: ['positive', 'greater than zero', 'above zero']
      }
    ]
  }

  // FUTURE: Add patterns for other subjects
  // 'history_time_period': {
  //   patterns: [...]
  // },
  // 'science_classification': {
  //   patterns: [...]
  // }
};

// ============================================================================
// SUBJECT CONFIGURATION
// ============================================================================
// Maps problem types to appropriate validators and configurations

const SUBJECT_CONFIG = {
  'math_arithmetic': {
    validator: 'numeric',
    errorDetector: (problemText) => {
      // Parse operation from problem text
      const match = problemText.match(/([\-\d]+)\s*([+\-*/])\s*([\-\d]+)/);
      if (!match) return null;

      const operation = match[2];
      const operationMap = {
        '+': 'math_arithmetic_addition',
        '-': 'math_arithmetic_subtraction',
        '*': 'math_arithmetic_multiplication',
        '/': 'math_arithmetic_division'
      };

      return operationMap[operation];
    },
    featureExtractor: {
      keywords: ['adding', 'subtracting', 'multiplying', 'dividing', 'plus', 'minus', 'times', 'divided by'],
      directions: ['right', 'left', 'up', 'down'],
      concepts: ['negative', 'positive', 'zero', 'number line']
    }
  }

  // FUTURE: Add configurations for other subjects
  // 'history_dates': {
  //   validator: 'date',
  //   featureExtractor: {
  //     keywords: ['before', 'after', 'during', 'century'],
  //     entities: ['events', 'people', 'places']
  //   }
  // }
};

// ============================================================================
// AGE GROUP TEMPLATES
// ============================================================================
// Response template customizations by age group

const AGE_GROUP_CONFIG = {
  'grades_3-5': {
    label: 'grades 3-5 (ages 8-10)',
    vocabulary: 'simple',
    sentenceLength: '5-12 words',
    scaffoldingDepth: 'high',
    examples: 'concrete'
  },
  'grades_6-8': {
    label: 'grades 6-8 (ages 11-13)',
    vocabulary: 'moderate',
    sentenceLength: '10-15 words',
    scaffoldingDepth: 'medium',
    examples: 'concrete with some abstraction'
  },
  'grades_9-12': {
    label: 'grades 9-12 (ages 14-18)',
    vocabulary: 'advanced',
    sentenceLength: '12-20 words',
    scaffoldingDepth: 'low',
    examples: 'abstract'
  }
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get error detector function for a problem
 */
function getErrorDetector(problemType, problemText) {
  const config = SUBJECT_CONFIG[problemType];
  if (!config || !config.errorDetector) {
    return null;
  }

  const detectorKey = config.errorDetector(problemText);
  return ERROR_DETECTORS[detectorKey] || null;
}

/**
 * Get semantic patterns for a problem type
 */
function getSemanticPatterns(problemType) {
  // For now, all math problems use the same patterns
  // In future, could be more specific based on problem type
  return SEMANTIC_PATTERNS;
}

/**
 * Get feature extraction config for a subject
 */
function getFeatureExtractionConfig(problemType) {
  const config = SUBJECT_CONFIG[problemType];
  return config ? config.featureExtractor : null;
}

/**
 * Get age group configuration
 */
function getAgeGroupConfig(ageGroup) {
  return AGE_GROUP_CONFIG[ageGroup] || AGE_GROUP_CONFIG['grades_3-5'];
}

// ============================================================================
// EXPORTS (for use in n8n Code nodes)
// ============================================================================

module.exports = {
  ERROR_DETECTORS,
  SEMANTIC_PATTERNS,
  SUBJECT_CONFIG,
  AGE_GROUP_CONFIG,
  getErrorDetector,
  getSemanticPatterns,
  getFeatureExtractionConfig,
  getAgeGroupConfig
};

// ============================================================================
// USAGE EXAMPLES
// ============================================================================

/**
 * Example 1: Enhanced Numeric Verifier
 *
 * const config = require('./config_registries.js');
 * const problemText = "What is -3 + 5?";
 * const problemType = "math_arithmetic";
 *
 * // Get error detector
 * const detector = config.getErrorDetector(problemType, problemText);
 * if (detector) {
 *   const possibleErrors = detector(-3, 5, '+');
 *   // possibleErrors = [8, -8, 8, -2]
 * }
 */

/**
 * Example 2: Semantic Validator
 *
 * const config = require('./config_registries.js');
 * const patterns = config.getSemanticPatterns('math_arithmetic');
 *
 * const opPatterns = patterns['math_operation_identification'];
 * const expected = opPatterns.patterns[0].expectedKeywords['+'];
 * // expected = ['adding', 'add', 'plus', 'addition', 'sum']
 */

/**
 * Example 3: Content Feature Extractor
 *
 * const config = require('./config_registries.js');
 * const extractConfig = config.getFeatureExtractionConfig('math_arithmetic');
 *
 * // Use extractConfig.keywords in LLM prompt
 * const prompt = `Extract these keywords: ${extractConfig.keywords.join(', ')}`;
 */

/**
 * Example 4: Age Group Templates
 *
 * const config = require('./config_registries.js');
 * const ageConfig = config.getAgeGroupConfig('grades_3-5');
 *
 * // Use ageConfig in Response: Unified
 * const prompt = `You are a math tutor for ${ageConfig.label}.
 * Use ${ageConfig.vocabulary} vocabulary with ${ageConfig.sentenceLength} sentences.`;
 */
