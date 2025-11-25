"""
Task File Store - File-based context storage for zero-token context sharing.

Instead of passing context between agents via XML, agents read/write to
a structured file store. This eliminates context token overhead entirely.

Directory Structure:
    .tasks/
        manifest.json           # Session state and task registry
        PM/
            output.json         # Structured output (summary, next_steps, warnings)
            artifacts.json      # List of created file paths
        ARCHITECT/
            output.json
            artifacts.json
            decisions.json      # Architectural decisions
        ...
"""

import fcntl
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agentic_builder.common.logging_config import get_logger
from agentic_builder.common.types import AgentType

logger = get_logger(__name__)


class TaskFileStore:
    """File-based task context store for efficient agent communication."""

    TASKS_DIR = ".tasks"

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.tasks_dir = self.project_root / self.TASKS_DIR
        self._ensure_gitignore()

    def _ensure_gitignore(self):
        """Ensure .tasks directory is gitignored."""
        gitignore = self.project_root / ".gitignore"
        entry = f"\n{self.TASKS_DIR}/\n"

        if gitignore.exists():
            content = gitignore.read_text()
            if self.TASKS_DIR not in content:
                with open(gitignore, "a") as f:
                    f.write(entry)
        else:
            gitignore.write_text(entry)

    def initialize_session(
        self,
        session_id: str,
        workflow: str,
        project_idea: str,
        agents: List[AgentType],
    ) -> None:
        """Initialize task store for a new session."""
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "session_id": session_id,
            "workflow": workflow,
            "project_idea": project_idea,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "agents": [a.value for a in agents],
            "tasks": {},
            "completed": [],
            "in_progress": [],
            "pending": [a.value for a in agents],
        }

        self._write_manifest(manifest)
        logger.debug(f"Initialized task store for session {session_id}")

    def get_manifest(self) -> Dict[str, Any]:
        """Read the session manifest."""
        manifest_path = self.tasks_dir / "manifest.json"
        if not manifest_path.exists():
            return {}
        return self._read_json_with_lock(manifest_path)

    def _write_manifest(self, manifest: Dict[str, Any]) -> None:
        """Write manifest with file locking for parallel safety."""
        manifest_path = self.tasks_dir / "manifest.json"
        self._write_json_with_lock(manifest_path, manifest)

    def start_task(self, agent_type: AgentType) -> None:
        """Mark a task as in-progress."""
        manifest = self.get_manifest()
        agent_name = agent_type.value

        # Update manifest state
        if agent_name in manifest.get("pending", []):
            manifest["pending"].remove(agent_name)
        if agent_name not in manifest.get("in_progress", []):
            manifest["in_progress"].append(agent_name)

        # Create task entry
        manifest.setdefault("tasks", {})[agent_name] = {
            "status": "in_progress",
            "started_at": datetime.utcnow().isoformat() + "Z",
        }

        self._write_manifest(manifest)

        # Create agent directory
        agent_dir = self.tasks_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Started task for {agent_name}")

    def complete_task(
        self,
        agent_type: AgentType,
        summary: str,
        artifacts: List[str],
        next_steps: List[str] = None,
        warnings: List[str] = None,
        decisions: Dict[str, Any] = None,
        tokens_used: int = 0,
    ) -> None:
        """Complete a task and store its outputs."""
        agent_name = agent_type.value
        agent_dir = self.tasks_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)

        # Write output.json
        output = {
            "summary": summary,
            "next_steps": next_steps or [],
            "warnings": warnings or [],
            "completed_at": datetime.utcnow().isoformat() + "Z",
        }
        self._write_json_with_lock(agent_dir / "output.json", output)

        # Write artifacts.json
        self._write_json_with_lock(agent_dir / "artifacts.json", {"files": artifacts})

        # Write decisions.json if provided (for ARCHITECT, TL_* agents)
        if decisions:
            self._write_json_with_lock(agent_dir / "decisions.json", decisions)

        # Update manifest
        manifest = self.get_manifest()
        if agent_name in manifest.get("in_progress", []):
            manifest["in_progress"].remove(agent_name)
        if agent_name not in manifest.get("completed", []):
            manifest["completed"].append(agent_name)

        manifest["tasks"][agent_name].update(
            {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "tokens_used": tokens_used,
                "artifact_count": len(artifacts),
            }
        )

        self._write_manifest(manifest)
        logger.debug(f"Completed task for {agent_name}: {len(artifacts)} artifacts")

    def fail_task(self, agent_type: AgentType, error: str) -> None:
        """Mark a task as failed."""
        agent_name = agent_type.value
        manifest = self.get_manifest()

        if agent_name in manifest.get("in_progress", []):
            manifest["in_progress"].remove(agent_name)

        manifest["tasks"][agent_name].update(
            {
                "status": "failed",
                "failed_at": datetime.utcnow().isoformat() + "Z",
                "error": error,
            }
        )

        self._write_manifest(manifest)
        logger.debug(f"Failed task for {agent_name}: {error}")

    def get_task_output(self, agent_type: AgentType) -> Optional[Dict[str, Any]]:
        """Get output from a completed task."""
        agent_dir = self.tasks_dir / agent_type.value
        output_path = agent_dir / "output.json"
        if output_path.exists():
            return self._read_json_with_lock(output_path)
        return None

    def get_task_artifacts(self, agent_type: AgentType) -> List[str]:
        """Get artifacts from a completed task."""
        agent_dir = self.tasks_dir / agent_type.value
        artifacts_path = agent_dir / "artifacts.json"
        if artifacts_path.exists():
            data = self._read_json_with_lock(artifacts_path)
            return data.get("files", [])
        return []

    def get_task_decisions(self, agent_type: AgentType) -> Optional[Dict[str, Any]]:
        """Get architectural decisions from a task (for ARCHITECT, TL_* agents)."""
        agent_dir = self.tasks_dir / agent_type.value
        decisions_path = agent_dir / "decisions.json"
        if decisions_path.exists():
            return self._read_json_with_lock(decisions_path)
        return None

    def is_task_completed(self, agent_type: AgentType) -> bool:
        """Check if a task is completed."""
        manifest = self.get_manifest()
        return agent_type.value in manifest.get("completed", [])

    def get_completed_agents(self) -> List[AgentType]:
        """Get list of completed agent types."""
        manifest = self.get_manifest()
        completed = manifest.get("completed", [])
        result = []
        for name in completed:
            try:
                result.append(AgentType(name))
            except ValueError:
                pass  # Skip unknown agent types
        return result

    def get_dependency_context(
        self,
        agent_type: AgentType,
        dependencies: List[AgentType],
    ) -> Dict[str, Dict[str, Any]]:
        """Get context from all dependencies for an agent."""
        context = {}
        for dep in dependencies:
            output = self.get_task_output(dep)
            artifacts = self.get_task_artifacts(dep)
            decisions = self.get_task_decisions(dep)

            if output or artifacts or decisions:
                context[dep.value] = {
                    "output": output,
                    "artifacts": artifacts,
                    "decisions": decisions,
                }

        return context

    def _read_json_with_lock(self, path: Path) -> Dict[str, Any]:
        """Read JSON file with shared lock for concurrent access."""
        with open(path, "r") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def _write_json_with_lock(self, path: Path, data: Dict[str, Any]) -> None:
        """Write JSON file with exclusive lock for atomic updates."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def cleanup(self) -> None:
        """Remove task store (for testing or cleanup)."""
        import shutil

        if self.tasks_dir.exists():
            shutil.rmtree(self.tasks_dir)
            logger.debug("Cleaned up task store")
