# Performance Optimization Architecture

## Executive Summary

This document outlines a comprehensive performance optimization strategy for the Agentic Builder framework. The goal is to reduce end-to-end workflow time from **80+ minutes to under 15 minutes** for a full app generation workflow.

## Current Bottlenecks Analysis

| Bottleneck | Current Impact | Severity |
|------------|----------------|----------|
| Sequential agent execution | 80+ min for 40 agents | **CRITICAL** |
| Full context passed to every agent | Growing token usage (15K+ tokens) | HIGH |
| No caching of intermediate results | Redundant file I/O | MEDIUM |
| Git commit after every agent | 40 sequential git operations | MEDIUM |
| Opus model for simple tasks | Slow response times | HIGH |
| XML serialization overhead | Token waste | LOW |

---

## Optimization Strategy 1: Task File Store (TASKS Directory)

### Concept

Replace in-memory context passing with a **file-based task store**. Each agent's output is persisted to disk in a structured format that subsequent agents can read directly.

### Directory Structure

```
project_root/
├── .tasks/                           # Task file store (gitignored)
│   ├── manifest.json                 # Session manifest with task registry
│   ├── PM/
│   │   ├── output.json               # Structured output (summary, next_steps, warnings)
│   │   ├── artifacts.json            # List of created file paths
│   │   └── context.md                # Human-readable context for debugging
│   ├── ARCHITECT/
│   │   ├── output.json
│   │   ├── artifacts.json
│   │   └── decisions.json            # Architectural decisions for downstream agents
│   ├── TL_UI_WEB/
│   │   └── ...
│   └── ...
├── src/                              # Actual project files
└── ...
```

### Manifest Schema

```json
{
  "session_id": "abc123",
  "workflow": "FULL_APP_GENERATION",
  "project_idea": "Build a todo app with React and FastAPI",
  "created_at": "2024-01-15T10:00:00Z",
  "tasks": {
    "PM": {
      "status": "completed",
      "started_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:02:30Z",
      "tokens_used": 1500,
      "output_path": ".tasks/PM/output.json"
    },
    "ARCHITECT": {
      "status": "completed",
      "dependencies": ["PM"],
      "started_at": "2024-01-15T10:02:31Z",
      "completed_at": "2024-01-15T10:05:00Z"
    }
  },
  "completed": ["PM", "ARCHITECT"],
  "in_progress": ["TL_UI_WEB", "TL_CORE_API"],
  "pending": ["DEV_UI_WEB", "DEV_CORE_API", "TEST"]
}
```

### Benefits

- **Zero token overhead**: Agents read only what they need from disk
- **Debuggability**: All context is inspectable in plain files
- **Resume support**: Session state survives crashes
- **Parallel safety**: File locks prevent race conditions

---

## Optimization Strategy 2: Minimal Context Injection

### Current Approach (Expensive)

```xml
<task_context>
  <project_idea>Build a todo app with React...</project_idea>
  <task_id>task-123</task_id>
  <dependencies>
    <dependency id="pm-task" agent="PM">
      <summary>Long summary of PM output...</summary>
      <artifacts>
        <artifact path="docs/requirements.md"/>
        <artifact path="docs/user-stories.md"/>
        <!-- 20+ more artifacts -->
      </artifacts>
      <next_steps>
        <step>Step 1...</step>
        <!-- 10+ steps -->
      </next_steps>
    </dependency>
    <!-- More dependencies with full output -->
  </dependencies>
</task_context>
```

**Token cost**: 2,000-15,000 tokens per agent invocation

### New Approach (Minimal)

```xml
<task>
  <id>DEV_UI_WEB</id>
  <manifest>.tasks/manifest.json</manifest>
  <read_from>PM, ARCHITECT, TL_UI_WEB</read_from>
</task>
```

**Token cost**: ~50 tokens per agent invocation

### Agent Instructions

Agents are instructed to:
1. Read `.tasks/manifest.json` to understand session state
2. Read `.tasks/{AGENT}/output.json` for each dependency they need
3. Read actual source files from disk when needed
4. Write their output to `.tasks/{AGENT}/output.json`

### Implementation

```python
class MinimalContextSerializer:
    @staticmethod
    def serialize(agent_type: AgentType, dependencies: List[AgentType]) -> str:
        """Generate minimal context pointer (< 100 tokens)."""
        deps_str = ", ".join(d.value for d in dependencies)
        return f"""<task>
  <agent>{agent_type.value}</agent>
  <manifest>.tasks/manifest.json</manifest>
  <dependencies>{deps_str}</dependencies>
</task>"""
```

---

## Optimization Strategy 3: Parallel Agent Execution

### Dependency Graph Analysis

```
                    ┌─────┐
                    │ PM  │
                    └──┬──┘
                       │
                 ┌─────┴─────┐
                 ▼           ▼
            ┌─────────┐  ┌─────────┐
            │ARCHITECT│  │ UIUX_*  │
            └────┬────┘  └────┬────┘
                 │            │
    ┌────────────┼────────────┼────────────┐
    ▼            ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│TL_UI_* │  │TL_CORE_│  │TL_PLAT_│  │TL_INT_ │
└───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘
    │           │           │           │
    ▼           ▼           ▼           ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│DEV_UI_*│  │DEV_CORE│  │DEV_PLAT│  │DEV_INT_│
└────────┘  └────────┘  └────────┘  └────────┘
    │           │           │           │
    └───────────┴─────┬─────┴───────────┘
                      ▼
                 ┌─────────┐
                 │  TEST   │
                 └────┬────┘
                      ▼
                 ┌─────────┐
                 │   CQR   │
                 └────┬────┘
                      ▼
                 ┌─────────┐
                 │   SR    │
                 └─────────┘
```

### Parallelization Opportunities

| Phase | Agents That Can Run in Parallel | Speedup |
|-------|--------------------------------|---------|
| 1 | PM | 1x |
| 2 | ARCHITECT, UIUX_GUI | 2x |
| 3 | TL_UI_WEB, TL_CORE_API, TL_PLATFORM_*, TL_INTEGRATION_* | 6x |
| 4 | DEV_UI_WEB, DEV_CORE_API, DEV_PLATFORM_*, DEV_INTEGRATION_* | 10x |
| 5 | TEST | 1x |
| 6 | CQR, SR | 2x |
| 7 | DOE | 1x |

### Async Execution Engine

```python
import asyncio
from typing import Set, Dict
from dataclasses import dataclass

@dataclass
class ExecutionPhase:
    agents: List[AgentType]

class ParallelWorkflowEngine:
    async def run_parallel(self, session_id: str):
        """Execute agents in parallel phases based on dependencies."""
        phases = self._compute_phases(session_id)

        for phase in phases:
            # Run all agents in this phase concurrently
            tasks = [
                self._execute_agent(agent, session_id)
                for agent in phase.agents
            ]
            await asyncio.gather(*tasks)

    def _compute_phases(self, session_id: str) -> List[ExecutionPhase]:
        """Group agents into phases where all agents in a phase can run in parallel."""
        workflow = self._get_workflow(session_id)
        completed: Set[AgentType] = set()
        phases: List[ExecutionPhase] = []
        remaining = set(workflow.agents)

        while remaining:
            # Find all agents whose dependencies are satisfied
            ready = [
                agent for agent in remaining
                if all(dep in completed for dep in agent.dependencies)
            ]

            if not ready:
                raise RuntimeError("Circular dependency detected")

            phases.append(ExecutionPhase(agents=ready))
            completed.update(ready)
            remaining -= set(ready)

        return phases

    async def _execute_agent(self, agent: AgentType, session_id: str):
        """Execute single agent with async Claude call."""
        # Use asyncio.subprocess for non-blocking Claude CLI calls
        process = await asyncio.create_subprocess_exec(
            "claude", "--model", agent.model.value,
            "--system-prompt", self._get_system_prompt(agent),
            "-p", self._get_task_prompt(agent),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        context = MinimalContextSerializer.serialize(agent, agent.dependencies)
        stdout, stderr = await process.communicate(context.encode())

        # Parse and store output
        self._store_task_output(agent, stdout.decode())
```

### Expected Speedup

| Scenario | Sequential Time | Parallel Time | Speedup |
|----------|-----------------|---------------|---------|
| 10 agents (2 min each) | 20 min | 6 min | 3.3x |
| 20 agents (2 min each) | 40 min | 10 min | 4x |
| 40 agents (2 min each) | 80 min | 14 min | 5.7x |

---

## Optimization Strategy 4: Aggressive Model Tier Downgrades

### Current Distribution

| Tier | Count | Use Case |
|------|-------|----------|
| Opus | 6 | PM, ARCHITECT, UIUX_GUI, TL_CONTENT, TL_GRAPHICS, SR |
| Sonnet | 32 | Everything else |
| Haiku | 0 | Unused for main agents |

### Proposed Distribution

| Tier | Count | Use Case | Rationale |
|------|-------|----------|-----------|
| Opus | 2 | PM, SR | Only for critical reasoning and security |
| Sonnet | 8 | ARCHITECT, UIUX_*, TL_* agents | Design decisions need good reasoning |
| Haiku | 28 | All DEV_* agents | Code generation is well-specified |

### Speed Comparison

| Model | Avg Response Time | Token Rate |
|-------|-------------------|------------|
| Opus | 45-120s | ~50 tok/s |
| Sonnet | 15-45s | ~100 tok/s |
| Haiku | 3-10s | ~200 tok/s |

### Expected Speedup from Model Downgrades

```
Current: (6 × 60s) + (32 × 30s) = 360 + 960 = 1320s = 22 min (model time only)
Proposed: (2 × 60s) + (8 × 30s) + (28 × 6s) = 120 + 240 + 168 = 528s = 8.8 min
Speedup: 2.5x
```

### Updated Agent Configs

```python
AGENT_MODEL_TIERS = {
    # Opus (2) - Critical reasoning only
    AgentType.PM: ModelTier.OPUS,
    AgentType.SR: ModelTier.OPUS,

    # Sonnet (8) - Design and architecture
    AgentType.ARCHITECT: ModelTier.SONNET,
    AgentType.UIUX_GUI: ModelTier.SONNET,
    AgentType.UIUX_CLI: ModelTier.SONNET,
    AgentType.TL_UI_WEB: ModelTier.SONNET,
    AgentType.TL_CORE_API: ModelTier.SONNET,
    AgentType.TL_CORE_SYSTEMS: ModelTier.SONNET,
    AgentType.TL_CORE_LIBRARY: ModelTier.SONNET,
    AgentType.TEST: ModelTier.SONNET,  # Test strategy needs reasoning

    # Haiku (everything else) - Implementation
    # All DEV_* agents
    # CQR, DOE
}
```

---

## Optimization Strategy 5: Batched Git Operations

### Current Approach

```python
# After EACH agent (40 times):
self.git.commit_files(created_files, commit_msg)
```

**Cost**: 40 sequential git operations × 0.5-2s each = 20-80s

### Optimized Approach: Phase-Based Commits

```python
class BatchedGitManager:
    def __init__(self):
        self.pending_files: List[str] = []
        self.pending_messages: List[str] = []

    def stage_files(self, files: List[str], agent: AgentType, summary: str):
        """Stage files for later commit."""
        self.pending_files.extend(files)
        self.pending_messages.append(f"[{agent.value}] {summary[:50]}")

    def commit_phase(self, phase_name: str):
        """Commit all staged files from a phase."""
        if not self.pending_files:
            return

        combined_message = f"[{phase_name}]\n\n" + "\n".join(self.pending_messages)
        self._git_add_and_commit(self.pending_files, combined_message)
        self.pending_files.clear()
        self.pending_messages.clear()
```

### Commit Strategy

| Phase | Agents | Commit |
|-------|--------|--------|
| Init | - | CLAUDE.md, manifest |
| Planning | PM | Requirements, specs |
| Architecture | ARCHITECT, UIUX_* | Design docs |
| Implementation | All TL_*, DEV_* | Source code |
| Quality | TEST, CQR, SR | Tests, reports |
| Ops | DOE | CI/CD, Docker |

**Result**: 6 commits instead of 40 → **85% reduction in git overhead**

---

## Optimization Strategy 6: Lazy Context Loading

### Concept

Instead of agents receiving all dependency outputs upfront, they request specific pieces of context on-demand.

### Implementation via System Prompt

```xml
<context_loading_instructions>
  Your context is stored in the .tasks/ directory.

  Available context:
  - .tasks/manifest.json - Session state and task registry
  - .tasks/PM/output.json - PM decisions and requirements
  - .tasks/ARCHITECT/output.json - Architecture decisions
  - .tasks/ARCHITECT/decisions.json - Tech stack, patterns

  Read ONLY what you need for your task. Do not read all files.

  For your role as DEV_UI_WEB, you likely need:
  1. .tasks/TL_UI_WEB/output.json - Your tech lead's instructions
  2. .tasks/ARCHITECT/decisions.json - Tech stack info

  You probably do NOT need:
  - PM output (already incorporated by ARCHITECT)
  - Platform-specific agent outputs (not your layer)
</context_loading_instructions>
```

### Benefits

- Agents self-select relevant context
- Reduces unnecessary file reads
- Keeps agent focus narrow

---

## Optimization Strategy 7: Sub-Agent Optimization

### Current Sub-Agent Issue

Sub-agents are invoked via the Task tool inside main agent runs. This creates:
- Nested Claude calls within Claude calls
- No parallelism within a main agent's sub-agent invocations

### Optimized Sub-Agent Execution

```python
class OptimizedSubAgentExecutor:
    async def execute_sub_agents(
        self,
        sub_agents: List[str],
        context: Dict
    ) -> Dict[str, str]:
        """Execute multiple sub-agents in parallel."""
        tasks = [
            self._call_sub_agent(name, context)
            for name in sub_agents
        ]
        results = await asyncio.gather(*tasks)
        return dict(zip(sub_agents, results))
```

### Sub-Agent Model Tiers (Already Optimized)

| Tier | Sub-Agents |
|------|------------|
| Opus | security-scanner, risk-assessor |
| Sonnet | *-analyzer, *-designer, *-evaluator |
| Haiku | *-generator (22 agents) |

---

## Combined Optimization Impact

### Time Breakdown

| Component | Current | Optimized | Savings |
|-----------|---------|-----------|---------|
| Model response time | 22 min | 8.8 min | 60% |
| Sequential → Parallel | 80 min | 14 min | 82% |
| Git operations | 1.5 min | 0.2 min | 87% |
| Context serialization | 0.5 min | 0.1 min | 80% |
| **Total** | **80+ min** | **~15 min** | **81%** |

### Token Usage

| Component | Current | Optimized | Savings |
|-----------|---------|-----------|---------|
| Context per agent | 5,000 avg | 50 avg | 99% |
| Total context tokens | 200,000 | 2,000 | 99% |
| Response overhead | Moderate | Low | ~30% |

---

## Implementation Phases

### Phase 1: Task File Store (Low Risk, High Impact)

1. Create `.tasks/` directory structure
2. Implement `TaskFileStore` class
3. Migrate `ContextSerializer` to write files
4. Update agents to read from `.tasks/`

### Phase 2: Parallel Execution (Medium Risk, Highest Impact)

1. Convert `run_loop` to async
2. Implement phase-based execution
3. Add file locking for parallel safety
4. Update progress reporting

### Phase 3: Model Tier Optimization (Low Risk, Medium Impact)

1. Update `AGENT_CONFIGS_MAP` with new tiers
2. Test Haiku performance on DEV_* agents
3. Validate output quality

### Phase 4: Batched Git (Low Risk, Low Impact)

1. Implement `BatchedGitManager`
2. Configure commit phases
3. Update workflow engine

---

## Monitoring & Observability

### Metrics to Track

```python
@dataclass
class WorkflowMetrics:
    total_time_seconds: float
    agent_times: Dict[str, float]
    parallel_efficiency: float  # actual_time / sequential_time
    token_usage: Dict[str, int]
    cache_hit_rate: float

    def report(self):
        print(f"Total time: {self.total_time_seconds:.1f}s")
        print(f"Parallel efficiency: {self.parallel_efficiency:.1%}")
        print(f"Slowest agent: {max(self.agent_times, key=self.agent_times.get)}")
```

---

## Conclusion

By implementing these optimizations:

1. **Task File Store** eliminates context token overhead (99% reduction)
2. **Parallel Execution** reduces wall-clock time by 5-6x
3. **Model Downgrades** speed up individual agent responses by 2.5x
4. **Batched Git** eliminates 85% of git overhead

**Expected Result**: Full app generation in **~15 minutes** instead of **80+ minutes**.
