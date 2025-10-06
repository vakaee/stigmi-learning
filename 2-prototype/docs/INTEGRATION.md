# Integration Guide - MinS Text Module

**Audience**: MinS Development Team
**Goal**: Connect AI tutor prototype to MinS production system
**Estimated time**: 2-4 hours

---

## Table of Contents

1. [Integration Options](#integration-options)
2. [Option A: Direct Frontend Integration](#option-a-direct-frontend-integration)
3. [Option B: Backend Proxy Integration](#option-b-backend-proxy-integration)
4. [Option C: Iframe Embedding](#option-c-iframe-embedding)
5. [Testing Integration](#testing-integration)
6. [Production Checklist](#production-checklist)

---

## Integration Options

### Comparison

| Option | Complexity | Security | Latency | Recommended For |
|--------|------------|----------|---------|-----------------|
| **A: Direct Frontend** | Low | Medium | Fast | Quick prototype, MVP |
| **B: Backend Proxy** | Medium | High | Medium | Production, analytics |
| **C: Iframe** | Very Low | Medium | Fast | Isolated testing |

**Recommendation**: Start with **Option B (Backend Proxy)** for production-ready integration.

---

## Option A: Direct Frontend Integration

### Overview

MinS text module calls n8n webhook directly from browser JavaScript.

### Architecture

```
MinS Frontend (React)
    ↓ fetch()
n8n Webhook
    ↓
Tutor Response
    ↓
MinS Frontend displays
```

### Implementation

#### 1. Add Webhook Client

```javascript
// src/services/tutorService.js

const TUTOR_WEBHOOK_URL = process.env.REACT_APP_TUTOR_WEBHOOK_URL;
const TUTOR_API_KEY = process.env.REACT_APP_TUTOR_API_KEY;

export async function sendToTutor(studentMessage, currentProblem) {
  const sessionId = getOrCreateSessionId();

  try {
    const response = await fetch(TUTOR_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${TUTOR_API_KEY}`
      },
      body: JSON.stringify({
        student_id: getCurrentUser().id,
        session_id: sessionId,
        message: studentMessage,
        current_problem: {
          id: currentProblem.id,
          text: currentProblem.text,
          correct_answer: currentProblem.correct_answer
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Tutor API error: ${response.status}`);
    }

    const data = await response.json();
    return data;

  } catch (error) {
    console.error('Tutor service error:', error);
    // Fallback to static response or show error
    return {
      response: "I'm having trouble right now. Could you try again?",
      metadata: { error: true }
    };
  }
}

// Session ID management
function getOrCreateSessionId() {
  let sessionId = sessionStorage.getItem('tutor_session_id');

  if (!sessionId) {
    sessionId = `sess_${Date.now()}_${getCurrentUser().id}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('tutor_session_id', sessionId);
  }

  return sessionId;
}

function getCurrentUser() {
  // Your existing user context
  return window.user || { id: 'guest' };
}
```

#### 2. Integrate with Text Module

```javascript
// src/components/TutorChat.jsx

import React, { useState } from 'react';
import { sendToTutor } from '../services/tutorService';

export function TutorChat({ currentProblem }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    // Add student message to chat
    const studentMessage = {
      role: 'student',
      content: input,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, studentMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Call tutor API
      const tutorResponse = await sendToTutor(input, currentProblem);

      // Add tutor message to chat
      const tutorMessage = {
        role: 'tutor',
        content: tutorResponse.response,
        metadata: tutorResponse.metadata,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, tutorMessage]);

      // Optional: Track analytics
      trackTutorInteraction(tutorResponse.metadata);

    } catch (error) {
      console.error('Error:', error);
      // Show error message
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="tutor-chat">
      {/* Chat messages */}
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type your answer..."
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading}>
          {isLoading ? 'Thinking...' : 'Send'}
        </button>
      </div>
    </div>
  );
}
```

#### 3. Environment Configuration

```bash
# .env.production
REACT_APP_TUTOR_WEBHOOK_URL=https://your-n8n-instance.com/webhook/tutor/message
REACT_APP_TUTOR_API_KEY=your_secret_api_key_here
```

#### 4. CORS Configuration

In n8n webhook settings, allow MinS domains:
```
Access-Control-Allow-Origin: https://mins.com, https://app.mins.com
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

### Pros & Cons

**Pros**:
- Simple, fast implementation
- Low latency (direct connection)
- Easy to debug (browser DevTools)

**Cons**:
- Exposes API key in frontend (security risk)
- No server-side analytics
- Can't add business logic

---

## Option B: Backend Proxy Integration (Recommended)

### Overview

MinS backend acts as proxy between frontend and n8n webhook.

### Architecture

```
MinS Frontend
    ↓
MinS Backend (Node.js/Express)
    ├─ Validate request
    ├─ Get current problem from DB
    ├─ Call n8n webhook
    ├─ Log analytics
    └─ Return response
        ↓
MinS Frontend displays
```

### Implementation

#### 1. Backend API Endpoint

```javascript
// routes/tutor.js (Express)

const express = require('express');
const router = express.Router();
const axios = require('axios');

const TUTOR_WEBHOOK_URL = process.env.TUTOR_WEBHOOK_URL;
const TUTOR_API_KEY = process.env.TUTOR_API_KEY;

// POST /api/tutor/message
router.post('/message', async (req, res) => {
  const { student_id, message } = req.body;

  // Validate input
  if (!student_id || !message) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  try {
    // Get current problem from your database
    const currentProblem = await getCurrentProblemFor Student(student_id);

    if (!currentProblem) {
      return res.status(404).json({ error: 'No active problem' });
    }

    // Get or create session ID (stored in MinS DB)
    const sessionId = await getOrCreateTutorSession(student_id);

    // Call n8n webhook
    const tutorResponse = await axios.post(TUTOR_WEBHOOK_URL, {
      student_id,
      session_id: sessionId,
      message,
      current_problem: {
        id: currentProblem.id,
        text: currentProblem.question,
        correct_answer: currentProblem.answer
      }
    }, {
      headers: {
        'Authorization': `Bearer ${TUTOR_API_KEY}`,
        'Content-Type': 'application/json'
      },
      timeout: 10000 // 10 second timeout
    });

    // Log interaction to MinS analytics
    await logTutorInteraction({
      student_id,
      problem_id: currentProblem.id,
      message,
      category: tutorResponse.data.metadata.category,
      latency: tutorResponse.data.metadata.latency_ms,
      timestamp: new Date()
    });

    // Return to frontend
    res.json(tutorResponse.data);

  } catch (error) {
    console.error('Tutor API error:', error);

    // Graceful fallback
    res.status(500).json({
      response: "I'm having trouble right now. Could you try again?",
      metadata: {
        error: true,
        error_type: error.code || 'unknown'
      }
    });
  }
});

// Helper: Get current problem for student
async function getCurrentProblemForStudent(student_id) {
  // Your existing logic to get active problem
  const student = await Student.findById(student_id);
  const problem = await Problem.findById(student.current_problem_id);

  return {
    id: problem._id.toString(),
    question: problem.text,
    answer: problem.correct_answer
  };
}

// Helper: Get or create tutor session
async function getOrCreateTutorSession(student_id) {
  const student = await Student.findById(student_id);

  if (!student.tutor_session_id || isSessionExpired(student.tutor_session_started_at)) {
    // Create new session
    student.tutor_session_id = `sess_${Date.now()}_${student_id}_${generateRandomId()}`;
    student.tutor_session_started_at = new Date();
    await student.save();
  }

  return student.tutor_session_id;
}

function isSessionExpired(started_at) {
  const THIRTY_MINUTES = 30 * 60 * 1000;
  return Date.now() - new Date(started_at).getTime() > THIRTY_MINUTES;
}

module.exports = router;
```

#### 2. Frontend Integration

```javascript
// src/services/tutorService.js

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

export async function sendToTutor(studentMessage) {
  try {
    const response = await fetch(`${API_BASE_URL}/tutor/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}` // Your existing auth
      },
      body: JSON.stringify({
        student_id: getCurrentUser().id,
        message: studentMessage
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();

  } catch (error) {
    console.error('Tutor service error:', error);
    throw error;
  }
}
```

#### 3. Database Schema Updates

```javascript
// models/Student.js (Mongoose example)

const studentSchema = new mongoose.Schema({
  // ... existing fields

  // Tutor session tracking
  tutor_session_id: { type: String, index: true },
  tutor_session_started_at: { type: Date },

  // Current problem
  current_problem_id: { type: mongoose.Schema.Types.ObjectId, ref: 'Problem' }
});

// models/TutorInteraction.js (Analytics)

const tutorInteractionSchema = new mongoose.Schema({
  student_id: { type: mongoose.Schema.Types.ObjectId, ref: 'Student', required: true },
  problem_id: { type: mongoose.Schema.Types.ObjectId, ref: 'Problem', required: true },
  session_id: { type: String, required: true },

  student_message: { type: String, required: true },
  tutor_response: { type: String, required: true },

  category: { type: String, enum: ['correct', 'close', 'wrong_operation', 'conceptual_question', 'stuck', 'off_topic'] },
  is_answer: { type: Boolean },
  verification_result: { type: Object },

  attempt_count: { type: Number },
  latency_ms: { type: Number },

  created_at: { type: Date, default: Date.now, index: true }
});
```

### Pros & Cons

**Pros**:
- Secure (API key hidden on server)
- Full analytics tracking
- Can add business logic (permissions, rate limiting)
- Current problem fetched from DB (single source of truth)

**Cons**:
- More complex implementation
- Slightly higher latency (extra hop)
- Requires backend changes

---

## Option C: Iframe Embedding

### Quick Testing Only

```html
<!-- For isolated testing, not production -->
<iframe
  src="https://n8n-instance.com/webhook-test-ui"
  width="400"
  height="600"
  frameborder="0"
></iframe>
```

Not recommended for production. Use for demos/testing only.

---

## Testing Integration

### 1. Unit Tests

```javascript
// __tests__/tutorService.test.js

import { sendToTutor } from '../services/tutorService';

describe('Tutor Service', () => {
  it('sends message and receives response', async () => {
    const problem = {
      id: 'test_1',
      text: 'What is 2 + 2?',
      correct_answer: '4'
    };

    const response = await sendToTutor('4', problem);

    expect(response.response).toBeTruthy();
    expect(response.metadata.category).toBe('correct');
  });

  it('handles API errors gracefully', async () => {
    // Mock network error
    global.fetch = jest.fn(() => Promise.reject('Network error'));

    const response = await sendToTutor('test', {});

    expect(response.metadata.error).toBe(true);
  });
});
```

### 2. Integration Tests

```javascript
// Test end-to-end flow
const request = require('supertest');
const app = require('../app');

describe('POST /api/tutor/message', () => {
  it('returns tutor response', async () => {
    const res = await request(app)
      .post('/api/tutor/message')
      .send({
        student_id: 'test_student',
        message: '2'
      })
      .expect(200);

    expect(res.body.response).toBeTruthy();
    expect(res.body.metadata.category).toMatch(/correct|close|wrong_operation/);
  });
});
```

### 3. Manual Testing Checklist

- [ ] Student can send message
- [ ] Tutor response appears in UI
- [ ] Multi-turn conversation works (session persists)
- [ ] Attempt count increments correctly
- [ ] Different categories trigger different responses
- [ ] Error handling shows user-friendly message
- [ ] Latency is acceptable (< 3s)
- [ ] Session expires after 30 minutes

---

## Production Checklist

### Security

- [ ] API keys stored in environment variables (not code)
- [ ] HTTPS enabled (not HTTP)
- [ ] CORS configured (whitelist only MinS domains)
- [ ] Rate limiting enabled (60 req/min per student)
- [ ] Input validation on all fields
- [ ] SQL injection prevention (parameterized queries)
- [ ] No sensitive data in logs (e.g., correct answers)

### Performance

- [ ] Latency < 3.5s for P99
- [ ] Timeout set on webhook calls (10s)
- [ ] Graceful error handling (fallback responses)
- [ ] Connection pooling for Redis/DB
- [ ] Monitoring alerts set up

### Analytics

- [ ] All tutor interactions logged to DB
- [ ] Dashboard shows: category distribution, avg latency, completion rate
- [ ] Student progress tracked (problems attempted, solved, avg attempts)

### Deployment

- [ ] Environment variables configured (staging + production)
- [ ] n8n webhook URL updated for production
- [ ] Redis session store configured
- [ ] Database indexes added (student_id, session_id, created_at)
- [ ] Backup/rollback plan ready

### Documentation

- [ ] Internal docs updated (how tutor works)
- [ ] Support team trained (what to tell students if issues)
- [ ] Monitoring runbook created (what to do if latency spikes)

---

## Troubleshooting

### Issue: "CORS error"

**Symptoms**: Browser console shows `Access-Control-Allow-Origin` error

**Solution**:
1. In n8n webhook settings → Response Headers:
   ```
   Access-Control-Allow-Origin: https://app.mins.com
   Access-Control-Allow-Methods: POST, OPTIONS
   Access-Control-Allow-Headers: Content-Type, Authorization
   ```
2. Or use backend proxy (Option B) - no CORS needed

### Issue: "Session not persisting across turns"

**Symptoms**: Attempt count always 1, no memory of previous conversation

**Solution**:
1. Check `session_id` is same across requests
2. Verify Redis/session storage is working
3. Check session hasn't expired (30 min TTL)

### Issue: "Slow response times (> 5s)"

**Symptoms**: User waits too long for tutor response

**Solution**:
1. Check n8n execution logs for bottlenecks
2. Verify OpenAI API key is valid (not rate limited)
3. Consider upgrading OpenAI tier (higher rate limits)
4. See `LATENCY-ANALYSIS.md` for optimization guide

### Issue: "Wrong category classification"

**Symptoms**: Student says "I don't know" but gets classified as "off_topic"

**Solution**:
1. Check prompt templates in n8n workflow
2. Adjust classification confidence thresholds
3. Add more examples to triage prompts

---

## Migration Roadmap

### Phase 1: Prototype (Now)
- n8n webhook + MinS backend proxy
- Redis session storage
- Basic analytics

### Phase 2: Production (1-2 months)
- Migrate n8n → Node.js/Express microservice
- Full MongoDB persistence
- Advanced analytics dashboard
- Multi-language support

### Phase 3: Scale (3-6 months)
- Knowledge base (RAG)
- Multi-step problem decomposition
- Voice integration
- Fine-tuned triage model

---

## Support

- **Integration issues**: Contact Vlad (consultant)
- **n8n errors**: Check workflow execution logs
- **API spec**: See `API-SPEC.md`
- **Full blueprint**: See `../1-blueprint/Tutoring-Flow-Blueprint.md`

---

**Ready to integrate?** Start with Option B (Backend Proxy) for production-quality implementation.

**Version**: 1.0
**Last Updated**: October 10, 2025
