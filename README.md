# AI Tutor POC - Adaptive Math Tutoring System

**Delivery Date**: October 8-10, 2025
**Budget**: $1,000 fixed (10 hours)
**Client**: MinS Education Platform

## Overview

This repository contains a complete proof-of-concept for an adaptive AI tutoring system that demonstrates:
- Intelligent student response classification (6 categories)
- Answer verification with edge case handling
- Multi-turn conversation memory
- Attempt-based pedagogical escalation
- Socratic teaching methodology

## Project Structure

```
ai-tutor-poc/
├── README.md                          # This file
├── SUMMARY.md                         # Executive summary for stakeholders
│
├── 1-blueprint/                       # Architectural design documents
│   ├── Tutoring-Flow-Blueprint.md     # Complete specification (~10 pages)
│   ├── diagrams/                      # Visual architecture
│   └── prompts/                       # 6 prompt templates (YAML)
│
├── 2-prototype/                       # Working implementation
│   ├── README.md                      # Setup and testing guide
│   ├── workflow.json                  # n8n workflow (importable)
│   ├── functions/                     # JavaScript functions for n8n
│   ├── exemplars/                     # Test questions
│   └── docs/                          # Technical documentation
│
└── 3-delivery/                        # Handoff materials
    ├── CHANGELOG.md                   # Development decisions
    ├── KNOWN-LIMITATIONS.md           # Prototype constraints
    └── HANDOFF-CHECKLIST.md           # For dev team
```

## Quick Start

### Blueprint (Design Documents)
Review the complete architectural specification:
- **[Tutoring Flow Blueprint](1-blueprint/Tutoring-Flow-Blueprint.md)** - Full system design
- **[Prompt Library](1-blueprint/prompts/)** - 6 production-ready templates
- **[Exemplar Questions](2-prototype/exemplars/questions.json)** - Fully specified test questions

### Prototype (Working Demo)
See the working implementation:
- **[Setup Instructions](2-prototype/README.md)** - How to run the prototype
- **[API Specification](2-prototype/docs/API-SPEC.md)** - Webhook integration contract
- **[Integration Guide](2-prototype/docs/INTEGRATION.md)** - Connect to your platform

## Key Features

### Two-Stage Triage System
1. **Stage 1**: Classify intent (answer attempt vs question/help request)
2. **Stage 2a**: If answer → verify then classify quality (correct/close/wrong)
3. **Stage 2b**: If not answer → classify type (conceptual/stuck/off-topic)

### Adaptive Responses
- **Attempt 1**: Encouraging probe, Socratic questioning
- **Attempt 2**: More explicit hints
- **Attempt 3+**: Direct teaching with worked examples

### Session Memory
- Maintains last 15 conversation turns
- Tracks attempt count per problem
- Detects error patterns
- 30-minute session TTL

## Technical Stack

- **Orchestration**: n8n (visual workflow)
- **LLM**: OpenAI GPT-4o-mini
- **Verification**: JavaScript (math.js)
- **Memory**: Redis or file storage
- **Prompts**: YAML templates (LangChain-compatible)

## Performance

- **Target Latency**: ≤3.5 seconds per turn
- **Actual Average**: ~1.5 seconds
- **Cost**: ~$0.0003 per turn (~$3/month for 10k turns)

## Deliverables

1. **Blueprint Document** (~10 pages)
   - Complete architectural specification
   - Triage system design
   - 6 prompt templates
   - 7-10 exemplar questions
   - Integration patterns

2. **Working Prototype**
   - Importable n8n workflow
   - Demonstrates all 6 categories
   - Multi-turn adaptive conversations
   - Validated latency performance

3. **Documentation**
   - API specification
   - Integration guide
   - Deployment recommendations
   - Future roadmap (RAG, agents, tools)

## Next Steps (Phase 2)

After reviewing this POC:
1. Integration with MinS text module
2. Migration from n8n to Node.js/MERN stack
3. Database persistence (MongoDB)
4. Knowledge base integration (RAG)
5. Multi-step problem decomposition (agents)
6. Production deployment

## Contact

For questions about this POC, refer to the handoff documentation in `3-delivery/`.

---

**Status**: Phase 1 Delivery Complete
**Version**: 1.0
**Last Updated**: October 10, 2025
