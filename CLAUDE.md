# CLAUDE.md - AI Assistant Guidelines


This document provides guidance for AI assistants working on the Jules Agentic Software Builder for Claude project.

## Project Overview

**Repository:** jules-agentic-software-builder-for-claude
**Name:** Agentic Builder
**Version:** 0.1.0
**Language:** Python 3.10+
**Purpose:** An agentic software builder tool designed to work with Claude AI for automated software development tasks.
**Status:** Initial Development Phase

## Codebase Structure

```
jules-agentic-software-builder-for-claude/
├── CLAUDE.md                    # AI assistant guidelines (this file)
├── README.md                    # Project documentation
├── pyproject.toml               # Python project configuration
├── .gitignore                   # Git ignore rules
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
└── tests/                       # Test suite
    ├── __init__.py
    ├── test_agents.py
    ├── test_cli.py
    ├── test_common.py
    ├── test_e2e.py
    ├── test_fixes.py
    ├── test_integration.py
    ├── test_orchestration.py
    ├── test_pms.py
    └── test_workflows.py
```

## Core Concepts

### Agent Types

The system uses 11 specialized agent types defined in `agentic_builder/common/types.py`:

| Agent | Description | Model Tier | Dependencies |
|-------|-------------|------------|--------------|
| PM | Project Manager | Opus | None |
| ARCHITECT | System Architect | Opus | PM |
| UIUX | UI/UX Designer | Sonnet | PM |
| TL_FRONTEND | Frontend Tech Lead | Sonnet | ARCHITECT, UIUX |
| TL_BACKEND | Backend Tech Lead | Sonnet | ARCHITECT |
| DEV_FRONTEND | Frontend Developer | Sonnet | TL_FRONTEND |
| DEV_BACKEND | Backend Developer | Sonnet | TL_BACKEND |
| TEST | Test Engineer | Sonnet | DEV_FRONTEND, DEV_BACKEND |
| CQR | Code Quality Reviewer | Sonnet | DEV_FRONTEND, DEV_BACKEND |
| SR | Security Reviewer | Opus | DEV_FRONTEND, DEV_BACKEND |
| DOE | DevOps Engineer | Haiku | DEV_FRONTEND, DEV_BACKEND |

### Workflow Types

Defined in `agentic_builder/orchestration/workflows.py`:

- `FULL_APP_GENERATION` - All agents participate
- `FEATURE_ADDITION` - Most agents except DOE
- `BUG_FIX` - PM, TLs, DEVs, TEST
- `REFACTORING` - ARCHITECT, TLs, DEVs, CQR
- `TEST_GENERATION` - TEST only
- `CODE_REVIEW` - CQR only
- `SECURITY_AUDIT` - SR only

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

**Context Passed to Agents** (includes previous agent outputs):
```xml
<task_context>
  <task_id>TASK-0003</task_id>
  <agent_role>DEV_FRONTEND</agent_role>
  <description>Execute DEV_FRONTEND phase</description>
  <dependencies>
    <dependency id='TASK-0002' agent='TL_FRONTEND'>
      <summary>Designed component architecture...</summary>
      <artifacts>
        <artifact path='/path/to/design.md'/>
      </artifacts>
      <next_steps>
        <step>Implement React components</step>
      </next_steps>
      <warnings>
        <warning>Consider mobile responsiveness</warning>
      </warnings>
    </dependency>
  </dependencies>
</task_context>
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
# Start a workflow
agentic-builder run FULL_APP_GENERATION

# Start a workflow with debug logging (see prompts and responses)
agentic-builder --debug run FULL_APP_GENERATION

# List sessions
agentic-builder list
agentic-builder list --all
agentic-builder list --zombies

# View session status
agentic-builder status <session-id>

# View logs
agentic-builder logs <session-id>

# Cancel a workflow
agentic-builder cancel <session-id>

# Resume a workflow
agentic-builder resume <session-id>

# Show token usage
agentic-builder usage
```

### Debug Logging

Debug logging provides detailed visibility into:
- **Prompts sent to Claude agents** (system prompts, task prompts, context XML)
- **Responses received from agents** (raw output, parsed artifacts, next steps)
- **Workflow operations** (agent spawning, task creation, file handling)
- **Context serialization** (dependency data passed between agents)

**Enable via CLI flag:**
```bash
agentic-builder --debug run FULL_APP_GENERATION
# or
agentic-builder -d run FULL_APP_GENERATION
```

**Enable via environment variable:**
```bash
export AMAB_DEBUG=1
agentic-builder run FULL_APP_GENERATION
```

Debug logs are written to:
- **Console (stderr):** Real-time output during execution
- **Log files:** `.sessions/debug_logs/debug_<timestamp>.log`

### Environment Variables

| Variable | Description |
|----------|-------------|
| `AMAB_DEBUG` | Set to `1` to enable debug logging (same as `--debug` flag) |
| `AMAB_MOCK_CLAUDE_CLI` | Set to `1` to mock Claude CLI responses |
| `AMAB_MOCK_GH_CLI` | Set to `1` to mock GitHub CLI (PR creation) |

## Key Conventions

### Code Style

- **Line length:** 120 characters (configured in `pyproject.toml`)
- **Target Python:** 3.10+
- **Linter:** Ruff with E, F, I rules enabled
- **Type hints:** Use Pydantic models for data classes
- **Naming:**
  - `snake_case` for functions and variables
  - `PascalCase` for classes
  - `UPPER_SNAKE_CASE` for constants and enum values

### File Organization

- One class per file for major components
- Group related functionality in subdirectories
- Use `__init__.py` for clean imports
- Keep tests in parallel structure under `tests/`

### Data Storage

- Sessions stored in `.sessions/` directory (gitignored)
- Tasks stored in `.tasks/` directory (gitignored)
- Use JSON format for persistence
- Task IDs follow `TASK-0001` format

### Error Handling

- Return `AgentOutput` with `success=False` for failures
- Use event emission for workflow failures
- Log errors with context to session-specific log files
- Security: Validate file paths to prevent directory traversal

### Testing

- Use pytest as the test framework
- Mock external dependencies (Claude CLI, GitHub CLI)
- Test topological sorting of agent dependencies
- Test workflow execution order

## AI Assistant Instructions

### When Working on This Project

1. **Understand the agent dependency graph** before modifying workflow logic
2. **Preserve event emission patterns** - the CLI relies on events for feedback
3. **Use Pydantic models** for any new data structures
4. **Add tests** for new functionality in the appropriate test file
5. **Security-first**: Always validate file paths before writing

### Common Tasks

**Adding a new agent type:**
1. Add enum value to `AgentType` in `common/types.py`
2. Add configuration to `AGENT_CONFIGS_MAP` in `agents/configs.py`
3. Update workflow templates in `orchestration/workflows.py`
4. Add agent prompt file to `prompts/agents/<AGENT_TYPE>.xml`

**Adding a new workflow:**
1. Add enum value to `WorkflowType` in `orchestration/workflows.py`
2. Add agent list to `WORKFLOW_TEMPLATES`
3. Handle alias in `WorkflowMapper.get_execution_order()` if needed

**Adding a new CLI command:**
1. Add function with `@app.command()` decorator in `main.py`
2. Use `rich.console.Console` for output formatting
3. Follow existing patterns for error handling

### Files to Read First

When working on a task, start by reading:
1. `agentic_builder/common/types.py` - Core data models
2. `agentic_builder/agents/configs.py` - Agent dependency graph
3. `agentic_builder/orchestration/workflow_engine.py` - Main execution logic

### Security Considerations

- **Path traversal prevention**: Always use `Path.is_relative_to()` before writing files
- **No credentials in code**: Use environment variables for secrets
- **Subprocess safety**: Use list form for `subprocess.run()` commands
- **Input validation**: Validate all external inputs before processing

## Git Workflow

- **Commit messages:** Use conventional commits (feat:, fix:, docs:, refactor:, test:, chore:)
- **Branch naming:** `feature/<description>`, `fix/<description>`
- **PR creation:** Draft PRs are created automatically after workflow completion

---

*Last updated: 2024 - Keep this document in sync with codebase changes.*
