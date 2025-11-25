# Agent Architecture

This document describes the layer-based agent architecture used in the Agentic Builder framework.

## Design Philosophy

The Agentic Builder uses a **layer-based architecture** that supports any type of software project, not just web applications. Instead of organizing agents around web paradigms (frontend/backend), agents are organized around **universal software layers** that exist in all software projects.

## Layer Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          UI LAYER                                       │
│  How users (or developers) interact with the software                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                       │
│  │   WEB   │ │ MOBILE  │ │ DESKTOP │ │   CLI   │                       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                       │
├─────────────────────────────────────────────────────────────────────────┤
│                         CORE LAYER                                      │
│  The actual functionality - algorithms, business rules, domain logic    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                                   │
│  │   API   │ │ SYSTEMS │ │ LIBRARY │                                   │
│  │Services │ │Low-level│ │SDK/Lib  │                                   │
│  └─────────┘ └─────────┘ └─────────┘                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                       CONTENT LAYER                                     │
│  Content research, generation, validation, and organization             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                       │
│  │Research │ │Generate │ │Validate │ │Organize │                       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                       │
├─────────────────────────────────────────────────────────────────────────┤
│                       PLATFORM LAYER                                    │
│  Platform-specific concerns and abstractions                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │   iOS   │ │ Android │ │ Windows │ │  Linux  │ │Embedded │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
├─────────────────────────────────────────────────────────────────────────┤
│                      INTEGRATION LAYER                                  │
│  External systems, data persistence, protocols                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                       │
│  │Database │ │   API   │ │ Network │ │Hardware │                       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                       │
└─────────────────────────────────────────────────────────────────────────┘
```

## Agent Categories

### Universal Agents

These agents apply to ALL software projects regardless of type:

| Agent | Role | Model Tier | Description |
|-------|------|------------|-------------|
| PM | Project Manager | Opus | Analyzes requirements, creates project plan, coordinates workflow |
| ARCHITECT | System Architect | Opus | Designs technical architecture, selects technologies |
| UIUX_GUI | UI/UX Designer (GUI) | Opus | Designs visual interfaces (Web, Mobile, Desktop) - wireframes, design systems, visual accessibility |
| UIUX_CLI | UX Designer (CLI) | Sonnet | Designs CLI user experience - command structure, help text, error messages, output formatting |
| TEST | Test Engineer | Sonnet | Creates and executes tests across all layers |
| CQR | Code Quality Reviewer | Sonnet | Reviews code quality, style, maintainability |
| SR | Security Reviewer | Opus | Audits security vulnerabilities |
| DOE | DevOps Engineer | Sonnet | Handles CI/CD, deployment, infrastructure |

**Note:** UIUX_GUI is used by graphical UI team leads (TL_UI_WEB, TL_UI_MOBILE, TL_UI_DESKTOP), while UIUX_CLI is used by CLI team leads (TL_UI_CLI).

### UI Layer Agents

Specialists for different user interface types:

| Agent | Role | Expertise |
|-------|------|-----------|
| TL_UI_WEB | Web UI Team Lead | React, Vue, Angular, HTML/CSS architecture |
| DEV_UI_WEB | Web UI Developer | Web component implementation |
| TL_UI_MOBILE | Mobile UI Team Lead | iOS, Android, Flutter, React Native architecture |
| DEV_UI_MOBILE | Mobile UI Developer | Mobile UI implementation |
| TL_UI_DESKTOP | Desktop UI Team Lead | Qt, Electron, WPF, GTK architecture |
| DEV_UI_DESKTOP | Desktop UI Developer | Desktop UI implementation |
| TL_UI_CLI | CLI Team Lead | Command-line interface architecture |
| DEV_UI_CLI | CLI Developer | CLI implementation (argparse, click, clap) |

### Core Layer Agents

Specialists for core business logic:

| Agent | Role | Expertise |
|-------|------|-----------|
| TL_CORE_API | API Services Team Lead | REST, GraphQL, gRPC API architecture |
| DEV_CORE_API | API Services Developer | API endpoint implementation |
| TL_CORE_SYSTEMS | Systems Team Lead | Low-level systems architecture (C, C++, Rust) |
| DEV_CORE_SYSTEMS | Systems Developer | Systems programming implementation |
| TL_CORE_LIBRARY | Library Team Lead | Library/SDK API design |
| DEV_CORE_LIBRARY | Library Developer | Library implementation |

### Platform Layer Agents

Specialists for platform-specific code (no Team Lead needed - ARCHITECT provides guidance):

| Agent | Platform | Expertise |
|-------|----------|-----------|
| DEV_PLATFORM_IOS | iOS/iPadOS | App lifecycle, permissions, App Store guidelines, HealthKit, etc. |
| DEV_PLATFORM_ANDROID | Android | Activities, intents, Play Store, Android-specific APIs |
| DEV_PLATFORM_WINDOWS | Windows | Win32, WinRT, registry, Windows services, installers |
| DEV_PLATFORM_LINUX | Linux | systemd, package managers, Linux-specific APIs |
| DEV_PLATFORM_MACOS | macOS | Cocoa, App Sandbox, Mac App Store |
| DEV_PLATFORM_EMBEDDED | Embedded | MCU, RTOS, HAL, memory-constrained environments |

### Integration Layer Agents

Specialists for external system integration (no Team Lead needed):

| Agent | Domain | Expertise |
|-------|--------|-----------|
| DEV_INTEGRATION_DATABASE | Databases | SQL, NoSQL, embedded DBs, ORM, migrations |
| DEV_INTEGRATION_API | External APIs | REST clients, OAuth, API consumption |
| DEV_INTEGRATION_NETWORK | Networking | TCP/UDP, WebSockets, protocols, sockets |
| DEV_INTEGRATION_HARDWARE | Hardware | Peripherals, drivers, device interfaces |

### Content Layer Agents

Specialists for content-driven applications (educational, knowledge bases, etc.):

| Agent | Role | Expertise |
|-------|------|-----------|
| TL_CONTENT | Content Team Lead | Content strategy, taxonomy design, source planning |
| DEV_CONTENT | Content Developer | Content research, generation, validation |

Content agents support applications that require:
- Content research from web and other sources
- Content generation (articles, questions, lessons, etc.)
- Content validation (accuracy, safety, appropriateness)
- Content organization (taxonomies, learning paths)

## Project Type Examples

### Web Application

```
Agents: PM, ARCHITECT, UIUX_GUI
        TL_UI_WEB, DEV_UI_WEB           (UI Layer)
        TL_CORE_API, DEV_CORE_API       (Core Layer)
        DEV_INTEGRATION_DATABASE        (Integration Layer)
        TEST, CQR, SR, DOE
```

### Mobile App (iOS + Android)

```
Agents: PM, ARCHITECT, UIUX_GUI
        TL_UI_MOBILE, DEV_UI_MOBILE     (UI Layer)
        TL_CORE_API, DEV_CORE_API       (Core Layer - backend)
        DEV_PLATFORM_IOS                (Platform Layer)
        DEV_PLATFORM_ANDROID            (Platform Layer)
        DEV_INTEGRATION_API             (Integration Layer - backend API)
        DEV_INTEGRATION_DATABASE        (Integration Layer - local storage)
        TEST, CQR, SR, DOE
```

### CLI Tool (like ripgrep)

```
Agents: PM, ARCHITECT, UIUX_CLI
        TL_UI_CLI, DEV_UI_CLI           (UI Layer)
        TL_CORE_SYSTEMS, DEV_CORE_SYSTEMS (Core Layer)
        DEV_PLATFORM_WINDOWS            (Platform Layer - if cross-platform)
        DEV_PLATFORM_LINUX              (Platform Layer)
        TEST, CQR, SR, DOE
```

### C++ Library (SQLite Wrapper)

```
Agents: PM, ARCHITECT
        TL_CORE_LIBRARY, DEV_CORE_LIBRARY   (Core Layer)
        TL_CORE_SYSTEMS, DEV_CORE_SYSTEMS   (Core Layer - C++ impl)
        DEV_INTEGRATION_DATABASE            (Integration Layer - SQLite)
        DEV_PLATFORM_WINDOWS                (Platform Layer - if needed)
        DEV_PLATFORM_LINUX                  (Platform Layer - if needed)
        TEST, CQR, SR, DOE
```

### Desktop Application (Qt)

```
Agents: PM, ARCHITECT, UIUX_GUI
        TL_UI_DESKTOP, DEV_UI_DESKTOP   (UI Layer)
        TL_CORE_SYSTEMS, DEV_CORE_SYSTEMS (Core Layer)
        DEV_PLATFORM_WINDOWS            (Platform Layer)
        DEV_PLATFORM_LINUX              (Platform Layer)
        DEV_PLATFORM_MACOS              (Platform Layer)
        DEV_INTEGRATION_DATABASE        (Integration Layer - if needed)
        TEST, CQR, SR, DOE
```

### Embedded Firmware

```
Agents: PM, ARCHITECT
        TL_CORE_SYSTEMS, DEV_CORE_SYSTEMS   (Core Layer)
        DEV_PLATFORM_EMBEDDED               (Platform Layer)
        DEV_INTEGRATION_HARDWARE            (Integration Layer)
        TEST, CQR, SR, DOE
```

### Educational Application

```
Agents: PM, ARCHITECT, UIUX_GUI
        TL_UI_WEB, DEV_UI_WEB               (UI Layer - or MOBILE)
        TL_CORE_API, DEV_CORE_API           (Core Layer)
        TL_CONTENT, DEV_CONTENT             (Content Layer)
        DEV_INTEGRATION_DATABASE            (Integration Layer)
        TEST, CQR, SR, DOE
```

### Knowledge Base / Documentation System

```
Agents: PM, ARCHITECT, UIUX_GUI
        TL_UI_WEB, DEV_UI_WEB               (UI Layer)
        TL_CORE_API, DEV_CORE_API           (Core Layer)
        TL_CONTENT, DEV_CONTENT             (Content Layer)
        DEV_INTEGRATION_DATABASE            (Integration Layer)
        DEV_INTEGRATION_API                 (Integration Layer - if indexing external sources)
        TEST, CQR, SR, DOE
```

## Agent Selection Flow

1. **PM** analyzes the project requirements
2. **PM** classifies the project type and identifies required layers
3. **ARCHITECT** designs the system architecture
4. **Orchestrator** selects appropriate agents based on:
   - Project type (web, mobile, desktop, CLI, library, embedded)
   - Required UI (if any)
   - Target platforms
   - Integration needs

## Dependency Graph

```
                          ┌──────┐
                          │  PM  │
                          └──┬───┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    ┌────────┐         ┌─────────┐         ┌─────────┐
    │ARCHITECT│         │UIUX_GUI │         │UIUX_CLI │
    └────┬───┘         └────┬────┘         └────┬────┘
         │                  │                   │
         ├──────────────────┼───────────────────┤
         │                  │                   │
         ▼                  ▼                   ▼
    ┌─────────┐       ┌───────────┐       ┌─────────┐
    │ TL_CORE │       │TL_UI_WEB/ │       │TL_UI_CLI│
    │  _XXX   │       │MOBILE/    │       └────┬────┘
    └────┬────┘       │DESKTOP    │            │
         │            └─────┬─────┘            │
         ▼                  ▼                  ▼
    ┌─────────┐       ┌─────────┐        ┌─────────┐
    │DEV_CORE │       │DEV_UI_* │        │DEV_UI_  │
    │  _XXX   │       │(GUI)    │        │CLI      │
    └────┬────┘       └────┬────┘        └────┬────┘
         │                 │                  │
         └─────────────────┼──────────────────┘
                           │
             ┌─────────────┼─────────────┬─────────────┐
             │             │             │             │
             ▼             ▼             ▼             ▼
        ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
        │  TEST  │    │  CQR   │    │   SR   │    │  DOE   │
        └────────┘    └────────┘    └────────┘    └────────┘
```

**Key dependencies:**
- TL_UI_WEB/MOBILE/DESKTOP depend on ARCHITECT + UIUX_GUI
- TL_UI_CLI depends on ARCHITECT + UIUX_CLI

## Sub-Agent Delegation

Each main agent can delegate to specialized sub-agents for focused tasks. See [Sub-Agent Mappings](sub-agent-mappings.md) for details.

## Orchestration

Main agents use the **orchestrator skill** to:
1. Plan work breakdown into sub-tasks
2. Map sub-tasks to appropriate sub-agents
3. Execute sub-agents in parallel where possible
4. Aggregate results

See [Orchestration Skill](../prompts/skills/orchestrator.md) for the orchestration pattern.

## Adding New Agents

To add a new agent type:

1. Add enum value to `AgentType` in `agentic_builder/common/types.py`
2. Add configuration to `AGENT_CONFIGS_MAP` in `agentic_builder/agents/configs.py`
3. Create prompt file in `prompts/agents/<AGENT_TYPE>.xml`
4. Update workflow templates in `agentic_builder/orchestration/workflows.py`
5. Document in this file

## Backward Compatibility

For backward compatibility with existing workflows:
- `UIUX` → alias for `UIUX_GUI`
- `TL_FRONTEND` → alias for `TL_UI_WEB`
- `DEV_FRONTEND` → alias for `DEV_UI_WEB`
- `TL_BACKEND` → alias for `TL_CORE_API`
- `DEV_BACKEND` → alias for `DEV_CORE_API`
