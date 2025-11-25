# Single Orchestrator Architecture

## Executive Summary

A radical simplification: **one persistent Claude CLI session** acts as the orchestrator, using the Task tool to spawn agents in parallel. Agents return only task IDs. All context lives on disk.

## The Problem with Multi-Process Architecture

Current approach spawns 40+ separate Claude CLI processes:

```
Process 1: claude --model opus ... (PM)
Process 2: claude --model opus ... (ARCHITECT)
Process 3: claude --model sonnet ... (UIUX_GUI)
...
Process 40: claude --model haiku ... (DOE)
```

**Issues:**
- 40x CLI startup overhead (~2-3s each = 80-120s total)
- 40x model loading overhead
- No shared state between processes
- Context must be serialized/deserialized for each agent

## The Single Orchestrator Model

```
+-------------------------------------------------------------+
|                    ORCHESTRATOR                              |
|                 (Single Claude CLI Session)                  |
|                                                              |
|  Responsibilities:                                           |
|  1. Load workflow configuration                              |
|  2. Compute execution phases (dependency resolution)         |
|  3. Spawn agents in parallel via Task tool                   |
|  4. Receive minimal completion signals                       |
|  5. Update manifest and continue                             |
|  6. Handle errors and retries                                |
+-------------------------------------------------------------+
                           |
           +---------------+---------------+
           |               |               |
           v               v               v
      +---------+    +---------+    +---------+
      | Task:PM |    |Task:ARCH|    |Task:TL  |
      |(spawned)|    |(spawned)|    |(spawned)|
      +----+----+    +----+----+    +----+----+
           |               |               |
           |    +----------+----------+    |
           |    |                     |    |
           v    v                     v    v
      +----------------------------------------+
      |              .tasks/                    |
      |  manifest.json                          |
      |  PM/output.json                         |
      |  ARCHITECT/output.json                  |
      |  ...                                    |
      +----------------------------------------+
```

## Key Design Principles

### 1. Minimal Token Returns

Agents return ONLY a completion signal:

```xml
&lt;task_complete&gt;
  &lt;id&gt;DEV_UI_WEB&lt;/id&gt;
  &lt;status&gt;success&lt;/status&gt;
&lt;/task_complete&gt;
```

**~15 tokens** instead of **~500 tokens**

All detailed output (summary, artifacts, warnings) goes to `.tasks/{AGENT}/output.json`

### 2. Context on Disk, Not in Tokens

Agents don't receive context in prompts. They read it from disk:

```python
# Agent reads its context
manifest = read_json(".tasks/manifest.json")
project_idea = manifest["project_idea"]
tl_output = read_json(".tasks/TL_UI_WEB/output.json")
arch_decisions = read_json(".tasks/ARCHITECT/decisions.json")
```

### 3. Parallel Spawning via Task Tool

The orchestrator spawns multiple agents in a single message using Task tool.
All agents in a phase run concurrently. The orchestrator waits for all to complete.

## Token Analysis

### Current Architecture (40 CLI invocations)

| Component | Tokens |
|-----------|--------|
| Per-agent system prompt | 1,000 |
| Per-agent context | 50 (minimal) |
| Per-agent output | 500 |
| **Per agent total** | **1,550** |
| **40 agents total** | **62,000** |

Plus: 40x CLI startup overhead

### Single Orchestrator Architecture

| Component | Tokens |
|-----------|--------|
| Orchestrator skill (once) | 500 |
| Manifest loading (once) | 200 |
| Per-agent spawn prompt | 50 |
| Per-agent return | 15 |
| **Orchestration total** | **700 + (40 x 65) = 3,300** |

**Orchestration token reduction: 95%**

Note: Agents still consume tokens for their actual work (reading files, generating code).
The savings is in orchestration overhead, not agent execution.

## Implementation Components

### 1. Orchestrator Skill

Located at `.claude/skills/workflow-orchestrator/SKILL.md`:

```markdown
# Workflow Orchestrator Skill

You are the workflow orchestrator. You manage the execution of a multi-agent
software development workflow.

## Your Responsibilities

1. Read `.tasks/manifest.json` to understand the workflow state
2. Determine which agents can run (dependencies satisfied)
3. Spawn agents in parallel using the Task tool
4. Wait for completion signals
5. Update the manifest
6. Repeat until workflow complete

## Agent Spawning Pattern

For each ready agent, use the Task tool with:
- subagent_type: The agent's sub-agent definition (e.g., "pm-agent")
- prompt: "Execute {AGENT_TYPE}. Return: done:{AGENT_TYPE}:success or done:{AGENT_TYPE}:failed"

Spawn all ready agents in a SINGLE message with multiple Task invocations.

## Completion Handling

Agents return minimal signals like: done:PM:success
Parse these and update .tasks/manifest.json accordingly.

## Error Handling

If an agent returns failed, check .tasks/{AGENT}/error.json for details.
Decide whether to retry, skip, or abort the workflow.
```

### 2. Agent Sub-Agent Definitions

Each main agent becomes a sub-agent. Example `.claude/agents/dev-ui-web.md`:

```markdown
---
name: dev-ui-web
description: Web UI Developer - implements frontend code
tools: [Read, Write, Edit, Glob, Grep, Bash]
model: haiku
---

# DEV_UI_WEB Agent

You implement web frontend code based on specifications.

## Context Loading

1. Read `.tasks/manifest.json` for project idea
2. Read `.tasks/TL_UI_WEB/output.json` for your instructions
3. Read `.tasks/ARCHITECT/decisions.json` for tech stack

## Execution

1. Implement the frontend code per specifications
2. Write files to the project directory
3. Write your output to `.tasks/DEV_UI_WEB/output.json`:
   ```json
   {
     "summary": "...",
     "artifacts": ["src/App.tsx", "src/components/..."],
     "next_steps": [...],
     "warnings": [...]
   }
   ```

## Return Value

Return ONLY: done:DEV_UI_WEB:success

Or on failure: done:DEV_UI_WEB:failed
```

### 3. Manifest Schema

```json
{
  "session_id": "abc123",
  "workflow": "FULL_APP_GENERATION",
  "project_idea": "Build a todo app with React and FastAPI",
  "created_at": "2024-01-15T10:00:00Z",

  "agents": {
    "PM": {
      "dependencies": [],
      "model": "opus",
      "status": "completed"
    },
    "ARCHITECT": {
      "dependencies": ["PM"],
      "model": "sonnet",
      "status": "completed"
    },
    "TL_UI_WEB": {
      "dependencies": ["ARCHITECT", "UIUX_GUI"],
      "model": "sonnet",
      "status": "in_progress"
    },
    "DEV_UI_WEB": {
      "dependencies": ["TL_UI_WEB"],
      "model": "haiku",
      "status": "pending"
    }
  },

  "phases": [
    {"phase": 1, "agents": ["PM"], "status": "completed"},
    {"phase": 2, "agents": ["ARCHITECT", "UIUX_GUI"], "status": "completed"},
    {"phase": 3, "agents": ["TL_UI_WEB", "TL_CORE_API"], "status": "in_progress"},
    {"phase": 4, "agents": ["DEV_UI_WEB", "DEV_CORE_API"], "status": "pending"}
  ]
}
```

## Execution Flow

```
1. User: agentic-builder run FULL_APP_GENERATION --idea "..."

2. Python CLI:
   - Creates .tasks/ directory
   - Writes manifest.json with workflow config
   - Invokes: claude --skill workflow-orchestrator

3. Orchestrator (single Claude session):

   [Turn 1]
   - Reads manifest
   - Phase 1: Spawns PM agent
   - PM does work, writes to .tasks/PM/, returns "done:PM:success"

   [Turn 2]
   - Updates manifest (PM completed)
   - Phase 2: Spawns ARCHITECT and UIUX_GUI in parallel
   - Both return "done:X:success"

   [Turn 3]
   - Updates manifest
   - Phase 3: Spawns TL_UI_WEB, TL_CORE_API, etc. in parallel
   - All return completion signals

   [Turn 4-N]
   - Continue until all agents complete

   [Final Turn]
   - Updates manifest (workflow completed)
   - Returns final status

4. Python CLI:
   - Commits all changes
   - Creates PR
```

## Performance Comparison

| Metric | Multi-Process | Single Orchestrator | Improvement |
|--------|---------------|---------------------|-------------|
| CLI startups | 40 | 1 | 40x |
| Orchestration tokens | 62,000 | 3,300 | 19x |
| Context serialization | 40 times | 0 | Eliminated |
| State management | File I/O per agent | In-memory | Faster |
| Error recovery | Complex | Natural (same session) | Simpler |

## Caveats and Considerations

### Context Window

The orchestrator session accumulates context. Mitigation:
- Minimal return values (~15 tokens per agent)
- No detailed outputs in conversation
- Total orchestration: ~3,300 tokens (well within limits)

### Agent Isolation

Agents run as sub-agents with their own context. They:
- Cannot see the orchestrator's conversation
- Read/write only via files
- Return only completion signals

### Task Tool Behavior

The Task tool spawns sub-agents that:
- Have access to defined tools
- Run with specified model tier
- Return a single response to the orchestrator

### Failure Handling

If an agent fails:
1. Returns "done:AGENT:failed"
2. Writes details to `.tasks/AGENT/error.json`
3. Orchestrator can retry, skip, or abort

## Migration Path

1. Create sub-agent definitions for all 38 main agents
2. Create orchestrator skill
3. Update CLI to invoke orchestrator instead of spawning processes
4. Keep existing infrastructure for backwards compatibility
