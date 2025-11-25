# Sub-Agent Mappings

This document defines which sub-agents are available to each main agent for delegation.

## Overview

Main agents can delegate specialized tasks to sub-agents using the orchestrator skill. Sub-agents are defined in `.claude/agents/` and provide focused expertise for specific tasks.

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
| api-designer | Design API specifications | After data-modeler |

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
| component-generator | Generate component boilerplate | Yes |
| api-client-generator | Generate API client code | Yes |
| accessibility-checker | Check accessibility | After components |

### TL_UI_MOBILE / DEV_UI_MOBILE

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| component-generator | Generate mobile component structure | Yes |
| api-client-generator | Generate API client code | Yes |
| accessibility-checker | Check accessibility | After components |

### TL_UI_DESKTOP / DEV_UI_DESKTOP

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| component-generator | Generate desktop component structure | Yes |
| wireframe-generator | Generate window layouts | Yes |

### TL_UI_CLI / DEV_UI_CLI

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| api-designer | Design CLI command structure | Yes |
| code-documentation-generator | Generate help text and man pages | After impl |

## Core Layer Agent Mappings

### TL_CORE_API / DEV_CORE_API

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| api-designer | Design API endpoints | First |
| controller-generator | Generate API controllers | After design |
| model-generator | Generate data models | After design |

### TL_CORE_SYSTEMS / DEV_CORE_SYSTEMS

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| complexity-analyzer | Analyze algorithm complexity | Yes |
| code-documentation-generator | Generate technical docs | After impl |

### TL_CORE_LIBRARY / DEV_CORE_LIBRARY

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| api-designer | Design public API | First |
| code-documentation-generator | Generate API documentation | After impl |
| unit-test-generator | Generate library tests | After impl |

## Platform Layer Agent Mappings

### DEV_PLATFORM_* (All Platforms)

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| env-config-generator | Generate platform-specific configs | Yes |
| dockerfile-generator | Generate platform build containers | Yes |

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
| security-scanner | Check network security | After impl |

### DEV_INTEGRATION_HARDWARE

| Sub-Agent | Purpose | Parallel |
|-----------|---------|----------|
| api-designer | Design hardware abstraction API | Yes |
| code-documentation-generator | Document hardware interfaces | After impl |

## Parallelization Rules

1. **Yes** = Can run in parallel with other "Yes" sub-agents
2. **First** = Must run before other sub-agents
3. **After X** = Must wait for sub-agent X to complete

## Adding New Mappings

When adding a new main agent:
1. Identify which sub-agents provide relevant expertise
2. Determine parallelization dependencies
3. Add mapping to this document
4. Update the main agent's XML file with `<sub_agents>` section
