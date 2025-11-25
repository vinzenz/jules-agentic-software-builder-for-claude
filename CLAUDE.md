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

## Codebase Structure

```
jules-agentic-software-builder-for-claude/
├── CLAUDE.md                    # AI assistant guidelines (this file)
├── README.md                    # Project documentation
├── pyproject.toml               # Python project configuration
├── .gitignore                   # Git ignore rules
├── docs/                        # Architecture documentation
│   ├── architecture.md          # Layer-based agent architecture
│   └── sub-agent-mappings.md    # Sub-agent delegation mappings
├── .claude/                     # Claude Code configuration
│   ├── agents/                  # Sub-agent definitions (48 specialists)
│   └── skills/                  # Reusable skills (orchestrator)
├── agentic_builder/             # Main package
│   ├── __init__.py
│   ├── main.py                  # CLI entry point (Typer app)
│   ├── agents/                  # Agent configurations
│   │   ├── __init__.py
│   │   ├── configs.py           # Agent configs and dependency map
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
│   │   └── pr_manager.py        # GitHub PR creation
│   ├── orchestration/           # Workflow management
│   │   ├── __init__.py
│   │   ├── session_manager.py   # Session persistence
│   │   ├── workflow_engine.py   # Main execution engine
│   │   └── workflows.py         # Workflow templates and mapper
│   └── pms/                     # Project Management System
│       ├── __init__.py
│       ├── context_serializer.py # Context XML serialization
│       └── task_manager.py      # Task CRUD operations
├── prompts/                     # Agent prompts
│   ├── agents/                  # Main agent XML prompts
│   ├── sub_agents/              # Sub-agent XML definitions
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

- **WorkflowEngine** (`orchestration/workflow_engine.py`): Main orchestrator that manages workflow execution, agent spawning, and event emission
- **SessionManager** (`orchestration/session_manager.py`): Handles session persistence and status tracking
- **TaskManager** (`pms/task_manager.py`): CRUD operations for tasks with JSON file storage
- **ClaudeClient** (`integration/claude_client.py`): Wrapper for Claude CLI invocation

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
# Start a workflow with a project idea
agentic-builder run FULL_APP_GENERATION --idea "Build a todo app with React and FastAPI"

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

*Last updated: 2024 - Keep this document in sync with codebase changes.*
