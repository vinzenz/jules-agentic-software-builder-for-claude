# CLAUDE.md - AI Assistant Guidelines

This document provides guidance for AI assistants working on the Jules Agentic Software Builder for Claude project.

## Project Overview

**Repository:** jules-agentic-software-builder-for-claude
**Status:** Initial Development Phase
**Purpose:** An agentic software builder tool designed to work with Claude AI for automated software development tasks.

## Codebase Structure

```
jules-agentic-software-builder-for-claude/
├── CLAUDE.md          # AI assistant guidelines (this file)
├── README.md          # Project documentation
└── (project structure to be established)
```

### Planned Architecture

As this project develops, the following structure is recommended:

```
├── src/               # Source code
│   ├── agents/        # Agent implementations
│   ├── builders/      # Software builder modules
│   ├── utils/         # Utility functions
│   └── index.ts       # Main entry point
├── tests/             # Test files
├── docs/              # Documentation
├── config/            # Configuration files
└── examples/          # Usage examples
```

## Development Workflows

### Getting Started

1. Clone the repository
2. Install dependencies (once package.json is established)
3. Review this CLAUDE.md for conventions

### Git Workflow

- **Main branch:** Contains stable, production-ready code
- **Feature branches:** Use descriptive names like `feature/agent-builder`, `fix/error-handling`
- **Commit messages:** Use conventional commits format:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation changes
  - `refactor:` for code refactoring
  - `test:` for test additions/changes
  - `chore:` for maintenance tasks

### Code Review

- All changes should be made via pull requests
- Ensure tests pass before merging
- Keep PRs focused and reasonably sized

## Key Conventions

### Code Style

- Use TypeScript for type safety (recommended)
- Follow consistent naming conventions:
  - `camelCase` for variables and functions
  - `PascalCase` for classes and interfaces
  - `UPPER_SNAKE_CASE` for constants
- Keep functions focused and single-purpose
- Document public APIs with JSDoc comments

### File Organization

- One component/module per file
- Group related functionality in directories
- Use index files for clean exports
- Keep test files adjacent to source files or in a parallel `tests/` directory

### Error Handling

- Use explicit error types when possible
- Provide meaningful error messages
- Handle errors at appropriate boundaries
- Log errors with context for debugging

### Testing

- Write tests for new functionality
- Maintain test coverage for critical paths
- Use descriptive test names that explain the scenario
- Follow the Arrange-Act-Assert pattern

## AI Assistant Instructions

### When Working on This Project

1. **Read before modifying:** Always read existing code before making changes
2. **Understand context:** Check related files and dependencies
3. **Preserve conventions:** Follow established patterns in the codebase
4. **Minimal changes:** Only modify what's necessary for the task
5. **Test changes:** Run tests after modifications when available

### Task Planning

- Break complex tasks into smaller steps
- Use TodoWrite to track multi-step tasks
- Complete one step before moving to the next
- Verify each change works before proceeding

### Common Commands

```bash
# Once the project is set up, common commands will include:
npm install        # Install dependencies
npm run build      # Build the project
npm run test       # Run tests
npm run lint       # Check code style
npm run dev        # Start development mode
```

### Areas of Focus

When contributing to this project, pay attention to:

- **Agent reliability:** Ensure agents handle edge cases gracefully
- **Builder modularity:** Keep builder components loosely coupled
- **Error resilience:** Implement proper error handling and recovery
- **Documentation:** Keep docs in sync with code changes
- **Performance:** Consider efficiency in agent loops and build processes

## Project-Specific Notes

### Jules Agentic Builder Concepts

This project implements an agentic approach to software building, which involves:

1. **Task decomposition:** Breaking down software tasks into manageable steps
2. **Autonomous execution:** Agents that can work independently with minimal supervision
3. **Tool integration:** Leveraging Claude's capabilities for code generation and analysis
4. **Iterative refinement:** Building software through progressive improvements

### Integration with Claude

- Design for Claude's context window limitations
- Structure prompts for optimal code generation
- Include validation steps for generated code
- Implement feedback loops for iterative improvement

## Security Considerations

- Never commit secrets, API keys, or credentials
- Use environment variables for sensitive configuration
- Validate all external inputs
- Follow OWASP guidelines for secure coding practices
- Review generated code for security vulnerabilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following these guidelines
4. Submit a pull request with clear description
5. Address review feedback promptly

---

*This document should be updated as the project evolves. Keep it current with actual conventions and structures used in the codebase.*
