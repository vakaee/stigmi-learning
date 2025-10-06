# Handoff Checklist - AI Tutor POC

**From**: Vlad (Consultant)
**To**: MinS Development Team
**Date**: October 10, 2025
**Phase**: 1 Delivery

---

## Purpose

This checklist ensures MinS team has everything needed to understand, test, integrate, and eventually productionize the AI tutor prototype.

---

## 1. Documentation Review

### Core Documents

- [ ] **Blueprint** (`1-blueprint/Tutoring-Flow-Blueprint.md`)
  - [ ] Understand two-stage triage system
  - [ ] Review all 6 prompt templates
  - [ ] Study session memory schema
  - [ ] Review verification approach
  - [ ] Understand latency optimization

- [ ] **Executive Summary** (`SUMMARY.md`)
  - [ ] Share with Min/Isaac for investor context
  - [ ] Understand business value proposition

- [ ] **API Specification** (`2-prototype/docs/API-SPEC.md`)
  - [ ] Understand webhook contract
  - [ ] Review request/response formats
  - [ ] Note all 6 category types

- [ ] **Integration Guide** (`2-prototype/docs/INTEGRATION.md`)
  - [ ] Choose integration option (A, B, or C)
  - [ ] Review code examples for your stack

- [ ] **Deployment Guide** (`2-prototype/docs/DEPLOYMENT.md`)
  - [ ] Choose deployment platform (n8n Cloud vs self-hosted)
  - [ ] Review production checklist

- [ ] **Known Limitations** (`3-delivery/KNOWN-LIMITATIONS.md`)
  - [ ] Set realistic expectations
  - [ ] Identify Phase 2 priorities

- [ ] **Changelog** (`3-delivery/CHANGELOG.md`)
  - [ ] Understand technical decisions made
  - [ ] Review alternatives considered

---

## 2. Code Review

### JavaScript Functions

- [ ] **verify_answer.js**
  - [ ] Understand math.js usage
  - [ ] Review edge case handling (fractions, decimals, written numbers)
  - [ ] Note 20% "close" threshold

- [ ] **session_management.js**
  - [ ] Understand session schema
  - [ ] Review turn tracking logic
  - [ ] Note 5-turn memory window
  - [ ] Check escalation rules (attempt 1/2/3+)

- [ ] **classify_answer_quality.js**
  - [ ] Review rule-based classification
  - [ ] Understand when to use vs LLM

### Prompt Templates

- [ ] **All 8 YAML files** in `1-blueprint/prompts/`
  - [ ] triage-stage1.yaml
  - [ ] triage-stage2b.yaml
  - [ ] teach_back.yaml
  - [ ] probe.yaml
  - [ ] clarify.yaml
  - [ ] concept.yaml
  - [ ] scaffold.yaml
  - [ ] redirect.yaml
  - [ ] Review Jinja2 templating syntax
  - [ ] Understand variable injection
  - [ ] Note attempt-based conditionals

---

## 3. Testing

### Setup Test Environment

- [ ] **Get access to n8n instance**
  - URL: ___________________
  - Login: ___________________
  - Password: ___________________

- [ ] **Get API credentials**
  - OpenAI API key: ___________________
  - Redis URL (if using): ___________________
  - Webhook auth token: ___________________

### Import & Activate Workflow

- [ ] Import `workflow.json` to n8n (once created)
- [ ] Configure OpenAI credential
- [ ] Configure Redis credential (optional)
- [ ] Activate workflow
- [ ] Copy webhook URL: ___________________

### Run Basic Tests

- [ ] **Test all 6 categories**:
  - [ ] Correct: Send "2" for problem "-3 + 5 = ?"
  - [ ] Close: Send "1" for same problem
  - [ ] Wrong operation: Send "-8" for same problem
  - [ ] Conceptual: Send "What's a negative number?"
  - [ ] Stuck: Send "I don't know"
  - [ ] Off-topic: Send "What's for lunch?"

- [ ] **Test multi-turn conversation**:
  - [ ] Use same `session_id` across 3-4 turns
  - [ ] Verify attempt count increments
  - [ ] Verify escalation (probe → hint → teach)
  - [ ] Check session memory (tutor references previous turns)

- [ ] **Test edge cases**:
  - [ ] Send "2.0" (decimal) → should verify as correct
  - [ ] Send "two" (written) → should verify as correct
  - [ ] Send "1/2" (fraction) for problem with answer "0.5"
  - [ ] Wait 31 minutes → verify session expires

- [ ] **Test error handling**:
  - [ ] Send malformed JSON → check error response
  - [ ] Send missing `current_problem` → check validation
  - [ ] Disable OpenAI credential → check fallback response

### Measure Performance

- [ ] **Record latency** for 10 test turns:
  - Turn 1: _____ ms
  - Turn 2: _____ ms
  - Turn 3: _____ ms
  - ...
  - Average: _____ ms (should be <2s)
  - P95: _____ ms (should be <3s)

- [ ] **Check n8n execution logs**:
  - [ ] View successful execution
  - [ ] Identify slowest node
  - [ ] Check for errors/warnings

---

## 4. Integration Planning

### Choose Integration Approach

- [ ] **Option A: Direct Frontend** (quick MVP)
- [ ] **Option B: Backend Proxy** (recommended for production)
- [ ] **Option C: Iframe** (testing only)

Selected: ___________________

### Backend Integration (if Option B)

- [ ] **Create API endpoint**: `POST /api/tutor/message`
- [ ] **Implement**:
  - [ ] Input validation
  - [ ] Get current problem from database
  - [ ] Call n8n webhook
  - [ ] Log interaction to analytics
  - [ ] Return response to frontend

- [ ] **Database updates**:
  - [ ] Add `tutor_session_id` to Student model
  - [ ] Add `tutor_session_started_at` to Student model
  - [ ] Create `TutorInteraction` collection (analytics)

### Frontend Integration

- [ ] **Create tutor service**: `src/services/tutorService.js`
- [ ] **Integrate with text module component**
- [ ] **Add loading state** (while waiting for response)
- [ ] **Handle errors** (show user-friendly message)
- [ ] **Test end-to-end** (student types → tutor responds)

---

## 5. Production Deployment

### Pre-Deployment Checklist

- [ ] **Environment variables set**:
  - [ ] `OPENAI_API_KEY`
  - [ ] `REDIS_URL` (if using)
  - [ ] `TUTOR_WEBHOOK_URL`
  - [ ] `TUTOR_API_KEY`

- [ ] **Security**:
  - [ ] HTTPS enabled
  - [ ] Webhook authentication configured
  - [ ] CORS whitelist set (MinS domains only)
  - [ ] Rate limiting configured (60 req/min per student)
  - [ ] Secrets stored in environment (not code)

- [ ] **Monitoring**:
  - [ ] Uptime monitoring (e.g., UptimeRobot)
  - [ ] Error tracking (e.g., Sentry)
  - [ ] Latency alerts (if P95 > 3s)

- [ ] **Backups**:
  - [ ] n8n workflow exported and committed to git
  - [ ] Redis persistence enabled (if using)
  - [ ] Database backups scheduled

### Deploy

- [ ] **Choose platform**:
  - [ ] n8n Cloud (fastest)
  - [ ] Self-hosted n8n (more control)
  - [ ] Migrate to Node.js (long-term)

- [ ] **Update MinS config**:
  - [ ] Point `TUTOR_WEBHOOK_URL` to production
  - [ ] Test from staging environment
  - [ ] Test from production environment

- [ ] **Smoke test**:
  - [ ] Send test request from production
  - [ ] Verify response received
  - [ ] Check latency acceptable
  - [ ] Review logs for errors

---

## 6. Analytics & Monitoring

### Set Up Analytics

- [ ] **Create analytics collection** (MongoDB):
  ```javascript
  TutorInteraction {
    student_id, problem_id, session_id,
    student_message, tutor_response,
    category, verification_result,
    attempt_count, latency_ms,
    created_at
  }
  ```

- [ ] **Log every interaction** from backend proxy

- [ ] **Create dashboard** (optional Phase 1, recommended Phase 2):
  - Category distribution (pie chart)
  - Average latency over time (line chart)
  - Success rate (problems solved / attempted)
  - Top struggling students

### Monitoring Alerts

- [ ] **Set up alerts**:
  - [ ] Webhook down (uptime < 99%)
  - [ ] High latency (P95 > 3.5s)
  - [ ] High error rate (>1%)
  - [ ] Redis connection lost

---

## 7. Team Knowledge Transfer

### Schedule Sessions

- [ ] **Walkthrough with Vlad** (consultant):
  - Date: ___________________
  - Topics:
    - [ ] Architecture deep-dive
    - [ ] Prompt engineering best practices
    - [ ] Debugging tips
    - [ ] Phase 2 roadmap

- [ ] **Internal team review**:
  - [ ] Frontend lead reviews integration code
  - [ ] Backend lead reviews webhook proxy
  - [ ] DevOps reviews deployment

- [ ] **Support team training**:
  - [ ] What to tell students if tutor is slow/down
  - [ ] How to report issues
  - [ ] Known limitations to communicate

### Documentation Sharing

- [ ] **Share with stakeholders**:
  - [ ] Min/Isaac: SUMMARY.md + demo
  - [ ] Investors: Live demo + one-pager
  - [ ] Dev team: Full repo access

- [ ] **Add to MinS wiki/Confluence**:
  - [ ] Link to this repository
  - [ ] Internal runbook (how to restart, troubleshoot)
  - [ ] Escalation path (who to contact if issues)

---

## 8. Phase 2 Planning

### Prioritize Next Features

Review `KNOWN-LIMITATIONS.md` and prioritize:

1. [ ] **Must-have for production**:
   - [ ] Redis session storage (if not done)
   - [ ] Full analytics pipeline
   - [ ] 20-50 questions (expand bank)

2. [ ] **High priority** (1-2 months):
   - [ ] Knowledge base (RAG)
   - [ ] Student profiles
   - [ ] Admin dashboard

3. [ ] **Medium priority** (3-6 months):
   - [ ] Multi-step problems (agents)
   - [ ] Fine-tuned triage
   - [ ] Multi-language

4. [ ] **Low priority** (6-12 months):
   - [ ] Migrate to Node.js
   - [ ] Voice integration (if not in parallel workstream)
   - [ ] Advanced analytics

### Estimate Phase 2

- [ ] **Scope Phase 2 work**:
  - Selected features: ___________________
  - Estimated time: ___________________
  - Estimated cost: ___________________

- [ ] **Schedule kickoff**:
  - Date: ___________________
  - Attendees: ___________________

---

## 9. Issue Tracking

### Known Issues (if any)

- [ ] **Issue #1**: ___________________
  - Severity: Low / Medium / High
  - Workaround: ___________________
  - Fix planned: Yes / No / Phase 2

- [ ] **Issue #2**: ___________________

### Report New Issues

If you find bugs or issues:

1. **Check**: Is this a known limitation? (see KNOWN-LIMITATIONS.md)
2. **Document**: Issue description, steps to reproduce, expected vs actual
3. **Contact**: Vlad (consultant) or create GitHub issue (if repo available)

---

## 10. Sign-Off

### Dev Team Sign-Off

- [ ] **Frontend lead**: ___________________ (Name & Date)
  - [ ] Reviewed integration code
  - [ ] Tested frontend integration
  - [ ] Understands API contract

- [ ] **Backend lead**: ___________________ (Name & Date)
  - [ ] Reviewed webhook proxy
  - [ ] Tested backend integration
  - [ ] Understands session management

- [ ] **DevOps/Infrastructure**: ___________________ (Name & Date)
  - [ ] Reviewed deployment options
  - [ ] Configured production environment
  - [ ] Set up monitoring

### Stakeholder Sign-Off

- [ ] **Min/Isaac**: ___________________ (Name & Date)
  - [ ] Reviewed demo
  - [ ] Approved for investor presentation
  - [ ] Signed off on Phase 1 deliverables

### Consultant Sign-Off

- [ ] **Vlad**: ___________________ (Name & Date)
  - [ ] All deliverables complete
  - [ ] Documentation reviewed
  - [ ] Handoff session conducted
  - [ ] Available for Phase 2 questions

---

## 11. Next Steps

After completing this checklist:

1. **Week 1**: Test and integrate with MinS staging
2. **Week 2**: Deploy to production (soft launch)
3. **Week 3**: Gather feedback, monitor performance
4. **Week 4**: Prepare investor demo
5. **Phase 2**: Plan detailed implementation (RAG, analytics, more questions)

---

## Support Contacts

- **Technical questions**: Vlad (consultant) - vlad@email.com
- **n8n issues**: n8n support or community forum
- **OpenAI API**: OpenAI support
- **Internal MinS**: Backend lead / DevOps lead

---

## Appendix: Quick Reference

### Useful Commands

```bash
# Test webhook
curl -X POST $WEBHOOK_URL -H "Content-Type: application/json" -d @test.json

# Check n8n logs (self-hosted)
docker-compose logs -f n8n

# Check Redis session
redis-cli GET session:test_session_123

# Restart n8n (self-hosted)
docker-compose restart n8n
```

### Key Files

| File | Purpose |
|------|---------|
| `1-blueprint/Tutoring-Flow-Blueprint.md` | Full technical spec |
| `2-prototype/docs/API-SPEC.md` | Webhook API documentation |
| `2-prototype/docs/INTEGRATION.md` | How to integrate with MinS |
| `2-prototype/functions/*.js` | Reusable JavaScript code |
| `1-blueprint/prompts/*.yaml` | Prompt templates |
| `2-prototype/exemplars/questions.json` | Test questions |

---

**Checklist Version**: 1.0
**Last Updated**: October 10, 2025
**Status**: Ready for handoff

---

## ✅ Handoff Complete

**Date**: ___________________
**Signed by**: ___________________
