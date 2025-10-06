# Deployment Guide - AI Tutor Prototype

**Audience**: DevOps, Backend Developers
**Goal**: Deploy n8n-based AI tutor to production
**Platforms**: n8n Cloud, Self-hosted n8n, or migrate to Node.js

---

## Deployment Options

### Comparison

| Option | Complexity | Cost | Control | Recommended For |
|--------|------------|------|---------|-----------------|
| **n8n Cloud** | Very Low | $20-50/mo | Medium | Quick production, MVP |
| **Self-hosted n8n** | Medium | $10-20/mo | High | Custom needs, data privacy |
| **Migrate to Node.js** | High | $5-15/mo | Full | Long-term production, scale |

---

## Option 1: n8n Cloud (Fastest)

### 1. Sign Up

1. Go to https://n8n.cloud
2. Create account (free trial available)
3. Choose plan: **Starter** ($20/mo) or **Pro** ($50/mo)

### 2. Import Workflow

1. In n8n Cloud dashboard → **Workflows**
2. Click **Import from File**
3. Upload `workflow.json` from prototype
4. Activate workflow

### 3. Configure Credentials

**OpenAI**:
- Settings → Credentials → Add OpenAI
- API Key: (from OpenAI dashboard)
- Save

**Redis** (if using):
- Add Redis credential
- Host: Your Redis instance (e.g., Redis Cloud)
- Port: 6379
- Password: (from Redis dashboard)

### 4. Get Webhook URL

1. Open workflow
2. Click **Webhook** node
3. Copy **Production URL**:
   ```
   https://your-instance.app.n8n.cloud/webhook/tutor/message
   ```

### 5. Test

```bash
curl -X POST https://your-instance.app.n8n.cloud/webhook/tutor/message \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test",
    "session_id": "test_session",
    "message": "2",
    "current_problem": {"id": "test_1", "text": "What is 1+1?", "correct_answer": "2"}
  }'
```

### 6. Point MinS to Production

Update MinS backend `.env`:
```bash
TUTOR_WEBHOOK_URL=https://your-instance.app.n8n.cloud/webhook/tutor/message
TUTOR_API_KEY=your_webhook_auth_token
```

### Pros & Cons

**Pros**:
- Zero infrastructure management
- Auto-scaling
- Built-in monitoring
- SSL/HTTPS included

**Cons**:
- Monthly cost ($20-50)
- Less control
- Data hosted by n8n

---

## Option 2: Self-Hosted n8n

### Requirements

- VPS with 2GB RAM minimum (DigitalOcean, AWS EC2, Linode)
- Ubuntu 20.04+ or Docker-capable OS
- Domain name (optional, for SSL)

### 1. Server Setup (Ubuntu)

```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
apt install docker-compose -y
```

### 2. Create Docker Compose File

```yaml
# docker-compose.yml

version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - N8N_HOST=${N8N_HOST}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - NODE_ENV=production
      - WEBHOOK_URL=https://${N8N_HOST}/
      - GENERIC_TIMEZONE=America/New_York
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - n8n-network

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - n8n-network

volumes:
  n8n_data:
  redis_data:

networks:
  n8n-network:
```

### 3. Environment Variables

```bash
# .env file

N8N_PASSWORD=your_secure_password_here
N8N_HOST=n8n.yourcompany.com
REDIS_PASSWORD=your_redis_password_here
```

### 4. Start Services

```bash
docker-compose up -d

# Check logs
docker-compose logs -f n8n
```

### 5. Configure SSL (with Nginx)

```bash
# Install Nginx
apt install nginx certbot python3-certbot-nginx -y

# Create Nginx config
nano /etc/nginx/sites-available/n8n
```

```nginx
# /etc/nginx/sites-available/n8n

server {
    listen 80;
    server_name n8n.yourcompany.com;

    location / {
        proxy_pass http://localhost:5678;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Enable site
ln -s /etc/nginx/sites-available/n8n /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Get SSL certificate
certbot --nginx -d n8n.yourcompany.com
```

### 6. Import Workflow

1. Access https://n8n.yourcompany.com
2. Login (admin / your_password)
3. Import `workflow.json`
4. Configure credentials (OpenAI, Redis)
5. Activate workflow

### Pros & Cons

**Pros**:
- Full control
- Lower cost (~$10-20/mo for VPS)
- Data stays on your server

**Cons**:
- Manual setup required
- You manage updates/backups
- Need DevOps knowledge

---

## Option 3: Migrate to Node.js/Express

### For Long-Term Production

**Timeline**: 2-3 weeks for full migration

### 1. Create Express Server

```javascript
// server.js

const express = require('express');
const { verifyAnswer } = require('./functions/verify_answer');
const { initializeSession, updateSession } = require('./functions/session_management');
const { triageStage1 } = require('./services/triage');
const { generateResponse } = require('./services/response');

const app = express();
app.use(express.json());

// Session storage
const sessions = new Map(); // Replace with Redis in production

// POST /tutor/message
app.post('/tutor/message', async (req, res) => {
  const startTime = Date.now();
  const { student_id, session_id, message, current_problem } = req.body;

  try {
    // 1. Load or create session
    let session = sessions.get(session_id);
    if (!session) {
      session = initializeSession(student_id, session_id, current_problem);
      sessions.set(session_id, session);
    }

    // 2. Stage 1 Triage: is_answer?
    const stage1 = await triageStage1(message, current_problem.text);

    let category, verification = null;

    if (stage1.is_answer) {
      // 3. Verify answer
      verification = verifyAnswer(message, current_problem.correct_answer);

      // 4. Stage 2a: Classify answer quality
      category = verification.correct ? 'correct' :
                 verification.close ? 'close' : 'wrong_operation';
    } else {
      // 5. Stage 2b: Classify non-answer intent
      const stage2b = await triageStage2b(message, current_problem.text);
      category = stage2b.category;
    }

    // 6. Generate response
    const response = await generateResponse({
      category,
      problem: current_problem,
      student_input: message,
      attempt_count: session.current_problem.attempt_count + 1,
      chat_history: formatChatHistory(session.recent_turns)
    });

    // 7. Update session
    const turn = {
      student_input: message,
      is_answer: stage1.is_answer,
      category,
      verification,
      tutor_response: response,
      latency_ms: Date.now() - startTime
    };
    session = updateSession(session, turn, current_problem);
    sessions.set(session_id, session);

    // 8. Return response
    res.json({
      response,
      metadata: {
        category,
        confidence: stage1.confidence,
        is_answer: stage1.is_answer,
        verification,
        attempt_count: session.current_problem.attempt_count,
        latency_ms: turn.latency_ms,
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    console.error('Tutor error:', error);
    res.status(500).json({
      response: "I'm having trouble right now. Could you try again?",
      metadata: { error: true }
    });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Tutor API running on port ${PORT}`));
```

### 2. LLM Service Wrapper

```javascript
// services/openai.js

const OpenAI = require('openai');
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

async function callLLM(prompt, options = {}) {
  const response = await openai.chat.completions.create({
    model: options.model || 'gpt-4o-mini',
    messages: [{ role: 'user', content: prompt }],
    temperature: options.temperature || 0.7,
    max_tokens: options.max_tokens || 150
  });

  return response.choices[0].message.content;
}

module.exports = { callLLM };
```

### 3. Deploy to Production

**Option A: Heroku**
```bash
git init
git add .
git commit -m "Initial commit"
heroku create your-tutor-api
git push heroku main
```

**Option B: AWS Lambda + API Gateway**
- Use Serverless Framework
- Auto-scaling
- Pay per request

**Option C: DigitalOcean App Platform**
- Push to GitHub
- Auto-deploy on push
- $5/mo minimum

---

## Redis Configuration (All Options)

### Redis Cloud (Managed)

1. Sign up: https://redis.com/try-free/
2. Create database
3. Get connection details:
   ```
   Host: redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com
   Port: 12345
   Password: your_password
   ```

### In n8n:
- Add Redis credential
- Use in **Set/Get nodes** for session storage

### In Node.js:
```javascript
const redis = require('redis');
const client = redis.createClient({
  url: process.env.REDIS_URL,
  password: process.env.REDIS_PASSWORD
});

await client.connect();

// Save session
await client.set(`session:${session_id}`, JSON.stringify(session), {
  EX: 1800 // 30 minute TTL
});

// Load session
const data = await client.get(`session:${session_id}`);
const session = JSON.parse(data);
```

---

## Monitoring & Logging

### n8n Built-in

- Executions tab shows all runs
- Click execution → see node-by-node data
- Filter by status (success, error, running)

### External Monitoring (Production)

**1. Uptime Monitoring**
```bash
# UptimeRobot (free)
# Monitor: https://your-n8n.com/webhook/health
# Alert if down > 5 minutes
```

**2. Error Tracking**
```javascript
// Sentry integration
const Sentry = require('@sentry/node');
Sentry.init({ dsn: process.env.SENTRY_DSN });

// In error handlers
Sentry.captureException(error);
```

**3. Latency Monitoring**
```javascript
// Log slow requests
if (latency_ms > 3500) {
  console.warn('Slow request:', { session_id, latency_ms, category });
}
```

**4. Dashboards**
- Grafana + Prometheus
- Datadog
- New Relic

---

## Backup & Recovery

### n8n Workflows

**Export regularly**:
```bash
# In n8n UI: Settings → Export Workflow
# Save to version control
git add workflow.json
git commit -m "Backup workflow"
```

### Session Data (Redis)

**Redis persistence**:
```bash
# redis.conf
save 900 1
save 300 10
save 60 10000
```

**Backup script**:
```bash
#!/bin/bash
# backup-redis.sh

DATE=$(date +%Y-%m-%d)
redis-cli --rdb /backups/redis-$DATE.rdb
```

### Database (if using MongoDB)

```bash
# mongodump
mongodump --out /backups/mongo-$(date +%Y-%m-%d)
```

---

## Scaling

### When to Scale

**Metrics to watch**:
- Latency P95 > 3.5s
- Error rate > 1%
- CPU/RAM > 80%
- Request queue growing

### Horizontal Scaling (n8n)

**n8n Cloud**: Auto-scales automatically

**Self-hosted**:
1. Deploy multiple n8n instances
2. Use load balancer (Nginx, HAProxy)
3. Share Redis for sessions

```nginx
# nginx.conf

upstream n8n_backend {
    server n8n-1:5678;
    server n8n-2:5678;
    server n8n-3:5678;
}

server {
    location / {
        proxy_pass http://n8n_backend;
    }
}
```

### Vertical Scaling

**Increase resources**:
- 2GB → 4GB RAM
- 1 CPU → 2 CPUs

Helps with:
- Concurrent requests
- Larger session storage
- Faster LLM calls

---

## Security Checklist

- [ ] **HTTPS enabled** (SSL certificate)
- [ ] **Webhook authentication** (Bearer token)
- [ ] **Environment variables** (no secrets in code)
- [ ] **Rate limiting** (60 req/min per student)
- [ ] **Input validation** (sanitize all inputs)
- [ ] **CORS configured** (whitelist MinS domains only)
- [ ] **Redis password** set
- [ ] **n8n admin password** strong (16+ chars)
- [ ] **Firewall rules** (only ports 80, 443, 22 open)
- [ ] **Logs scrubbed** (no PII or secrets)
- [ ] **Backups encrypted**

---

## Cost Estimation

### Monthly Costs

**Option 1: n8n Cloud**
- n8n Starter: $20/mo
- Redis Cloud (free tier): $0
- OpenAI API (1000 students × 10 turns): ~$3
- **Total**: ~$23/mo

**Option 2: Self-Hosted**
- VPS (2GB RAM): $10/mo
- Redis Cloud (free tier): $0
- OpenAI API: ~$3
- **Total**: ~$13/mo

**Option 3: Node.js on Heroku**
- Dyno (1×): $7/mo
- Redis add-on: $0 (free tier)
- OpenAI API: ~$3
- **Total**: ~$10/mo

**At Scale** (10,000 students):
- OpenAI API: ~$30/mo
- Infrastructure: +$50-100/mo (more servers)
- **Total**: ~$80-130/mo

---

## Troubleshooting

### "Workflow not executing"
- Check n8n is running: `docker ps` or n8n.cloud status
- Check webhook URL is correct
- Check credentials are configured

### "High latency (> 5s)"
- Check OpenAI API status
- Check Redis connection
- Review n8n execution logs for bottlenecks
- Consider caching common responses

### "Session data lost"
- Check Redis persistence is enabled
- Check Redis TTL settings (should be 1800s)
- Verify session_id is consistent across requests

---

## Next Steps

1. **Choose deployment option** (n8n Cloud recommended for MVP)
2. **Deploy prototype** (follow steps above)
3. **Integrate with MinS** (see INTEGRATION.md)
4. **Monitor performance** (set up alerts)
5. **Plan migration** (to Node.js for long-term)

---

**Version**: 1.0
**Last Updated**: October 10, 2025
**Support**: See INTEGRATION.md for troubleshooting
