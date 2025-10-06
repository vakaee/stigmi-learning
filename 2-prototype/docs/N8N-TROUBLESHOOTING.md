# n8n Troubleshooting Guide

**AI Tutor POC - Common Issues and Fixes**

This guide helps you debug and resolve common issues when running the AI Tutor workflows in n8n.

---

## Quick Diagnosis

Start here to quickly identify your issue:

| Symptom | Likely Cause | Jump to |
|---------|--------------|---------|
| Workflow not receiving requests | Webhook URL wrong or workflow inactive | [Webhook Issues](#webhook-issues) |
| "OpenAI credential not found" error | Credential not configured | [OpenAI Credential Issues](#openai-credential-issues) |
| Response takes >5 seconds | Network latency or LLM timeout | [Performance Issues](#performance-issues) |
| "Cannot parse JSON" error | Invalid input format | [Input Validation Issues](#input-validation-issues) |
| Wrong category returned | Triage logic issue | [Triage Issues](#triage-issues) |
| Session memory not working | Session storage issue | [Session Issues](#session-issues) |
| Verification fails for correct answer | Math.js parsing error | [Verification Issues](#verification-issues) |

---

## Webhook Issues

### Problem: Workflow not receiving requests

**Symptoms**:
- curl command returns "Cannot POST" or 404
- No executions appear in n8n Executions panel
- Timeout errors

**Causes**:
1. Workflow is not active
2. Wrong webhook URL
3. Webhook path mismatch

**Fixes**:

#### Fix 1: Activate Workflow
1. Open workflow in n8n editor
2. Check **Active** toggle (top right) is ON
3. If off, toggle to ON
4. Try request again

#### Fix 2: Verify Webhook URL
1. Click on **Webhook Trigger** node
2. Check the **Webhook URLs** section
3. Use the **Production URL** for app integration
4. Use the **Test URL** for manual testing
5. Ensure you're using the correct URL in your curl/app

**Example correct URLs**:
- Production: `https://your-instance.app.n8n.cloud/webhook/tutor-test`
- Test: `https://your-instance.app.n8n.cloud/webhook-test/tutor-test`

For `workflow.json`:
- Production: `https://your-instance.app.n8n.cloud/webhook/tutor/message`

#### Fix 3: Check Webhook Path
1. Open **Webhook Trigger** node settings
2. Verify **Path** field matches your URL
3. For `workflow-simple.json`: path should be `tutor-test`
4. For `workflow.json`: path should be `tutor/message`
5. If wrong, update and save

### Problem: 401 Unauthorized

**Cause**: Webhook authentication enabled but request missing header

**Fix**:
1. Check **Webhook Trigger** node settings
2. If **Authentication** is set to "Header Auth":
   - Note the header name (e.g., `X-API-Key`)
   - Note the header value
3. Add header to your request:
```bash
curl -X POST [URL] \
  -H "X-API-Key: your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Problem: CORS errors (browser only)

**Symptoms**:
- "CORS policy" error in browser console
- Works in curl but not in web app

**Fix**:
For self-hosted n8n, add CORS headers:
1. Edit n8n environment variables
2. Add: `N8N_CORS_ORIGIN=https://your-frontend-domain.com`
3. Restart n8n

For n8n Cloud:
- Use backend proxy (Option B in INTEGRATION.md)
- Or contact n8n support to whitelist your domain

---

## OpenAI Credential Issues

### Problem: "OpenAI credential not found"

**Symptoms**:
- Workflow fails at OpenAI nodes
- Error: "Credentials for 'OpenAI' are not set"

**Fix**:
1. Click **Credentials** in left sidebar
2. Verify OpenAI credential exists
3. If not, create it:
   - Click **+ Add Credential**
   - Select **OpenAI**
   - Enter API key from OpenAI dashboard
   - Save
4. Link to workflow:
   - Open workflow
   - Click each OpenAI node
   - Select credential from dropdown
   - Save workflow

**Note**: For `workflow.json`, you need to link credentials to 7 OpenAI nodes:
- Stage 1: Triage (Is Answer?)
- Stage 2b: Non-Answer Intent
- Response: Correct (Teach Back)
- Response: Close (Probe)
- Response: Wrong Operation (Clarify)
- Response: Conceptual Question
- Response: Stuck (Scaffold)
- Response: Off Topic (Redirect)

### Problem: "OpenAI API key invalid"

**Symptoms**:
- Error: "Incorrect API key provided"
- Status code 401 from OpenAI

**Fix**:
1. Verify API key is correct:
   - Go to https://platform.openai.com/api-keys
   - Check key starts with `sk-`
   - If expired/revoked, create new key
2. Update credential in n8n:
   - Click **Credentials** → Your OpenAI credential
   - Replace with new API key
   - Save
3. Test workflow again

### Problem: "Rate limit exceeded"

**Symptoms**:
- Error: "Rate limit reached for requests"
- Status code 429 from OpenAI

**Fix**:
1. **Short-term**: Wait 1 minute, try again
2. **Long-term**: Upgrade OpenAI plan or add rate limiting in backend proxy

---

## Performance Issues

### Problem: Response takes >5 seconds

**Symptoms**:
- Slow responses
- Timeouts in frontend
- Poor user experience

**Diagnosis**:
1. Click **Executions** in n8n sidebar
2. Open a slow execution
3. Check execution time per node
4. Identify bottleneck

**Common Bottlenecks**:

#### Bottleneck 1: OpenAI LLM Calls
**Typical time**: 300-800ms per call

**Fixes**:
1. Reduce `max_tokens` in OpenAI nodes:
   - Click OpenAI node → Options
   - Set `max_tokens` to 100-150 (for short responses)
2. Use `gpt-4o-mini` instead of `gpt-4` (already configured)
3. Increase `temperature` slightly (0.7 → 0.8) for faster sampling

#### Bottleneck 2: Network Latency
**Typical time**: 100-300ms

**Fixes**:
1. Deploy n8n closer to your users (same region)
2. Use n8n Cloud in same region as your app
3. For self-hosted: use cloud provider in same region as OpenAI (us-east-1)

#### Bottleneck 3: Session Load/Save
**Typical time**: 50-100ms (Redis), 200-500ms (workflow static data)

**Fix**:
For `workflow.json` (uses workflow static data):
1. Migrate to Redis for faster session storage:
   - Add Redis node before "Update Session" node
   - Use Redis GET/SET commands
   - See `session_management.js` for schema
2. Or accept the trade-off (slower but no external dependency)

#### Bottleneck 4: Too Many Nodes
**Typical time**: 10-20ms overhead per node

**Fix**:
- Use `workflow-simple.json` for basic use cases
- Or migrate to Node.js for production (see DEPLOYMENT.md)

**Target Latency**:
- P50 (median): <1500ms
- P95: <3000ms
- P99: <5000ms

If consistently slower, review execution logs to identify specific slow nodes.

---

## Input Validation Issues

### Problem: "Cannot parse JSON" error

**Symptoms**:
- Error at beginning of workflow
- "Unexpected token" error

**Fix**:
1. Verify request body is valid JSON:
```bash
# Test with jq
echo '{...}' | jq .
```
2. Ensure `Content-Type: application/json` header is set
3. Check for missing commas, quotes, or braces
4. Use a JSON validator: https://jsonlint.com

**Correct format**:
```json
{
  "student_id": "test_123",
  "session_id": "sess_001",
  "message": "2",
  "current_problem": {
    "id": "neg_add_1",
    "text": "What is -3 + 5?",
    "correct_answer": "2"
  }
}
```

### Problem: Missing required fields

**Symptoms**:
- Workflow fails at "Verify Answer" or "Stage 1 Triage" node
- Error: "Cannot read property 'X' of undefined"

**Fix**:
Ensure all required fields are present:
- `student_id` (string)
- `session_id` (string)
- `message` (string) - student's input
- `current_problem` (object):
  - `id` (string)
  - `text` (string)
  - `correct_answer` (string or number)

**Optional fields**:
- `current_problem.metadata` (object)

---

## Triage Issues

### Problem: Wrong category returned

**Symptoms**:
- Student says "I don't know" but category is "wrong_operation"
- Answer "2" for "-3 + 5 = ?" returns "close" instead of "correct"

**Diagnosis**:
1. Open execution in n8n
2. Check output of **Stage 1: Triage** node
3. Check output of **Verify Answer** node (if is_answer=true)
4. Check output of **Stage 2a** or **Stage 2b** node

**Common Issues**:

#### Issue 1: Stage 1 Misclassifies
**Example**: "I don't know" detected as `is_answer: true`

**Cause**: LLM hallucination or ambiguous input

**Fix**:
1. Check Stage 1 Triage prompt (in OpenAI node)
2. Add more examples to prompt:
```
Examples:
- "I don't know" → is_answer: false
- "I'm stuck" → is_answer: false
- "2" → is_answer: true
```
3. Increase `temperature` to 0.3 for more consistent results
4. Or use fine-tuned model (Phase 2)

#### Issue 2: Verification Fails
**Example**: Answer "2.0" for correct answer "2" returns `correct: false`

**Cause**: Math.js comparison without tolerance

**Fix**:
Already handled in `workflow.json` - verification uses 0.001 tolerance. If still failing:
1. Open **Verify Answer** node (Function node)
2. Check `tolerance` value (should be `0.001`)
3. Increase if needed: `const tolerance = 0.01;`

#### Issue 3: "Close" threshold too strict
**Example**: Answer "1.9" for correct answer "2" returns "wrong_operation" instead of "close"

**Cause**: 20% threshold not appropriate for small numbers

**Fix**:
1. Open **Classify Answer Quality** node
2. Adjust `closeThreshold` calculation:
```javascript
// Original (20% of correct value)
const closeThreshold = Math.abs(correctNum * 0.2);

// Alternative (absolute difference)
const closeThreshold = 0.5; // Accept answers within ±0.5
```

---

## Session Issues

### Problem: Session memory not persisting

**Symptoms**:
- Each turn acts like first interaction
- `attempt_count` always 1
- Tutor doesn't reference previous turns

**Diagnosis**:
1. Check `session_id` is the same across requests
2. Check workflow execution logs:
   - Open **Update Session** node output
   - Verify `session.recent_turns` array grows

**For workflow.json**:

#### Issue 1: Different session_id each request
**Fix**: Use same `session_id` for entire conversation:
```javascript
// Good (frontend)
const sessionId = generateUUID(); // Once per problem
// Use same sessionId for all turns on this problem

// Bad
const sessionId = generateUUID(); // New UUID every request
```

#### Issue 2: Workflow static data cleared
**Cause**: Workflow redeployed or n8n restarted

**Fix**:
1. **Short-term**: Accept this limitation for POC
2. **Long-term**: Migrate to Redis:
   - Add **Redis** node after **Load Session**
   - Use `GET session:{session_id}`
   - Add **Redis** node in **Update Session**
   - Use `SET session:{session_id} {json} EX 1800` (30-min TTL)

#### Issue 3: Session expires too quickly
**Cause**: 30-minute TTL (if using Redis)

**Fix**:
1. Increase TTL in Redis SET command:
```javascript
// 1 hour
SET session:{session_id} {json} EX 3600

// 24 hours
SET session:{session_id} {json} EX 86400
```

---

## Verification Issues

### Problem: Verification fails for correct answers

**Symptoms**:
- Answer "2" for "-3 + 5" returns `correct: false`
- Written numbers ("two") not recognized
- Fractions ("1/2") not verified correctly

**Diagnosis**:
1. Open execution logs
2. Check **Verify Answer** node output
3. Look for `error` field in verification result

**Common Issues**:

#### Issue 1: Written numbers not parsed
**Example**: Input "two" for correct answer "2"

**Cause**: Number word replacement not applied

**Fix**:
Already handled in `workflow.json`. If still failing:
1. Open **Verify Answer** node
2. Check `numberWords` object includes your case
3. Add more mappings:
```javascript
const numberWords = {
  'zero': '0', 'one': '1', 'two': '2', // ... existing
  'eleven': '11', 'twelve': '12', // Add more
  'twenty': '20', 'thirty': '30',
};
```

#### Issue 2: Fractions not evaluated
**Example**: Input "1/2" for correct answer "0.5"

**Cause**: Math.js should handle this, but check if it's working

**Fix**:
Test in isolation:
1. Add temporary **Code** node:
```javascript
const math = require('mathjs');
const result = math.evaluate('1/2');
return { json: { result } };
```
2. Should return `0.5`
3. If error, check math.js is available in n8n environment

#### Issue 3: Expression evaluation fails
**Example**: Input "3 - 1" for correct answer "2"

**Cause**: Math.js not evaluating expressions

**Fix**:
Already handled in `workflow.json`. If still failing:
1. Check **Verify Answer** node
2. Ensure `math.evaluate()` is used (not just `parseFloat()`)

---

## Response Quality Issues

### Problem: Tutor responses are too generic

**Symptoms**:
- Tutor says "I'm here to help!" for all categories
- No personalization based on student input

**Diagnosis**:
1. Check execution logs
2. Look at **Response: [Category]** node output
3. Check if correct prompt template is being used

**Fix**:
1. Open the relevant **Response** node (e.g., **Response: Wrong Operation**)
2. Check the **Messages** section
3. Verify prompt includes:
   - `{{$json.problem}}` (current problem)
   - `{{$json.student_input}}` (what student said)
   - `{{$json.chat_history}}` (previous turns)
   - `{{$json.attempt_count}}` (escalation level)
4. If missing, update prompt template from `1-blueprint/prompts/*.yaml`

### Problem: Tutor gives away the answer

**Symptoms**:
- Tutor says "The answer is 2" instead of guiding

**Fix**:
1. Review prompt templates in `1-blueprint/prompts/`
2. Add explicit instruction to prompts:
```yaml
Rules:
- DO NOT give the answer directly
- Ask Socratic questions to guide thinking
- Use concrete examples (number line, objects)
```
3. Update the OpenAI node with revised prompt

---

## Debugging Tips

### Enable Verbose Logging

For self-hosted n8n:
1. Edit `.env` file
2. Add: `N8N_LOG_LEVEL=debug`
3. Restart n8n
4. Check logs: `docker-compose logs -f n8n`

### Use n8n's Built-in Debugger

1. Open workflow
2. Click **Execute Workflow** (top right)
3. Send test request
4. Watch nodes execute in real-time
5. Click any node to see its output

### Test Individual Nodes

1. Right-click a node
2. Select **Execute Node**
3. Provide sample input data
4. See output without running full workflow

### Check OpenAI API Directly

Test if OpenAI is working outside n8n:
```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer sk-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Test"}],
    "max_tokens": 50
  }'
```

### Clear Workflow Static Data

If session data is corrupted:
1. Open **Update Session** node
2. Find the line: `$setWorkflowStaticData('global', { sessions });`
3. Temporarily replace with: `$setWorkflowStaticData('global', {});`
4. Execute workflow once to clear all sessions
5. Revert the change

---

## Performance Optimization

### Reduce Latency

1. **Parallel execution**: n8n executes nodes in parallel when possible. No action needed.
2. **Reduce LLM tokens**: Lower `max_tokens` in OpenAI nodes (100-150 for short responses)
3. **Use Redis**: Faster session storage than workflow static data
4. **Deploy regionally**: n8n + OpenAI in same region (us-east-1)

### Reduce Costs

1. **Use gpt-4o-mini**: Already configured (90% cheaper than GPT-4)
2. **Cache responses**: For common questions (future enhancement)
3. **Limit max_tokens**: Set to minimum needed (100-150)
4. **Monitor usage**: Check OpenAI dashboard for token consumption

---

## Common Error Messages

### "Cannot read property 'json' of undefined"

**Cause**: Node trying to access data from previous node that didn't execute

**Fix**: Check conditional logic (If nodes) - ensure all paths lead to expected nodes

### "Workflow did not return any data"

**Cause**: Workflow execution stopped before reaching **Respond to Webhook** node

**Fix**: Check for errors in middle nodes, ensure all paths converge to response node

### "Function execution timed out"

**Cause**: JavaScript code in Function node took >10 seconds

**Fix**: Optimize code in **Verify Answer** or **Update Session** nodes

### "Invalid JSON in response"

**Cause**: OpenAI returned non-JSON output despite prompt asking for JSON

**Fix**: Add JSON parsing with error handling:
```javascript
try {
  const parsed = JSON.parse($json.message.content);
  return { json: parsed };
} catch (error) {
  // Fallback
  return { json: { is_answer: false, confidence: 0.5 } };
}
```

---

## When to Contact Support

Contact n8n support if:
- n8n Cloud is down (check status.n8n.io)
- Workflow corruption (cannot open workflow)
- Credential issues not resolved by above fixes

Contact OpenAI support if:
- API key issues persist
- Consistent 500 errors from OpenAI
- Billing/quota questions

Contact consultant (Vlad) if:
- Triage logic needs adjustment
- Prompt templates need refinement
- Architecture questions

---

## Useful Commands

### Test workflow with curl
```bash
curl -X POST [WEBHOOK_URL] \
  -H "Content-Type: application/json" \
  -d @test-payload.json
```

### View n8n logs (self-hosted)
```bash
docker-compose logs -f n8n
```

### Check Redis session (if using Redis)
```bash
redis-cli GET session:test_session_123
```

### Clear Redis sessions (if using Redis)
```bash
redis-cli KEYS "session:*" | xargs redis-cli DEL
```

---

## Additional Resources

- **n8n Community Forum**: https://community.n8n.io
- **n8n Documentation**: https://docs.n8n.io
- **OpenAI Status**: https://status.openai.com
- **Blueprint Document**: `1-blueprint/Tutoring-Flow-Blueprint.md`
- **API Specification**: `2-prototype/docs/API-SPEC.md`
- **Setup Guide**: `2-prototype/docs/N8N-SETUP.md`

---

**Troubleshooting Version**: 1.0
**Last Updated**: October 10, 2025
**Status**: Comprehensive coverage of common issues
