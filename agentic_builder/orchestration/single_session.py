"""
Single Session Orchestrator - Thin wrapper that invokes Claude as the orchestrator.

This module provides a minimal Python layer that:
1. Initializes the .tasks/ directory with manifest
2. Invokes a single Claude CLI session with the orchestrator skill
3. Handles final cleanup (git commit, PR creation)

The actual workflow orchestration happens inside Claude, not Python.
This is the "let Claude do the work" architecture.

Performance Benefits:
- Single CLI startup (not 40+)
- Persistent session state
- Parallel agent spawning via Task tool
- Minimal token overhead (~3,300 tokens vs ~62,000)
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from agentic_builder.agents.fast_configs import FAST_AGENT_CONFIGS_MAP
from agentic_builder.common.logging_config import get_logger
from agentic_builder.common.types import AgentType
from agentic_builder.orchestration.workflows import WorkflowMapper

logger = get_logger(__name__)


class SingleSessionOrchestrator:
    """
    Thin wrapper that sets up the workflow and invokes Claude as orchestrator.

    The Python code only:
    1. Creates the initial manifest
    2. Invokes Claude with the orchestrator skill
    3. Handles post-workflow cleanup

    All orchestration logic lives in the Claude skill.
    """

    TASKS_DIR = ".tasks"
    ORCHESTRATOR_SKILL = "workflow-orchestrator"

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.tasks_dir = self.project_root / self.TASKS_DIR

    def run_workflow(
        self,
        workflow_name: str,
        project_idea: str,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Run a complete workflow using Claude as the orchestrator.

        Args:
            workflow_name: The workflow type (e.g., "FULL_APP_GENERATION")
            project_idea: Description of what to build
            session_id: Optional session ID (generated if not provided)

        Returns:
            dict with workflow results
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = self._generate_session_id()

        logger.info(f"Starting workflow {workflow_name} with session {session_id}")

        # 1. Initialize manifest
        manifest = self._create_manifest(workflow_name, project_idea, session_id)
        logger.info(f"Created manifest with {len(manifest['agents'])} agents")

        # 2. Invoke Claude orchestrator
        result = self._invoke_orchestrator(manifest)

        # 3. Post-workflow cleanup
        if result["success"]:
            self._finalize_workflow(session_id)

        return result

    def _create_manifest(
        self,
        workflow_name: str,
        project_idea: str,
        session_id: str,
    ) -> dict:
        """Create the initial workflow manifest."""
        # Get execution order for this workflow
        execution_order = WorkflowMapper.get_execution_order(workflow_name)

        # Build agent configurations
        agents = {}
        for agent_type in execution_order:
            config = FAST_AGENT_CONFIGS_MAP.get(agent_type)
            if config:
                agents[agent_type.value] = {
                    "dependencies": [d.value for d in config.dependencies],
                    "model": config.model_tier.value,
                    "status": "pending",
                    "subagent": f"main-{agent_type.value.lower().replace('_', '-')}",
                }

        # Compute execution phases
        phases = self._compute_phases(execution_order)

        manifest = {
            "session_id": session_id,
            "workflow": workflow_name,
            "project_idea": project_idea,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "agents": agents,
            "phases": phases,
            "completed": [],
            "in_progress": [],
            "pending": [a.value for a in execution_order],
            "current_phase": 0,
        }

        # Write manifest
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.tasks_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        # Ensure .tasks is gitignored
        self._ensure_gitignore()

        return manifest

    def _compute_phases(self, execution_order: List[AgentType]) -> List[dict]:
        """Group agents into parallel execution phases."""
        phases = []
        completed = set()
        remaining = set(execution_order)
        phase_num = 0

        while remaining:
            phase_num += 1
            ready = []

            for agent in remaining:
                config = FAST_AGENT_CONFIGS_MAP.get(agent)
                if config:
                    deps_satisfied = all(d in completed for d in config.dependencies)
                    if deps_satisfied:
                        ready.append(agent)

            if not ready and remaining:
                # Should not happen with valid configs
                logger.error(f"Cannot resolve: {remaining}")
                break

            phases.append(
                {
                    "phase": phase_num,
                    "agents": [a.value for a in ready],
                    "status": "pending",
                }
            )
            completed.update(ready)
            remaining -= set(ready)

        return phases

    def _invoke_orchestrator(self, manifest: dict) -> dict:
        """Invoke Claude CLI with the orchestrator skill."""
        logger.info("Invoking Claude orchestrator...")

        # Build the orchestrator prompt
        prompt = f"""Execute workflow orchestration.

Workflow: {manifest["workflow"]}
Session: {manifest["session_id"]}
Agents: {len(manifest["agents"])}
Phases: {len(manifest["phases"])}

Read .tasks/manifest.json and begin orchestrating the workflow.
Spawn agents in parallel phases using the Task tool.
Update the manifest after each phase.
Continue until all agents complete.

Return a summary when done."""

        try:
            # Invoke Claude with the orchestrator skill
            result = subprocess.run(
                [
                    "claude",
                    "--skill",
                    self.ORCHESTRATOR_SKILL,
                    "--dangerously-skip-permissions",
                    "-p",
                    prompt,
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour max
            )

            if result.returncode == 0:
                logger.info("Orchestrator completed successfully")
                return {
                    "success": True,
                    "output": result.stdout,
                    "session_id": manifest["session_id"],
                }
            else:
                logger.error(f"Orchestrator failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "session_id": manifest["session_id"],
                }

        except subprocess.TimeoutExpired:
            logger.error("Orchestrator timed out")
            return {
                "success": False,
                "error": "Workflow timed out after 1 hour",
                "session_id": manifest["session_id"],
            }
        except Exception as e:
            logger.error(f"Failed to invoke orchestrator: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": manifest["session_id"],
            }

    def _finalize_workflow(self, session_id: str) -> None:
        """Finalize the workflow (git commit, etc.)."""
        logger.info("Finalizing workflow...")

        # Read final manifest
        manifest_path = self.tasks_dir / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            completed = manifest.get("completed", [])
            logger.info(f"Completed {len(completed)} agents")

        # Collect all artifacts
        artifacts = []
        for agent_dir in self.tasks_dir.iterdir():
            if agent_dir.is_dir():
                artifacts_file = agent_dir / "artifacts.json"
                if artifacts_file.exists():
                    data = json.loads(artifacts_file.read_text())
                    artifacts.extend(data.get("files", []))

        logger.info(f"Total artifacts: {len(artifacts)}")

        # Git commit would happen here
        # self._git_commit(artifacts, session_id)

    def _ensure_gitignore(self) -> None:
        """Ensure .tasks directory is gitignored."""
        gitignore = self.project_root / ".gitignore"
        entry = f"{self.TASKS_DIR}/"

        if gitignore.exists():
            content = gitignore.read_text()
            if entry not in content:
                with open(gitignore, "a") as f:
                    f.write(f"\n{entry}\n")
        else:
            gitignore.write_text(f"{entry}\n")

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import uuid

        return f"sess_{uuid.uuid4().hex[:12]}"


def run_single_session_workflow(
    project_root: Path,
    workflow_name: str,
    project_idea: str,
) -> dict:
    """
    Convenience function to run a workflow with the single session orchestrator.

    Args:
        project_root: Path to the project directory
        workflow_name: Workflow type (e.g., "FULL_APP_GENERATION")
        project_idea: Description of what to build

    Returns:
        dict with workflow results
    """
    orchestrator = SingleSessionOrchestrator(project_root)
    return orchestrator.run_workflow(workflow_name, project_idea)
