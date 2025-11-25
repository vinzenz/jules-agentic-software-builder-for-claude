"""
Batched Git Manager - Phase-based commits for reduced overhead.

Instead of committing after every agent (40 commits), we batch commits
by execution phase (6 commits).

Performance Comparison:
    Individual commits: 40 × 1s = 40 seconds overhead
    Batched commits: 6 × 1s = 6 seconds overhead
    Savings: 85%
"""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from agentic_builder.common.logging_config import get_logger
from agentic_builder.common.types import AgentType

logger = get_logger(__name__)


@dataclass
class StagedChange:
    """A staged file change waiting to be committed."""

    file_path: str
    agent: AgentType
    summary: str


@dataclass
class CommitPhase:
    """A collection of changes for a single commit."""

    name: str
    changes: List[StagedChange] = field(default_factory=list)

    @property
    def files(self) -> List[str]:
        return [c.file_path for c in self.changes]

    @property
    def message(self) -> str:
        """Generate commit message for this phase."""
        if not self.changes:
            return f"[{self.name}] No changes"

        # Group by agent
        agents = sorted(set(c.agent.value for c in self.changes))

        if len(agents) == 1:
            # Single agent
            agent = agents[0]
            summary = self.changes[0].summary[:50]
            return f"[{agent}] {summary}"

        # Multiple agents - create summary
        lines = [f"[{self.name}]", ""]
        for agent in agents:
            agent_changes = [c for c in self.changes if c.agent.value == agent]
            summary = agent_changes[0].summary[:40]
            file_count = len(agent_changes)
            lines.append(f"- {agent}: {summary} ({file_count} files)")

        return "\n".join(lines)


class BatchedGitManager:
    """
    Git manager that batches commits by phase for reduced overhead.

    Usage:
        git = BatchedGitManager(repo_path)
        git.start_phase("Planning")

        # ... agents run and create files ...
        git.stage_change("file.py", AgentType.PM, "Created requirements")

        git.commit_phase()  # Single commit for all changes in phase
    """

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        self.current_phase: Optional[CommitPhase] = None
        self._pending_phases: List[CommitPhase] = []

    def start_phase(self, phase_name: str) -> None:
        """Start a new commit phase."""
        if self.current_phase and self.current_phase.changes:
            # Auto-commit previous phase if it has changes
            self.commit_phase()

        self.current_phase = CommitPhase(name=phase_name)
        logger.debug(f"Started git phase: {phase_name}")

    def stage_change(
        self,
        file_path: str,
        agent: AgentType,
        summary: str,
    ) -> None:
        """Stage a file change for the current phase."""
        if not self.current_phase:
            self.start_phase("Default")

        change = StagedChange(
            file_path=str(file_path),
            agent=agent,
            summary=summary,
        )
        self.current_phase.changes.append(change)
        logger.debug(f"Staged: {file_path} ({agent.value})")

    def stage_files(
        self,
        files: List[str],
        agent: AgentType,
        summary: str,
    ) -> None:
        """Stage multiple files for the current phase."""
        for file_path in files:
            self.stage_change(file_path, agent, summary)

    def commit_phase(self) -> bool:
        """Commit all changes in the current phase."""
        if not self.current_phase or not self.current_phase.changes:
            logger.debug("No changes to commit in current phase")
            return True

        files = self.current_phase.files
        message = self.current_phase.message

        try:
            # Git add
            self._run_git(["add"] + files)

            # Git commit
            self._run_git(["commit", "-m", message])

            logger.info(f"Committed phase '{self.current_phase.name}': {len(files)} files")
            self._pending_phases.append(self.current_phase)
            self.current_phase = None
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Git commit failed: {e}")
            return False

    def commit_all_pending(self) -> int:
        """Commit any remaining staged changes."""
        committed = 0

        if self.current_phase and self.current_phase.changes:
            if self.commit_phase():
                committed += 1

        return committed

    def create_branch(self, branch_name: str) -> bool:
        """Create and checkout a new branch."""
        try:
            self._run_git(["checkout", "-b", branch_name])
            logger.info(f"Created branch: {branch_name}")
            return True
        except subprocess.CalledProcessError:
            # Branch might exist, try checkout
            try:
                self._run_git(["checkout", branch_name])
                logger.info(f"Checked out existing branch: {branch_name}")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create/checkout branch: {e}")
                return False

    def get_stats(self) -> dict:
        """Get statistics about batched commits."""
        total_changes = sum(len(p.changes) for p in self._pending_phases)
        return {
            "phases_committed": len(self._pending_phases),
            "total_files_committed": total_changes,
            "phases": [p.name for p in self._pending_phases],
        }

    def _run_git(self, args: List[str]) -> str:
        """Run a git command."""
        cmd = ["git"] + args
        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout


class PhaseCommitStrategy:
    """
    Defines commit phases for different workflow types.

    Standard phases:
    1. Init - CLAUDE.md, manifest
    2. Planning - PM output
    3. Architecture - ARCHITECT, UIUX_* outputs
    4. Implementation - All TL_*, DEV_* code
    5. Quality - TEST, CQR, SR reports
    6. Operations - DOE outputs (CI/CD, Docker)
    """

    PHASES = {
        "INIT": ["CLAUDE.md", "manifest"],
        "PLANNING": ["PM"],
        "ARCHITECTURE": ["ARCHITECT", "UIUX_GUI", "UIUX_CLI"],
        "IMPLEMENTATION": [
            "TL_UI_WEB",
            "TL_UI_MOBILE",
            "TL_UI_DESKTOP",
            "TL_UI_CLI",
            "TL_CORE_API",
            "TL_CORE_SYSTEMS",
            "TL_CORE_LIBRARY",
            "DEV_UI_WEB",
            "DEV_UI_MOBILE",
            "DEV_UI_DESKTOP",
            "DEV_UI_CLI",
            "DEV_CORE_API",
            "DEV_CORE_SYSTEMS",
            "DEV_CORE_LIBRARY",
            "DEV_PLATFORM_IOS",
            "DEV_PLATFORM_ANDROID",
            "DEV_PLATFORM_WINDOWS",
            "DEV_PLATFORM_LINUX",
            "DEV_PLATFORM_MACOS",
            "DEV_PLATFORM_EMBEDDED",
            "DEV_INTEGRATION_DATABASE",
            "DEV_INTEGRATION_API",
            "DEV_INTEGRATION_NETWORK",
            "DEV_INTEGRATION_HARDWARE",
        ],
        "CONTENT": ["TL_CONTENT", "DEV_CONTENT", "TL_GRAPHICS", "DEV_GRAPHICS"],
        "QUALITY": ["TEST", "CQR", "SR"],
        "OPERATIONS": ["DOE"],
    }

    @classmethod
    def get_phase_for_agent(cls, agent: AgentType) -> str:
        """Get the commit phase for an agent."""
        agent_name = agent.value
        for phase, agents in cls.PHASES.items():
            if agent_name in agents:
                return phase
        return "IMPLEMENTATION"  # Default

    @classmethod
    def get_phase_order(cls) -> List[str]:
        """Get ordered list of phases."""
        return [
            "INIT",
            "PLANNING",
            "ARCHITECTURE",
            "IMPLEMENTATION",
            "CONTENT",
            "QUALITY",
            "OPERATIONS",
        ]
