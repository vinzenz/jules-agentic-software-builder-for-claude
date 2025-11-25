# Sub-Agent Mappings

This document defines which sub-agents are available to each main agent for delegation.

## Overview

Main agents can delegate specialized tasks to sub-agents using the orchestrator skill. Sub-agents are defined in `.claude/agents/` and provide focused expertise for specific tasks.

## Sub-Agent Inventory (38 Total)

| Category | Sub-Agents |
|----------|------------|
| Analysis | requirements-analyzer, risk-assessor, scope-estimator, complexity-analyzer, performance-analyzer |
| Design | api-designer, data-modeler, wireframe-generator, design-system-creator, protocol-schema-generator |
| Code Generation | component-generator, controller-generator, model-generator, api-client-generator |
| Testing | unit-test-generator, integration-test-generator, e2e-test-generator, test-data-generator |
| Quality | lint-analyzer, code-documentation-generator, accessibility-checker |
| Security | security-scanner, dependency-auditor |
| DevOps | dockerfile-generator, ci-pipeline-generator, env-config-generator, k8s-manifest-generator, platform-manifest-generator |
| Localization | localization-generator |
| Architecture | tech-stack-evaluator |
| **Content** | **content-researcher, content-sourcer, content-taxonomy-designer, content-schema-designer, content-generator, assessment-generator, content-validator, learning-path-designer** |

*New content sub-agents in **bold***

## Universal Agent Mappings

### PM (Project Manager)

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| requirements-analyzer | Extract and structure requirements | Yes |
| risk-assessor | Identify and analyze project risks | Yes |
| scope-estimator | Estimate complexity and define scope | Yes |

### ARCHITECT (System Architect)

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| tech-stack-evaluator | Evaluate technology choices | First |
| data-modeler | Design database schemas | After tech-stack |
| api-designer | Design API specifications (REST, GraphQL, gRPC) | After data-modeler |
| protocol-schema-generator | Generate Protocol Buffer/binary schemas | After api-designer |

### UIUX (UI/UX Designer)

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| wireframe-generator | Create wireframe layouts | Yes |
| design-system-creator | Define design tokens and patterns | Yes |
| accessibility-checker | Review for WCAG compliance | After wireframes |

### TEST (Test Engineer)

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| test-data-generator | Generate fixtures and factories | First |
| unit-test-generator | Create unit tests | After test-data |
| integration-test-generator | Create integration tests | After test-data |
| e2e-test-generator | Create end-to-end tests | After test-data |

### CQR (Code Quality Reviewer)

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| complexity-analyzer | Analyze code complexity metrics | Yes |
| lint-analyzer | Analyze and categorize lint issues | Yes |
| performance-analyzer | Identify performance issues | Yes |
| code-documentation-generator | Generate documentation | After analysis |

### SR (Security Reviewer)

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| security-scanner | Static security analysis | Yes |
| dependency-auditor | Audit dependencies for CVEs | Yes |

### DOE (DevOps Engineer)

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| dockerfile-generator | Generate optimized Dockerfiles | Yes |
| ci-pipeline-generator | Generate CI/CD pipelines | Yes |
| env-config-generator | Generate environment configs | Yes |
| k8s-manifest-generator | Generate Kubernetes manifests | After dockerfile |

## UI Layer Agent Mappings

### TL_UI_WEB / DEV_UI_WEB

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| component-generator | Generate web component boilerplate (React, Vue, Svelte, Angular) | Yes |
| api-client-generator | Generate API client code | Yes |
| accessibility-checker | Check accessibility | After components |
| localization-generator | Set up i18n infrastructure | Yes |

### TL_UI_MOBILE / DEV_UI_MOBILE

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| component-generator | Generate mobile components (React Native, Flutter, SwiftUI, Compose) | Yes |
| api-client-generator | Generate API client code | Yes |
| accessibility-checker | Check accessibility | After components |
| localization-generator | Set up i18n for mobile | Yes |

### TL_UI_DESKTOP / DEV_UI_DESKTOP

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| component-generator | Generate desktop components (Qt, Electron, WPF, GTK) | Yes |
| wireframe-generator | Generate window layouts | Yes |
| localization-generator | Set up i18n for desktop | Yes |

### TL_UI_CLI / DEV_UI_CLI

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| api-designer | Design CLI command structure | Yes |
| code-documentation-generator | Generate help text and man pages | After impl |
| localization-generator | Set up i18n for CLI messages | Yes |

## Core Layer Agent Mappings

### TL_CORE_API / DEV_CORE_API

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| api-designer | Design API endpoints (REST, GraphQL, gRPC) | First |
| protocol-schema-generator | Generate Protocol Buffer definitions | After design |
| controller-generator | Generate API controllers | After design |
| model-generator | Generate data models | After design |

### TL_CORE_SYSTEMS / DEV_CORE_SYSTEMS

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| complexity-analyzer | Analyze algorithmic complexity | Yes |
| performance-analyzer | Analyze memory, cache, and runtime performance | Yes |
| code-documentation-generator | Generate technical docs | After impl |

### TL_CORE_LIBRARY / DEV_CORE_LIBRARY

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| api-designer | Design public API | First |
| code-documentation-generator | Generate API documentation | After impl |
| unit-test-generator | Generate library tests | After impl |

## Platform Layer Agent Mappings

### DEV_PLATFORM_IOS

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| platform-manifest-generator | Generate Info.plist, entitlements | Yes |
| env-config-generator | Generate build configurations | Yes |

### DEV_PLATFORM_ANDROID

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| platform-manifest-generator | Generate AndroidManifest.xml, gradle configs | Yes |
| env-config-generator | Generate build configurations | Yes |

### DEV_PLATFORM_WINDOWS

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| platform-manifest-generator | Generate app manifests, MSIX config | Yes |
| env-config-generator | Generate build configurations | Yes |

### DEV_PLATFORM_MACOS

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| platform-manifest-generator | Generate Info.plist, entitlements | Yes |
| env-config-generator | Generate build configurations | Yes |

### DEV_PLATFORM_LINUX

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| platform-manifest-generator | Generate .desktop files, systemd units, package configs | Yes |
| env-config-generator | Generate build configurations | Yes |

### DEV_PLATFORM_EMBEDDED

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| platform-manifest-generator | Generate linker scripts, Kconfig | Yes |
| env-config-generator | Generate build configurations | Yes |
| performance-analyzer | Analyze memory and timing constraints | After impl |

## Integration Layer Agent Mappings

### DEV_INTEGRATION_DATABASE

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| data-modeler | Design database schemas | First |
| model-generator | Generate ORM models | After design |

### DEV_INTEGRATION_API

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| api-client-generator | Generate API client code | Yes |
| api-designer | Design integration contracts | Yes |

### DEV_INTEGRATION_NETWORK

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| api-designer | Design protocol schemas | Yes |
| protocol-schema-generator | Generate binary/protobuf schemas | Yes |
| security-scanner | Check network security | After impl |

### DEV_INTEGRATION_HARDWARE

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| api-designer | Design hardware abstraction API | Yes |
| code-documentation-generator | Document hardware interfaces | After impl |
| protocol-schema-generator | Generate communication protocol schemas | Yes |

## Content Layer Agent Mappings

### TL_CONTENT

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| content-researcher | Research topics and gather information | Yes |
| content-sourcer | Find and validate information sources | Yes |
| content-taxonomy-designer | Design content classification systems | After research |
| content-schema-designer | Design data models for content storage | After taxonomy |

### DEV_CONTENT

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| content-researcher | Research specific topics in depth | Yes |
| content-generator | Generate articles, explanations, lessons | After research |
| assessment-generator | Generate questions, tests, quizzes | After research |
| content-validator | Validate accuracy, safety, appropriateness | After generation |
| learning-path-designer | Design learning sequences and progressions | After validation |

## Parallelization Rules

1. **Yes** = Can run in parallel with other "Yes" sub-agents
2. **First** = Must run before other sub-agents
3. **After X** = Must wait for sub-agent X to complete

## Extended Sub-Agents

The following sub-agents have been extended to support multiple platforms:

### component-generator
- **Web**: React, Vue, Svelte, Angular, Solid
- **Mobile**: React Native, Flutter, SwiftUI, Jetpack Compose
- **Desktop**: Qt (QML/Widgets), Electron, Tauri, WPF, GTK

### api-designer
- **REST**: OpenAPI/Swagger specifications
- **GraphQL**: SDL schema definitions
- **gRPC**: Protocol Buffer service definitions
- **WebSocket**: Message schemas and event catalogs
- **CLI**: Command structure and help text
- **Binary**: Custom protocol specifications

### env-config-generator
- **Backend**: .env files, config YAML/TOML
- **Frontend**: Build-time env vars, runtime config
- **Mobile**: Build variants, remote config
- **Desktop**: XDG, Registry, plist configs
- **CLI**: ~/.config files, precedence rules
- **Embedded**: Kconfig, compile-time defines

## Adding New Mappings

When adding a new main agent:
1. Identify which sub-agents provide relevant expertise
2. Determine parallelization dependencies
3. Add mapping to this document
4. Update the main agent's XML file with `<sub_agents>` section
