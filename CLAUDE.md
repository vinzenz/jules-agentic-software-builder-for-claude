# CLAUDE.md - AI Assistant Guidelines


This document provides guidance for AI assistants working on the Jules Agentic Software Builder for Claude project.

## Project Overview

**Repository:** jules-agentic-software-builder-for-claude
**Name:** Agentic Builder
**Version:** 0.2.0
**Language:** Python 3.10+
**Purpose:** A generic agentic software builder tool designed to work with Claude AI for automated software development tasks across all project types (web, mobile, desktop, CLI, libraries, embedded, etc.).
**Status:** Active Development

## Architecture Documentation

For detailed architecture information, see:
- **[Agent Architecture](docs/architecture.md)** - Layer-based agent model, project type examples
- **[Sub-Agent Mappings](docs/sub-agent-mappings.md)** - Which sub-agents each main agent can delegate to
- **[Performance Optimization](docs/performance-optimization.md)** - Speed optimization strategies (5x faster)
- **[Orchestrator Architecture](docs/orchestrator-architecture.md)** - Single-session orchestrator design (8x faster)
- **[Discovery-Driven Architecture](docs/discovery-driven-architecture.md)** - Adaptive agent spawning (85% fewer agents)

## Codebase Structure

```
jules-agentic-software-builder-for-claude/
├── CLAUDE.md                    # AI assistant guidelines (this file)
├── README.md                    # Project documentation
├── pyproject.toml               # Python project configuration
├── .gitignore                   # Git ignore rules
├── docs/                        # Architecture documentation
│   ├── architecture.md          # Layer-based agent architecture
│   ├── sub-agent-mappings.md    # Sub-agent delegation mappings
│   ├── performance-optimization.md  # Speed optimization guide
│   ├── orchestrator-architecture.md # Single-session orchestrator design
│   └── discovery-driven-architecture.md  # Adaptive spawning design
├── .claude/                     # Claude Code configuration
│   ├── agents/                  # Sub-agent definitions (49 specialists + 14 new)
│   │   ├── main-*.md            # Main agent Task wrappers (8)
│   │   └── architect-*.md       # Specialized architects (6)
│   └── skills/                  # Reusable skills
│       ├── orchestrator/        # Base orchestrator pattern
│       ├── workflow-orchestrator/   # Single-session workflow skill
│       └── adaptive-orchestrator/   # Discovery-driven skill
├── agentic_builder/             # Main package
│   ├── __init__.py
│   ├── main.py                  # CLI entry point (Typer app)
│   ├── agents/                  # Agent configurations
│   │   ├── __init__.py
│   │   ├── configs.py           # Agent configs and dependency map
│   │   ├── fast_configs.py      # Speed-optimized configs (Haiku-heavy)
│   │   └── response_parser.py   # Claude response parsing
│   ├── common/                  # Shared utilities and types
│   │   ├── __init__.py
│   │   ├── events.py            # Event emitter system
│   │   ├── types.py             # Pydantic models and enums
│   │   └── utils.py             # Utility functions
│   ├── integration/             # External integrations
│   │   ├── __init__.py
│   │   ├── claude_client.py     # Claude CLI wrapper
│   │   ├── git_manager.py       # Git operations
│   │   ├── batched_git.py       # Phase-based git commits
│   │   └── pr_manager.py        # GitHub PR creation
│   ├── orchestration/           # Workflow management
│   │   ├── __init__.py
│   │   ├── session_manager.py   # Session persistence
│   │   ├── workflow_engine.py   # Sequential execution engine
│   │   ├── parallel_engine.py   # Async parallel execution (5x faster)
│   │   ├── single_session.py    # Single CLI orchestrator (8x faster)
│   │   ├── adaptive_orchestrator.py  # Discovery-driven orchestrator
│   │   └── workflows.py         # Workflow templates and mapper
│   └── pms/                     # Project Management System
│       ├── __init__.py
│       ├── context_serializer.py # Context XML serialization
│       ├── task_file_store.py   # File-based context store (.tasks/)
│       ├── minimal_context.py   # Minimal context injection (~50 tokens)
│       └── task_manager.py      # Task CRUD operations
├── prompts/                     # Agent prompts
│   ├── agents/                  # Main agent XML prompts
│   └── common_schema.xml        # Shared output format
└── tests/                       # Test suite
    └── ...
```

## Core Concepts

### Layer-Based Agent Architecture

The system uses a **layer-based architecture** that supports any type of software project. Agents are organized into layers rather than web-specific paradigms:

```
┌─────────────────────────────────────────────────────────────┐
│                      UI LAYER                               │
│  Web │ Mobile │ Desktop │ CLI                               │
├─────────────────────────────────────────────────────────────┤
│                     CORE LAYER                              │
│  API Services │ Systems Programming │ Library Development   │
├─────────────────────────────────────────────────────────────┤
│                   PLATFORM LAYER                            │
│  iOS │ Android │ Windows │ Linux │ macOS │ Embedded         │
├─────────────────────────────────────────────────────────────┤
│                  INTEGRATION LAYER                          │
│  Database │ External APIs │ Network │ Hardware              │
├─────────────────────────────────────────────────────────────┤
│                   GRAPHICS LAYER                            │
│  AI Image Gen │ Background Removal │ Icons │ Assets         │
└─────────────────────────────────────────────────────────────┘
```

### Agent Types

Defined in `agentic_builder/common/types.py`. Total: 38 agent configurations.

**Universal Agents (always applicable):**

| Agent | Description | Model Tier |
|-------|-------------|------------|
| PM | Project Manager | Opus |
| ARCHITECT | System Architect | Opus |
| UIUX_GUI | UI/UX Designer for Graphical Interfaces (Web, Mobile, Desktop) | Opus |
| UIUX_CLI | UX Designer for Command-Line Interfaces | Sonnet |
| TEST | Test Engineer | Sonnet |
| CQR | Code Quality Reviewer | Sonnet |
| SR | Security Reviewer | Opus |
| DOE | DevOps Engineer | Sonnet |

**UI Layer Agents:**

| Agent | Description | Expertise |
|-------|-------------|-----------|
| TL_UI_WEB / DEV_UI_WEB | Web UI | React, Vue, Angular, HTML/CSS |
| TL_UI_MOBILE / DEV_UI_MOBILE | Mobile UI | iOS, Android, Flutter, React Native |
| TL_UI_DESKTOP / DEV_UI_DESKTOP | Desktop UI | Qt, Electron, WPF, GTK |
| TL_UI_CLI / DEV_UI_CLI | CLI | argparse, click, clap |

**Core Layer Agents:**

| Agent | Description | Expertise |
|-------|-------------|-----------|
| TL_CORE_API / DEV_CORE_API | API Services | REST, GraphQL, gRPC |
| TL_CORE_SYSTEMS / DEV_CORE_SYSTEMS | Systems | C, C++, Rust, low-level |
| TL_CORE_LIBRARY / DEV_CORE_LIBRARY | Libraries | SDK design, public APIs |

**Platform Layer Agents:**

| Agent | Platform |
|-------|----------|
| DEV_PLATFORM_IOS | iOS/iPadOS |
| DEV_PLATFORM_ANDROID | Android |
| DEV_PLATFORM_WINDOWS | Windows |
| DEV_PLATFORM_LINUX | Linux |
| DEV_PLATFORM_MACOS | macOS |
| DEV_PLATFORM_EMBEDDED | Embedded/RTOS |

**Integration Layer Agents:**

| Agent | Domain |
|-------|--------|
| DEV_INTEGRATION_DATABASE | SQL, NoSQL, embedded DBs |
| DEV_INTEGRATION_API | External API consumption |
| DEV_INTEGRATION_NETWORK | Protocols, sockets |
| DEV_INTEGRATION_HARDWARE | Peripherals, drivers |

**Graphics Layer Agents:**

| Agent | Description | Expertise |
|-------|-------------|-----------|
| TL_GRAPHICS | Graphics Tech Lead | Brand assets, design direction, visual strategy |
| DEV_GRAPHICS | Graphics Developer | Image generation, asset optimization, mockups |

**Legacy Aliases (backward compatibility):**
- `UIUX` → `UIUX_GUI`
- `TL_FRONTEND` → `TL_UI_WEB`
- `DEV_FRONTEND` → `DEV_UI_WEB`
- `TL_BACKEND` → `TL_CORE_API`
- `DEV_BACKEND` → `DEV_CORE_API`

### Sub-Agents

49 specialized sub-agents in `.claude/agents/` that main agents can delegate to:

| Category | Sub-Agents |
|----------|------------|
| Analysis | requirements-analyzer, risk-assessor, scope-estimator, complexity-analyzer, performance-analyzer |
| Design | api-designer*, data-modeler, wireframe-generator, design-system-creator, protocol-schema-generator, **cli-ux-designer** |
| Code Generation | component-generator*, controller-generator, model-generator, api-client-generator |
| Testing | unit-test-generator, integration-test-generator, e2e-test-generator, test-data-generator |
| Quality | lint-analyzer, code-documentation-generator, accessibility-checker |
| Security | security-scanner, dependency-auditor |
| DevOps | dockerfile-generator, ci-pipeline-generator, env-config-generator*, k8s-manifest-generator, platform-manifest-generator |
| Localization | localization-generator |
| Architecture | tech-stack-evaluator |
| Content | content-researcher, content-sourcer, content-taxonomy-designer, content-schema-designer, content-generator, assessment-generator, content-validator, learning-path-designer |
| Graphics | image-generator, background-remover, icon-generator, asset-optimizer, image-editor, color-palette-extractor, mockup-generator, social-media-asset-generator, sprite-sheet-generator, logo-generator |

**Sub-Agent Model Tiers:**

Sub-agents use tiered models based on task complexity:

| Model | Count | Usage | Sub-Agents |
|-------|-------|-------|------------|
| Opus | 2 | Deep reasoning, security-critical | security-scanner, risk-assessor |
| Sonnet | 25 | Analysis, design, testing | api-designer, data-modeler, wireframe-generator, design-system-creator, cli-ux-designer, unit-test-generator, integration-test-generator, e2e-test-generator, lint-analyzer, accessibility-checker, dependency-auditor, complexity-analyzer, performance-analyzer, requirements-analyzer, scope-estimator, tech-stack-evaluator, image-generator, content-* agents, learning-path-designer |
| Haiku | 22 | Templated code/config generation | component-generator, controller-generator, model-generator, api-client-generator, protocol-schema-generator, code-documentation-generator, test-data-generator, dockerfile-generator, ci-pipeline-generator, k8s-manifest-generator, env-config-generator, platform-manifest-generator, localization-generator, icon-generator, asset-optimizer, image-editor, color-palette-extractor, sprite-sheet-generator, background-remover, mockup-generator, social-media-asset-generator, logo-generator |

*New sub-agent **cli-ux-designer** for CLI UX design*

**Extended Sub-Agents:**
- `component-generator*` - Now supports web (React, Vue, Svelte, Angular), mobile (React Native, Flutter, SwiftUI, Compose), and desktop (Qt, Electron, WPF, GTK)
- `api-designer*` - Now supports REST, GraphQL, gRPC, WebSocket, CLI commands, and binary protocols
- `env-config-generator*` - Now supports backend, frontend, mobile, desktop, CLI, and embedded configurations

**Graphics Sub-Agents (NEW):**
- `image-generator` - Generate images using Google AI Imagen API from text prompts
- `background-remover` - Remove backgrounds from images using AI segmentation (rembg/U2Net)
- `icon-generator` - Generate app icons for iOS, Android, web, and desktop platforms
- `asset-optimizer` - Optimize images for web/mobile with WebP/AVIF conversion and responsive variants
- `image-editor` - Programmatic image editing (resize, crop, rotate, filters, watermarks)
- `color-palette-extractor` - Extract color palettes from images for design systems
- `mockup-generator` - Generate device mockups for screenshots and marketing materials
- `social-media-asset-generator` - Generate social media graphics for all major platforms
- `sprite-sheet-generator` - Generate sprite sheets for games with JSON metadata
- `logo-generator` - Generate logo concepts and brand asset packages

**Specialized Architects (Discovery-Driven):**

Used by the adaptive orchestrator to determine exactly what's needed:

| Architect | Description | Spawns |
|-----------|-------------|--------|
| `architect-system` | Overall system design, tech stack selection | Spawns specialized architects |
| `architect-frontend` | UI architecture (web/mobile/desktop) | DEV_UI_* agents |
| `architect-backend` | API/service design, database schema | DEV_CORE_API, DEV_INTEGRATION_* |
| `architect-mobile` | Mobile-specific architecture | DEV_UI_MOBILE, platform agents |
| `architect-data` | Complex data modeling, storage strategy | DEV_INTEGRATION_DATABASE |
| `architect-infrastructure` | Deployment, CI/CD, DevOps | DOE, infrastructure setup |

**Main Agent Task Wrappers:**

Sub-agents that wrap main agents for Task tool spawning:

| Wrapper | Main Agent | Model |
|---------|------------|-------|
| `main-pm` | PM (Project Manager) | Opus |
| `main-architect` | ARCHITECT | Sonnet |
| `main-uiux-gui` | UIUX_GUI | Sonnet |
| `main-tl-ui-web` | TL_UI_WEB | Sonnet |
| `main-tl-core-api` | TL_CORE_API | Sonnet |
| `main-dev-ui-web` | DEV_UI_WEB | Haiku |
| `main-dev-core-api` | DEV_CORE_API | Haiku |
| `main-test` | TEST | Sonnet |

### Orchestration

Main agents use the **orchestrator skill** (`.claude/skills/orchestrator.md`) to:
1. **Plan**: Break work into sub-tasks with dependencies
2. **Delegate**: Map tasks to sub-agents
3. **Execute**: Run sub-agents in parallel where possible
4. **Aggregate**: Combine results

### Workflow Types

Defined in `agentic_builder/orchestration/workflows.py`:

- `FULL_APP_GENERATION` - Complete application build
- `FEATURE_ADDITION` - Add new feature
- `BUG_FIX` - Fix bugs
- `REFACTORING` - Code refactoring
- `TEST_GENERATION` - Generate tests
- `CODE_REVIEW` - Review code quality
- `SECURITY_AUDIT` - Security review

### Key Classes

**Orchestration Engines:**

| Class | Module | Description | Speed |
|-------|--------|-------------|-------|
| `WorkflowEngine` | `workflow_engine.py` | Sequential orchestrator (original) | 1x (baseline) |
| `ParallelWorkflowEngine` | `parallel_engine.py` | Async parallel execution | 5x faster |
| `SingleSessionOrchestrator` | `single_session.py` | Single Claude CLI instance | 8x faster |
| `AdaptiveOrchestrator` | `adaptive_orchestrator.py` | Discovery-driven spawning | 8x + 85% fewer agents |

**Supporting Classes:**

- **SessionManager** (`orchestration/session_manager.py`): Handles session persistence and status tracking
- **TaskManager** (`pms/task_manager.py`): CRUD operations for tasks with JSON file storage
- **TaskFileStore** (`pms/task_file_store.py`): File-based context store for zero-token context sharing
- **MinimalContextSerializer** (`pms/minimal_context.py`): Generates ~50 token context pointers
- **BatchedGitManager** (`integration/batched_git.py`): Phase-based git commits (85% less overhead)
- **PhaseCommitStrategy** (`integration/batched_git.py`): Maps agents to git commit phases
- **ClaudeClient** (`integration/claude_client.py`): Wrapper for Claude CLI invocation

**Adaptive Orchestrator Data Classes:**

- **ConfidenceLevel**: Enum for decision confidence (HIGH, MEDIUM, LOW)
- **SpawnRequest**: Request to spawn an agent with context
- **SkipDecision**: Decision to skip an agent with reason
- **UserQuestion**: Question requiring user input
- **AgentDecision**: Decision made by an agent
- **AgentOutput**: Parsed output from an agent execution

### Performance Optimization (New)

The framework includes optimizations that reduce workflow time from **80+ minutes to ~15 minutes**:

| Optimization | Impact | Module |
|--------------|--------|--------|
| Parallel agent execution | 5.7x speedup | `parallel_engine.py` |
| File-based context store | 99% token reduction | `task_file_store.py` |
| Minimal context injection | ~50 vs ~5000 tokens | `minimal_context.py` |
| Model tier downgrades | 2.7x model time reduction | `fast_configs.py` |
| Batched git commits | 85% git overhead reduction | `batched_git.py` |

**Task File Store (`.tasks/` directory)**:
```
.tasks/
├── manifest.json           # Session state and task registry
├── PM/
│   ├── output.json         # Summary, next_steps, warnings
│   └── artifacts.json      # Created file paths
├── ARCHITECT/
│   ├── output.json
│   ├── artifacts.json
│   └── decisions.json      # Architectural decisions
└── ...
```

**Minimal Context Injection** (~50 tokens instead of ~5000):
```xml
<task>
  <agent>DEV_UI_WEB</agent>
  <manifest>.tasks/manifest.json</manifest>
  <read_from>PM, ARCHITECT, TL_UI_WEB</read_from>
</task>
```

Agents read context files directly from disk instead of receiving full context in prompts.

**Fast Model Tier Distribution**:
| Tier | Count | Agents |
|------|-------|--------|
| Opus | 2 | PM, SR |
| Sonnet | 10 | ARCHITECT, UIUX_*, TL_*, TEST |
| Haiku | 26 | All DEV_*, CQR, DOE, Content, Graphics |

### Discovery-Driven Orchestration (AdaptiveOrchestrator)

The adaptive orchestrator uses a **discovery-driven** approach where agents are spawned only when needed:

```
Traditional: PM → ARCHITECT → ALL 40 AGENTS (sequential)
Discovery:   PM → architect-system → [only needed agents] (parallel)
```

**Agent Reduction by Project Type:**

| Project Type | Traditional | Discovery | Reduction |
|--------------|-------------|-----------|-----------|
| Simple web app | 40 agents | 6 agents | 85% |
| Mobile app | 40 agents | 10 agents | 75% |
| CLI tool | 40 agents | 4 agents | 90% |

**Confidence Levels:**

Agents make decisions with confidence levels that determine user interaction:

| Level | Behavior | Example |
|-------|----------|---------|
| HIGH | Proceed silently, log decision | "Using React 18 (industry standard)" |
| MEDIUM | State decision, allow 2s override | "Using SQLite - say 'postgres' to change" |
| LOW | Must ask user before proceeding | "Include authentication? [y/n]" |

**Skip Propagation:**

When an agent decides to skip downstream agents, the decision propagates:

```python
# PM outputs skip_agents
skip_agents: [
  {"agent": "architect-mobile", "reason": "Web-only project"},
  {"agent": "DEV_UI_MOBILE", "reason": "No mobile UI needed"}
]

# These agents are added to global skip list and never spawned
```

**Agent Output Schema (Discovery-Driven):**

```json
{
  "summary": "Completed analysis",
  "spawn_next": [
    {"agent": "architect-frontend", "reason": "Web UI needed", "priority": "required"}
  ],
  "skip_agents": [
    {"agent": "architect-mobile", "reason": "Web-only project"}
  ],
  "ask_user": [
    {
      "id": "include_auth",
      "question": "Include user authentication?",
      "confidence": "low",
      "recommendation": "no",
      "reason": "Simpler MVP"
    }
  ]
}
```

### Artifact Handling (Token-Efficient Design)

Agents write files directly to disk and only report file paths in their XML response. This saves tokens by:
- Not embedding file content in XML responses
- Not passing file content between agents (only paths)
- Allowing agents to read files directly when needed

**Agent Output Format** (`prompts/common_schema.xml`):
```xml
<summary>Description of work done</summary>
<artifacts>
  <artifact path="src/file.py" action="created"/>
  <artifact path="tests/test_file.py" action="modified"/>
</artifacts>
<next_steps>- Step 1</next_steps>
<warnings>- Warning if any</warnings>
```

## Development Workflows

### Setup

```bash
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_workflows.py

# Run with verbose output
pytest -v
```

### Linting

```bash
# Run ruff linter
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

### CLI Usage

```bash
# Start a workflow with a project idea (outputs to current directory)
agentic-builder run FULL_APP_GENERATION --idea "Build a todo app with React and FastAPI"

# Specify a custom output directory for the project
agentic-builder run FULL_APP_GENERATION --idea "Build a todo app" --output-dir ./my-project
agentic-builder run FULL_APP_GENERATION --idea "Build a todo app" -o ./my-project

# For a CLI tool
agentic-builder run FULL_APP_GENERATION --idea "Build a CLI file encryption tool in Rust"

# For a library
agentic-builder run FULL_APP_GENERATION --idea "Create a C++ SQLite wrapper library"

# With debug logging
agentic-builder --debug run FULL_APP_GENERATION --idea "Your project idea"

# List sessions
agentic-builder list

# View session status
agentic-builder status <session-id>

# Cancel a workflow
agentic-builder cancel <session-id>

# Resume a workflow
agentic-builder resume <session-id>
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `AMAB_DEBUG` | Set to `1` to enable debug logging |
| `AMAB_MOCK_CLAUDE_CLI` | Set to `1` to mock Claude CLI responses |
| `AMAB_MOCK_GH_CLI` | Set to `1` to mock GitHub CLI |
| `GOOGLE_AI_API_KEY` | Google AI Studio API key for image generation (Imagen) |

## Key Conventions

### Code Style

- **Line length:** 120 characters
- **Target Python:** 3.10+
- **Linter:** Ruff with E, F, I rules
- **Type hints:** Use Pydantic models for data classes
- **Naming:** `snake_case` functions, `PascalCase` classes, `UPPER_SNAKE_CASE` constants

### Adding a New Agent Type

1. Add enum value to `AgentType` in `common/types.py`
2. Add configuration to `AGENT_CONFIGS_MAP` in `agents/configs.py` with appropriate `layer`
3. Create prompt file in `prompts/agents/<AGENT_TYPE>.xml`
4. Update workflow templates in `orchestration/workflows.py`
5. Document in `docs/architecture.md`

### Adding a New Sub-Agent

1. Create markdown file in `.claude/agents/<name>.md` with YAML frontmatter
2. Define `name`, `description`, `tools`, `model`
3. Add XML instructions in the body
4. Update `docs/sub-agent-mappings.md`

### Security Considerations

- **Path traversal prevention**: Always use `Path.is_relative_to()` before writing files
- **No credentials in code**: Use environment variables for secrets
- **Subprocess safety**: Use list form for `subprocess.run()` commands
- **Input validation**: Validate all external inputs before processing

## Git Workflow

- **Commit messages:** Use conventional commits (feat:, fix:, docs:, refactor:, test:, chore:)
- **Branch naming:** `feature/<description>`, `fix/<description>`

---

*Last updated: 2025-01 - Keep this document in sync with codebase changes.*
