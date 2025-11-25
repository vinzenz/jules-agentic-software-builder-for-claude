"""
Parallel Workflow Engine - Async execution of agents in phases.

Agents with satisfied dependencies run concurrently, reducing total
workflow time from O(n) to O(depth) where depth is the longest
dependency chain.

Performance Comparison:
    Sequential (40 agents @ 2min each): 80 minutes
    Parallel (6 phases @ avg 3min each): 14 minutes
    Speedup: 5.7x
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from agentic_builder.agents.configs import get_agent_config
from agentic_builder.common.events import EventEmitter
from agentic_builder.common.logging_config import get_logger, log_separator
from agentic_builder.common.types import AgentType, WorkflowStatus
from agentic_builder.orchestration.session_manager import SessionManager
from agentic_builder.orchestration.workflows import WorkflowMapper
from agentic_builder.pms.minimal_context import MinimalContextSerializer
from agentic_builder.pms.task_file_store import TaskFileStore

logger = get_logger(__name__)


@dataclass
class ExecutionPhase:
    """A phase of agents that can run in parallel."""

    phase_number: int
    agents: List[AgentType]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class PhaseResult:
    """Result of executing a phase."""

    phase: ExecutionPhase
    success: bool
    failed_agents: List[AgentType] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class WorkflowMetrics:
    """Metrics for workflow execution."""

    total_time_seconds: float = 0.0
    agent_times: Dict[str, float] = field(default_factory=dict)
    parallel_efficiency: float = 0.0  # actual_time / sequential_time
    token_usage: Dict[str, int] = field(default_factory=dict)
    phases_count: int = 0
    agents_count: int = 0

    def report(self) -> str:
        """Generate metrics report."""
        lines = [
            f"Total time: {self.total_time_seconds:.1f}s",
            f"Phases: {self.phases_count}",
            f"Agents: {self.agents_count}",
            f"Parallel efficiency: {self.parallel_efficiency:.1%}",
        ]
        if self.agent_times:
            slowest = max(self.agent_times, key=self.agent_times.get)
            lines.append(f"Slowest agent: {slowest} ({self.agent_times[slowest]:.1f}s)")
        return "\n".join(lines)


class ParallelWorkflowEngine(EventEmitter):
    """
    Async workflow engine that runs agents in parallel phases.

    Agents are grouped into phases based on dependency resolution.
    All agents in a phase run concurrently, then the next phase starts.
    """

    def __init__(
        self,
        session_manager: SessionManager,
        claude_client,
        git_manager,
        pr_manager,
        max_concurrent: int = 10,
    ):
        super().__init__()
        self.session_manager = session_manager
        self.claude = claude_client
        self.git = git_manager
        self.pr_manager = pr_manager
        self.max_concurrent = max_concurrent
        self._active_runs: Dict[str, bool] = {}
        self._semaphore: Optional[asyncio.Semaphore] = None

    def start_workflow(self, workflow_name: str, idea: Optional[str] = None) -> str:
        """Start workflow (sync wrapper for async execution)."""
        return asyncio.run(self._start_workflow_async(workflow_name, idea))

    async def _start_workflow_async(self, workflow_name: str, idea: Optional[str] = None) -> str:
        """Start and run workflow asynchronously."""
        log_separator(logger, f"STARTING PARALLEL WORKFLOW: {workflow_name}")

        session = self.session_manager.create_session(workflow_name, idea=idea)
        self.session_manager.update_status(session.id, WorkflowStatus.RUNNING)
        self._active_runs[session.id] = True
        self.emit("workflow_started", session.id)

        # Initialize task file store
        task_store = TaskFileStore(self.session_manager.output_dir)
        execution_order = WorkflowMapper.get_execution_order(workflow_name)
        task_store.initialize_session(session.id, workflow_name, idea or "", execution_order)

        # Create git branch
        branch_name = f"feature/{session.id}"
        try:
            self.git.create_branch(branch_name)
        except Exception:
            try:
                self.git.checkout_branch(branch_name)
            except Exception as e:
                logger.error(f"Failed to create/switch branch: {e}")
                raise

        # Create CLAUDE.md
        if idea:
            self._create_claude_md(session.id, workflow_name, idea, execution_order)

        try:
            metrics = await self._run_parallel(session.id, task_store)
            logger.info(f"Workflow completed:\n{metrics.report()}")
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            self.session_manager.update_status(session.id, WorkflowStatus.FAILED)
            self.emit("workflow_failed", {"id": session.id, "error": str(e)})
            raise

        # Finalize
        if session.id in self._active_runs:
            self.session_manager.update_status(session.id, WorkflowStatus.COMPLETED)
            del self._active_runs[session.id]
            self._create_pr(session.id, workflow_name)
            self.emit("workflow_completed", session.id)

        return session.id

    async def _run_parallel(self, session_id: str, task_store: TaskFileStore) -> WorkflowMetrics:
        """Run agents in parallel phases."""
        session = self.session_manager.load_session(session_id)
        execution_order = WorkflowMapper.get_execution_order(session.workflow_name)

        # Compute phases
        phases = self._compute_phases(execution_order)
        logger.info(f"Computed {len(phases)} execution phases")
        for phase in phases:
            logger.debug(f"Phase {phase.phase_number}: {[a.value for a in phase.agents]}")

        # Initialize semaphore for max concurrency
        self._semaphore = asyncio.Semaphore(self.max_concurrent)

        # Track metrics
        metrics = WorkflowMetrics(
            phases_count=len(phases),
            agents_count=len(execution_order),
        )
        start_time = datetime.now()
        sequential_time = 0.0

        # Skip already completed agents
        completed = set(task_store.get_completed_agents())

        # Execute phases
        for phase in phases:
            if session_id not in self._active_runs:
                break  # Cancelled

            # Filter out completed agents
            pending_agents = [a for a in phase.agents if a not in completed]
            if not pending_agents:
                logger.debug(f"Phase {phase.phase_number}: all agents already completed")
                continue

            log_separator(logger, f"PHASE {phase.phase_number}: {len(pending_agents)} agents")
            phase_result = await self._execute_phase(session_id, task_store, phase, pending_agents, metrics)

            if not phase_result.success:
                raise Exception(f"Phase {phase.phase_number} failed: {phase_result.failed_agents}")

            # Add to sequential time estimate
            for agent in pending_agents:
                agent_time = metrics.agent_times.get(agent.value, 120.0)
                sequential_time += agent_time

        # Calculate final metrics
        total_time = (datetime.now() - start_time).total_seconds()
        metrics.total_time_seconds = total_time
        metrics.parallel_efficiency = total_time / sequential_time if sequential_time > 0 else 1.0

        return metrics

    async def _execute_phase(
        self,
        session_id: str,
        task_store: TaskFileStore,
        phase: ExecutionPhase,
        agents: List[AgentType],
        metrics: WorkflowMetrics,
    ) -> PhaseResult:
        """Execute all agents in a phase concurrently."""
        phase.started_at = datetime.now()

        # Create tasks for all agents
        tasks = [self._execute_agent(session_id, task_store, agent, metrics) for agent in agents]

        # Run concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        phase.completed_at = datetime.now()
        duration = (phase.completed_at - phase.started_at).total_seconds()

        # Check for failures
        failed_agents = []
        for agent, result in zip(agents, results):
            if isinstance(result, Exception):
                logger.error(f"Agent {agent.value} failed: {result}")
                failed_agents.append(agent)
                task_store.fail_task(agent, str(result))
            elif not result:
                failed_agents.append(agent)

        return PhaseResult(
            phase=phase,
            success=len(failed_agents) == 0,
            failed_agents=failed_agents,
            duration_seconds=duration,
        )

    async def _execute_agent(
        self,
        session_id: str,
        task_store: TaskFileStore,
        agent_type: AgentType,
        metrics: WorkflowMetrics,
    ) -> bool:
        """Execute a single agent asynchronously."""
        async with self._semaphore:
            start_time = datetime.now()
            logger.info(f"Starting agent: {agent_type.value}")
            self.emit("agent_spawned", {"agent": agent_type})

            try:
                task_store.start_task(agent_type)
                config = get_agent_config(agent_type)

                # Generate minimal context (< 100 tokens!)
                session = self.session_manager.load_session(session_id)
                context = MinimalContextSerializer.serialize(
                    agent_type,
                    config.dependencies,
                    project_idea=session.idea if agent_type == AgentType.PM else None,
                )

                # Call Claude asynchronously
                response = await self._call_claude_async(agent_type, config, context)

                if not response.success:
                    raise Exception(response.summary)

                # Process artifacts
                artifacts = self._process_artifacts(response, agent_type)

                # Store task output
                task_store.complete_task(
                    agent_type=agent_type,
                    summary=response.summary,
                    artifacts=artifacts,
                    next_steps=response.next_steps,
                    warnings=response.warnings,
                    tokens_used=response.metadata.get("tokensUsed", 0),
                )

                # Track metrics
                duration = (datetime.now() - start_time).total_seconds()
                metrics.agent_times[agent_type.value] = duration
                metrics.token_usage[agent_type.value] = response.metadata.get("tokensUsed", 0)

                self.emit("agent_completed", {"agent": agent_type, "summary": response.summary})
                logger.info(f"Completed agent: {agent_type.value} ({duration:.1f}s)")
                return True

            except Exception as e:
                logger.error(f"Agent {agent_type.value} failed: {e}")
                self.emit("agent_failed", {"agent": agent_type, "error": str(e)})
                return False

    async def _call_claude_async(self, agent_type, config, context: str):
        """Call Claude CLI asynchronously using subprocess."""
        prompt = f"Execute {agent_type.value} phase"

        # Get context instructions to add to system prompt
        context_instructions = MinimalContextSerializer.get_context_instructions(agent_type)

        # Build command
        cmd = [
            "claude",
            "--model",
            config.model_tier.value,
            "--dangerously-skip-permissions",
            "--tools",
            "default",
            "-p",
            prompt,
            "-",
        ]

        # Add context instructions to the input
        full_input = f"{context_instructions}\n\n{context}"

        # Run async subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.session_manager.output_dir),
        )

        stdout, stderr = await process.communicate(full_input.encode())

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise Exception(f"Claude CLI failed: {error_msg}")

        # Parse response (reuse existing parser)
        from agentic_builder.agents.response_parser import ResponseParser

        return ResponseParser.parse(stdout.decode())

    def _process_artifacts(self, response, agent_type: AgentType) -> List[str]:
        """Process and validate artifacts from response."""
        artifacts = []
        root_path = self.session_manager.output_dir.resolve()

        for artifact in response.artifacts:
            if artifact.type == "file" and artifact.path:
                artifact_path = Path(artifact.path)
                if artifact_path.is_absolute():
                    fpath = artifact_path.resolve()
                else:
                    fpath = (root_path / artifact_path).resolve()

                if not fpath.is_relative_to(root_path):
                    logger.warning(f"Security: path outside repo: {fpath}")
                    continue

                if fpath.exists():
                    artifacts.append(str(fpath))
                else:
                    logger.warning(f"File not found: {fpath}")

        return artifacts

    def _compute_phases(self, execution_order: List[AgentType]) -> List[ExecutionPhase]:
        """
        Group agents into phases where all agents in a phase can run in parallel.

        Algorithm:
        1. Start with agents that have no dependencies (or all deps satisfied)
        2. Add them to current phase
        3. Mark them as "completed"
        4. Repeat until all agents are assigned to phases
        """
        phases: List[ExecutionPhase] = []
        completed: Set[AgentType] = set()
        remaining = set(execution_order)
        phase_num = 0

        while remaining:
            phase_num += 1
            ready = []

            for agent in remaining:
                config = get_agent_config(agent)
                deps_satisfied = all(dep in completed for dep in config.dependencies)
                if deps_satisfied:
                    ready.append(agent)

            if not ready:
                # All remaining agents have unsatisfied dependencies
                # This shouldn't happen with valid workflow configs
                logger.error(f"Circular dependency or missing agent: {remaining}")
                raise RuntimeError(f"Cannot resolve dependencies for: {remaining}")

            phases.append(ExecutionPhase(phase_number=phase_num, agents=ready))
            completed.update(ready)
            remaining -= set(ready)

        return phases

    def _create_claude_md(
        self,
        session_id: str,
        workflow_name: str,
        idea: str,
        execution_order: List[AgentType],
    ) -> None:
        """Create CLAUDE.md with project context."""
        project_root = self.session_manager.output_dir
        claude_md_path = project_root / "CLAUDE.md"

        agent_list = "\n".join([f"- **{agent.value}**" for agent in execution_order])

        content = f"""# CLAUDE.md - Project Context

**Session ID:** {session_id}
**Workflow:** {workflow_name}
**Started:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Project Idea

{idea}

## Agent Context System

This project uses a file-based context system for efficient agent communication.
All agent outputs are stored in `.tasks/` directory (gitignored).

### Reading Context
- `.tasks/manifest.json` - Session state and project idea
- `.tasks/{{AGENT}}/output.json` - Agent outputs
- `.tasks/{{AGENT}}/artifacts.json` - Created file paths
- `.tasks/{{AGENT}}/decisions.json` - Design decisions

### Agent Workflow

{agent_list}

---
*Generated by Agentic Builder (Parallel Engine)*
"""

        claude_md_path.write_text(content)
        try:
            self.git.commit_files([str(claude_md_path)], "[INIT] Create CLAUDE.md")
        except Exception as e:
            logger.warning(f"Failed to commit CLAUDE.md: {e}")

    def _create_pr(self, session_id: str, workflow_name: str) -> None:
        """Create pull request for the workflow."""
        try:
            self.pr_manager.create_pr(
                branch=f"feature/{session_id}",
                title=f"Workflow {workflow_name}",
                body="Generated by Agentic Builder (Parallel Engine)",
            )
        except Exception as e:
            logger.warning(f"Failed to create PR: {e}")

    def cancel_workflow(self, session_id: str) -> None:
        """Cancel a running workflow."""
        if session_id in self._active_runs:
            del self._active_runs[session_id]
        self.session_manager.update_status(session_id, WorkflowStatus.CANCELLED)
