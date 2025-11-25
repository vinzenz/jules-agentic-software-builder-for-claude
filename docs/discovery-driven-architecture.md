# Discovery-Driven Orchestration Architecture

## Executive Summary

Instead of predefined workflows with 40 agents, the system **discovers what's needed** during execution. Agents spawn only what's required, ask users only when uncertain, and skip everything else.

**Result**: 6-10 agents instead of 40 (85% reduction), with user control at key decision points.

## Design Principles

### 1. Hybrid User Interaction
- PM asks high-level questions upfront (platform, complexity, key features)
- Specialized architects ask only when uncertain
- Sensible defaults for everything - user can override

### 2. Domain-Driven Specialist Spawning
- Spawn specialists based on project type analysis
- Web project: 3-4 specialists
- Full-stack: 5-6 specialists
- Enterprise/complex: 8-10 specialists

### 3. Confidence-Level Decisions
| Level | Behavior | Example |
|-------|----------|---------|
| HIGH | Proceed silently | "Using TypeScript (industry standard)" |
| MEDIUM | State decision, allow override | "Going with React. Say 'use vue' to change." |
| LOW | Ask user | "Auth adds complexity. Include it? [yes/no]" |

### 4. Hard Skip
If an architect says "skip DEV_UI_MOBILE", it's never spawned. No soft skips.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                           PM                                 │
│                                                              │
│  1. Analyze project idea                                     │
│  2. Classify project type                                    │
│  3. Ask HIGH-IMPACT questions (hybrid)                       │
│  4. Output: spawn_next = [specialists needed]                │
└─────────────────────────────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│architect-system │ │architect-frontend│ │architect-backend│
│                 │ │                 │ │                 │
│ Overall design  │ │ UI decisions    │ │ API decisions   │
│ Tech stack      │ │ spawn: DEV_UI_* │ │ spawn: DEV_CORE_│
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                  │                  │
         │          ┌───────┴───────┐          │
         │          ▼               ▼          │
         │    [DEV_UI_WEB]    [Skip mobile]    │
         │                                     │
         └──────────────────┬──────────────────┘
                            ▼
                    [DEV_CORE_API]
                            │
                            ▼
              (Continue based on spawn_next)
```

---

## Agent Output Schema

Every agent outputs a structured response:

```json
{
  "summary": "What I did",
  "confidence": "high|medium|low",

  "artifacts": [
    {"path": "src/file.py", "action": "created"}
  ],

  "decisions": [
    {
      "decision": "Using React 18 with TypeScript",
      "confidence": "high",
      "reason": "Industry standard, large ecosystem",
      "alternatives": ["vue", "svelte"]
    }
  ],

  "spawn_next": [
    {
      "agent": "DEV_UI_WEB",
      "reason": "Implement React components",
      "priority": "required",
      "context": {"framework": "react", "typescript": true}
    }
  ],

  "skip_agents": [
    {
      "agent": "DEV_UI_MOBILE",
      "reason": "User chose web-only"
    },
    {
      "agent": "DEV_PLATFORM_IOS",
      "reason": "No mobile platform needed"
    }
  ],

  "ask_user": [
    {
      "id": "include_auth",
      "question": "Include user authentication?",
      "confidence": "low",
      "context": "Adds login/signup, JWT tokens, protected routes",
      "options": [
        {"value": "yes", "description": "Full auth with login/signup"},
        {"value": "no", "description": "Skip for MVP, add later"}
      ],
      "recommendation": "no",
      "reason": "Simpler MVP"
    }
  ],

  "warnings": ["API design may need revision after frontend implementation"]
}
```

---

## Specialized Architects

### architect-system (Always First)

**Role**: Overall system design, tech stack decisions, coordinates other architects

**Outputs**:
- System architecture overview
- Tech stack decisions (with confidence levels)
- Which specialized architects to spawn

**Spawns Based On**:
| Project Type | Spawns |
|--------------|--------|
| Web app | architect-frontend, architect-backend |
| Mobile app | architect-mobile, architect-backend |
| Full-stack | architect-frontend, architect-backend, architect-mobile |
| CLI tool | architect-cli |
| Library | architect-library |
| Embedded | architect-embedded |

### architect-frontend

**Role**: UI architecture for web/desktop

**Decisions**:
- Framework (React/Vue/Svelte/Angular)
- State management
- Styling approach
- Component structure

**Spawns**: DEV_UI_WEB, DEV_UI_DESKTOP (based on platforms)

**Skips**: DEV_UI_MOBILE (if mobile not needed)

### architect-backend

**Role**: API and services architecture

**Decisions**:
- Framework (FastAPI/Express/Go/Rust)
- API style (REST/GraphQL/gRPC)
- Database choice
- Auth approach

**Spawns**: DEV_CORE_API, DEV_INTEGRATION_DATABASE (if complex)

**Skips**: DEV_CORE_SYSTEMS (if not low-level)

### architect-mobile

**Role**: Mobile app architecture (only spawned if mobile needed)

**Decisions**:
- Approach (native/cross-platform)
- Framework (React Native/Flutter/native)
- Platform targets

**Spawns**: DEV_UI_MOBILE, DEV_PLATFORM_IOS, DEV_PLATFORM_ANDROID

### architect-data

**Role**: Data architecture (only for complex data needs)

**Decisions**:
- Database type (SQL/NoSQL/embedded)
- Schema design
- Data access patterns

**Spawns**: DEV_INTEGRATION_DATABASE

### architect-infrastructure

**Role**: Deployment and DevOps (only for complex deployments)

**Decisions**:
- Containerization
- CI/CD approach
- Cloud provider

**Spawns**: DOE

---

## PM Project Analysis

PM performs initial analysis and asks hybrid questions:

```
PROJECT ANALYSIS
================

Project Type: Web Application
Complexity: Medium
Estimated Agents: 6-8

DETECTED NEEDS:
✓ Frontend (web)
✓ Backend (API)
✓ Database (simple)
✗ Mobile (not mentioned)
✗ Desktop (not mentioned)
✗ Hardware integration (not mentioned)

HIGH-IMPACT QUESTIONS (please answer):

1. Authentication needed?
   Context: Adds user accounts, login/signup, JWT
   Recommendation: NO (simpler MVP)
   [yes / NO]

2. Target platforms?
   Recommendation: WEB ONLY
   [WEB_ONLY / web+mobile / web+desktop / all]

3. Deployment complexity?
   Recommendation: SIMPLE (single server)
   [SIMPLE / containerized / kubernetes]

Press ENTER to accept recommendations, or type your choices:
```

---

## Confidence Level Examples

### HIGH Confidence (proceed silently)
```json
{
  "decision": "Using TypeScript",
  "confidence": "high",
  "reason": "Industry standard for React projects, better tooling"
}
```
Agent proceeds without asking.

### MEDIUM Confidence (state + allow override)
```json
{
  "decision": "Using PostgreSQL",
  "confidence": "medium",
  "reason": "Good default for web apps",
  "override_prompt": "Using PostgreSQL. Say 'use mysql' or 'use sqlite' to change."
}
```
Agent states decision, continues, user can interrupt.

### LOW Confidence (ask user)
```json
{
  "ask_user": {
    "question": "Include real-time features (WebSockets)?",
    "confidence": "low",
    "reason": "Could be useful but adds complexity",
    "options": ["yes", "no"],
    "recommendation": "no"
  }
}
```
Agent waits for user response.

---

## Execution Flow Example

### Input: "Build a todo app"

```
PHASE 1: PM Analysis
====================
PM: Analyzing "Build a todo app"...

Project Type: Simple Web Application
Complexity: Low
Recommended Agents: 5

Questions (ENTER for defaults):
• Auth? [yes/NO]
• Platforms? [WEB_ONLY/mobile/desktop]
• Deployment? [SIMPLE/docker]

User: <ENTER>

PM Decision: Web-only, no auth, simple deployment
Spawning: architect-system

PHASE 2: System Architecture
============================
architect-system: Designing overall system...

Decisions (HIGH confidence - proceeding):
• Monorepo structure
• React frontend + FastAPI backend
• SQLite database (simple, no setup)

Spawning: architect-frontend, architect-backend
Skipping: architect-mobile, architect-data (not needed)

PHASE 3: Specialized Architecture (PARALLEL)
============================================
architect-frontend: Designing React app...
  Decision (HIGH): TypeScript + Tailwind
  Decision (MEDIUM): Using Zustand for state. Override? [continue]
  Spawning: DEV_UI_WEB
  Skipping: DEV_UI_MOBILE, DEV_UI_DESKTOP

architect-backend: Designing FastAPI API...
  Decision (HIGH): REST with Pydantic models
  Decision (HIGH): SQLite with SQLAlchemy (inline, no separate DB agent)
  Spawning: DEV_CORE_API
  Skipping: DEV_INTEGRATION_DATABASE (handled inline)

PHASE 4: Implementation (PARALLEL)
==================================
DEV_UI_WEB: Implementing React frontend...
  → Created: src/App.tsx, src/components/...
  → Done

DEV_CORE_API: Implementing FastAPI backend...
  → Created: src/api/main.py, src/api/routes/...
  → Done

PHASE 5: Finalization
=====================
architect-system: All components complete.
  Question (MEDIUM): Generate tests? [YES/no]

User: yes

Spawning: TEST

TEST: Generating tests...
  → Done

COMPLETE
========
Agents run: 6 (PM, architect-system, architect-frontend, architect-backend, DEV_UI_WEB, DEV_CORE_API, TEST)
Agents skipped: 32
Time: ~8 minutes
```

---

## Skip Propagation

When an agent skips downstream agents, it propagates:

```
architect-system skips architect-mobile
  → architect-mobile never runs
  → Therefore DEV_UI_MOBILE never runs
  → Therefore DEV_PLATFORM_IOS never runs
  → Therefore DEV_PLATFORM_ANDROID never runs

Total skip: 4 agents from 1 decision
```

---

## Implementation Components

### 1. Adaptive Orchestrator Skill
- No predefined workflow
- Reads spawn_next from each agent
- Handles ask_user interactions
- Tracks skipped agents

### 2. Specialized Architect Agents
- architect-system.md
- architect-frontend.md
- architect-backend.md
- architect-mobile.md
- architect-data.md
- architect-infrastructure.md

### 3. Updated PM Agent
- Project type classification
- Hybrid questioning
- Initial specialist spawning

### 4. Decision Tracker
- Logs all decisions with confidence
- Allows post-hoc review
- Supports "why did you choose X?"

---

## Comparison

| Metric | Fixed Workflow | Discovery-Driven |
|--------|---------------|------------------|
| Agents for simple web app | 40 | 6-8 |
| Agents for mobile app | 40 | 10-12 |
| Agents for CLI tool | 40 | 4-5 |
| User questions | 0 | 2-5 (high-impact only) |
| Wasted agent runs | 20-30 | 0 |
| Adaptability | None | Full |
| Time for simple app | 80+ min | ~8 min |
