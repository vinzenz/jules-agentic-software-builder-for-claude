"""Tests for the new performance optimization modules."""

import tempfile
from pathlib import Path

from agentic_builder.common.types import AgentType


class TestTaskFileStore:
    """Tests for the TaskFileStore class."""

    def test_initialize_session(self):
        """Test session initialization creates manifest."""
        from agentic_builder.pms.task_file_store import TaskFileStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = TaskFileStore(Path(tmpdir))
            store.initialize_session(
                session_id="test123",
                workflow="FULL_APP_GENERATION",
                project_idea="Build a todo app",
                agents=[AgentType.PM, AgentType.ARCHITECT],
            )

            manifest = store.get_manifest()
            assert manifest["session_id"] == "test123"
            assert manifest["workflow"] == "FULL_APP_GENERATION"
            assert manifest["project_idea"] == "Build a todo app"
            assert "PM" in manifest["pending"]
            assert "ARCHITECT" in manifest["pending"]

    def test_start_and_complete_task(self):
        """Test task lifecycle: start and complete."""
        from agentic_builder.pms.task_file_store import TaskFileStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = TaskFileStore(Path(tmpdir))
            store.initialize_session(
                session_id="test123",
                workflow="TEST",
                project_idea="Test",
                agents=[AgentType.PM],
            )

            store.start_task(AgentType.PM)
            manifest = store.get_manifest()
            assert "PM" in manifest["in_progress"]
            assert "PM" not in manifest["pending"]

            store.complete_task(
                agent_type=AgentType.PM,
                summary="Completed PM analysis",
                artifacts=["docs/requirements.md"],
                next_steps=["Run architect"],
                warnings=[],
                tokens_used=1000,
            )

            manifest = store.get_manifest()
            assert "PM" in manifest["completed"]
            assert "PM" not in manifest["in_progress"]

    def test_get_task_output(self):
        """Test retrieving task output."""
        from agentic_builder.pms.task_file_store import TaskFileStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = TaskFileStore(Path(tmpdir))
            store.initialize_session(
                session_id="test123",
                workflow="TEST",
                project_idea="Test",
                agents=[AgentType.PM],
            )

            store.start_task(AgentType.PM)
            store.complete_task(
                agent_type=AgentType.PM,
                summary="Test summary",
                artifacts=["file1.py", "file2.py"],
            )

            output = store.get_task_output(AgentType.PM)
            assert output["summary"] == "Test summary"

            artifacts = store.get_task_artifacts(AgentType.PM)
            assert len(artifacts) == 2
            assert "file1.py" in artifacts


class TestMinimalContextSerializer:
    """Tests for MinimalContextSerializer."""

    def test_serialize_pm(self):
        """Test serialization for PM (first agent with project idea)."""
        from agentic_builder.pms.minimal_context import MinimalContextSerializer

        result = MinimalContextSerializer.serialize(
            agent_type=AgentType.PM,
            dependencies=[],
            project_idea="Build a todo app",
        )

        assert "<agent>PM</agent>" in result
        assert "Build a todo app" in result
        assert "<manifest>.tasks/manifest.json</manifest>" in result

    def test_serialize_dependent_agent(self):
        """Test serialization for agents with dependencies."""
        from agentic_builder.pms.minimal_context import MinimalContextSerializer

        result = MinimalContextSerializer.serialize(
            agent_type=AgentType.ARCHITECT,
            dependencies=[AgentType.PM],
        )

        assert "<agent>ARCHITECT</agent>" in result
        assert "<read_from>PM</read_from>" in result
        # Should NOT include project_idea for non-PM agents
        assert "project_idea" not in result

    def test_get_recommended_reads(self):
        """Test recommended read files for different agents."""
        from agentic_builder.pms.minimal_context import MinimalContextSerializer

        # ARCHITECT should read PM output
        reads = MinimalContextSerializer.get_recommended_reads(AgentType.ARCHITECT)
        assert ".tasks/PM/output.json" in reads

        # DEV_UI_WEB should read TL_UI_WEB output
        reads = MinimalContextSerializer.get_recommended_reads(AgentType.DEV_UI_WEB)
        assert ".tasks/TL_UI_WEB/output.json" in reads


class TestFastConfigs:
    """Tests for fast agent configurations."""

    def test_fast_configs_exist(self):
        """Test that fast configs are defined for expected agents."""
        from agentic_builder.agents.fast_configs import FAST_AGENT_CONFIGS_MAP

        assert AgentType.PM in FAST_AGENT_CONFIGS_MAP
        assert AgentType.ARCHITECT in FAST_AGENT_CONFIGS_MAP
        assert AgentType.DEV_UI_WEB in FAST_AGENT_CONFIGS_MAP

    def test_model_tier_distribution(self):
        """Test that model tiers are properly distributed for speed."""
        from agentic_builder.agents.fast_configs import (
            FAST_AGENT_CONFIGS_MAP,
            get_tier_distribution,
        )
        from agentic_builder.common.types import ModelTier

        dist = get_tier_distribution()

        # Should have more Haiku than others for speed
        assert dist.get("haiku", 0) > dist.get("opus", 0)
        assert dist.get("haiku", 0) > dist.get("sonnet", 0)

        # PM should be Opus (critical reasoning)
        assert FAST_AGENT_CONFIGS_MAP[AgentType.PM].model_tier == ModelTier.OPUS

        # DEV agents should be Haiku (fast implementation)
        assert FAST_AGENT_CONFIGS_MAP[AgentType.DEV_UI_WEB].model_tier == ModelTier.HAIKU


class TestBatchedGitManager:
    """Tests for BatchedGitManager."""

    def test_stage_and_commit_phase(self):
        """Test staging files and committing a phase."""
        from agentic_builder.integration.batched_git import BatchedGitManager

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a git repo
            import subprocess

            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmpdir,
                capture_output=True,
            )

            # Create a test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("# test")

            git = BatchedGitManager(Path(tmpdir))
            git.start_phase("Planning")
            git.stage_change(str(test_file), AgentType.PM, "Created requirements")

            assert len(git.current_phase.changes) == 1
            assert git.current_phase.name == "Planning"

    def test_phase_commit_strategy(self):
        """Test phase classification for agents."""
        from agentic_builder.integration.batched_git import PhaseCommitStrategy

        assert PhaseCommitStrategy.get_phase_for_agent(AgentType.PM) == "PLANNING"
        assert PhaseCommitStrategy.get_phase_for_agent(AgentType.ARCHITECT) == "ARCHITECTURE"
        assert PhaseCommitStrategy.get_phase_for_agent(AgentType.DEV_UI_WEB) == "IMPLEMENTATION"
        assert PhaseCommitStrategy.get_phase_for_agent(AgentType.TEST) == "QUALITY"


class TestAdaptiveOrchestrator:
    """Tests for AdaptiveOrchestrator."""

    def test_confidence_levels(self):
        """Test confidence level enum values."""
        from agentic_builder.orchestration.adaptive_orchestrator import ConfidenceLevel

        assert ConfidenceLevel.HIGH == "high"
        assert ConfidenceLevel.MEDIUM == "medium"
        assert ConfidenceLevel.LOW == "low"

    def test_spawn_request_dataclass(self):
        """Test SpawnRequest dataclass."""
        from agentic_builder.orchestration.adaptive_orchestrator import SpawnRequest

        req = SpawnRequest(
            agent="DEV_UI_WEB",
            reason="Implement frontend",
            priority="required",
            context={"framework": "react"},
        )

        assert req.agent == "DEV_UI_WEB"
        assert req.reason == "Implement frontend"
        assert req.context["framework"] == "react"

    def test_skip_decision_dataclass(self):
        """Test SkipDecision dataclass."""
        from agentic_builder.orchestration.adaptive_orchestrator import SkipDecision

        skip = SkipDecision(agent="DEV_UI_MOBILE", reason="Web only project")
        assert skip.agent == "DEV_UI_MOBILE"
        assert skip.reason == "Web only project"

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly."""
        from agentic_builder.orchestration.adaptive_orchestrator import AdaptiveOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            orch = AdaptiveOrchestrator(Path(tmpdir), interactive=False)
            assert orch.project_root == Path(tmpdir)
            assert orch.interactive is False
            assert len(orch.skipped_agents) == 0
            assert len(orch.completed_agents) == 0

    def test_orchestrator_agent_mapping(self):
        """Test agent name to subagent type mapping."""
        from agentic_builder.orchestration.adaptive_orchestrator import AdaptiveOrchestrator

        mapping = AdaptiveOrchestrator.AGENT_MAPPING
        assert mapping["PM"] == "main-pm"
        assert mapping["architect-system"] == "architect-system"
        assert mapping["DEV_UI_WEB"] == "main-dev-ui-web"


class TestSingleSessionOrchestrator:
    """Tests for SingleSessionOrchestrator."""

    def test_compute_phases(self):
        """Test phase computation from agent list."""
        from agentic_builder.orchestration.single_session import SingleSessionOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            orch = SingleSessionOrchestrator(Path(tmpdir))
            execution_order = [AgentType.PM, AgentType.ARCHITECT, AgentType.TL_UI_WEB]
            phases = orch._compute_phases(execution_order)

            # PM should be in phase 1 (no deps)
            # ARCHITECT in phase 2 (depends on PM)
            # TL_UI_WEB in phase 3 (depends on ARCHITECT)
            assert len(phases) >= 2
            assert "PM" in phases[0]["agents"]

    def test_generate_session_id(self):
        """Test session ID generation."""
        from agentic_builder.orchestration.single_session import SingleSessionOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            orch = SingleSessionOrchestrator(Path(tmpdir))
            id1 = orch._generate_session_id()
            id2 = orch._generate_session_id()

            assert id1.startswith("sess_")
            assert id2.startswith("sess_")
            assert id1 != id2  # Should be unique


class TestWorkflowConstraints:
    """Tests for WorkflowConstraints dataclass."""

    def test_default_constraints(self):
        """Test default constraint values."""
        from agentic_builder.common.types import ScopeLevel, WorkflowConstraints

        constraints = WorkflowConstraints()
        assert constraints.scope == ScopeLevel.MVP
        assert constraints.full_feature is False
        assert constraints.interactive is True
        assert constraints.explicit_includes == []
        assert constraints.explicit_excludes == []

    def test_full_feature_effective_scope(self):
        """Test that full_feature overrides scope to comprehensive."""
        from agentic_builder.common.types import ScopeLevel, WorkflowConstraints

        # With full_feature=True, effective scope should be COMPREHENSIVE
        constraints = WorkflowConstraints(full_feature=True, scope=ScopeLevel.MVP)
        assert constraints.effective_scope() == ScopeLevel.COMPREHENSIVE

        # Without full_feature, effective scope should match scope
        constraints = WorkflowConstraints(full_feature=False, scope=ScopeLevel.STANDARD)
        assert constraints.effective_scope() == ScopeLevel.STANDARD

    def test_constraints_to_manifest_dict(self):
        """Test conversion to manifest dictionary."""
        from agentic_builder.common.types import ScopeLevel, WorkflowConstraints

        constraints = WorkflowConstraints(
            scope=ScopeLevel.STANDARD,
            full_feature=True,
            interactive=False,
            explicit_includes=["auth"],
            explicit_excludes=["mobile"],
        )

        manifest_dict = constraints.to_manifest_dict()

        # full_feature=True should override scope to comprehensive
        assert manifest_dict["scope"] == "comprehensive"
        assert manifest_dict["full_feature"] is True
        assert manifest_dict["interactive"] is False
        assert "auth" in manifest_dict["explicit_includes"]
        assert "mobile" in manifest_dict["explicit_excludes"]


class TestOrchestratorTypes:
    """Tests for orchestrator type enum."""

    def test_orchestrator_type_values(self):
        """Test OrchestratorType enum values."""
        from agentic_builder.common.types import OrchestratorType

        assert OrchestratorType.ADAPTIVE.value == "adaptive"
        assert OrchestratorType.PARALLEL.value == "parallel"
        assert OrchestratorType.SEQUENTIAL.value == "sequential"


class TestAdaptiveOrchestratorConstraints:
    """Tests for AdaptiveOrchestrator with constraints."""

    def test_orchestrator_with_constraints(self):
        """Test orchestrator accepts constraints."""
        from agentic_builder.common.types import ScopeLevel, WorkflowConstraints
        from agentic_builder.orchestration.adaptive_orchestrator import AdaptiveOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            constraints = WorkflowConstraints(
                scope=ScopeLevel.COMPREHENSIVE,
                full_feature=True,
                interactive=False,
            )
            orch = AdaptiveOrchestrator(Path(tmpdir), constraints=constraints)

            assert orch.constraints.full_feature is True
            assert orch.constraints.scope == ScopeLevel.COMPREHENSIVE
            assert orch.interactive is False

    def test_orchestrator_constraints_in_manifest(self):
        """Test constraints are written to manifest."""
        import json

        from agentic_builder.common.types import ScopeLevel, WorkflowConstraints
        from agentic_builder.orchestration.adaptive_orchestrator import AdaptiveOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            constraints = WorkflowConstraints(
                scope=ScopeLevel.COMPREHENSIVE,
                full_feature=True,
            )
            orch = AdaptiveOrchestrator(Path(tmpdir), constraints=constraints)

            # Initialize session to create manifest
            orch._initialize_session("test_session", "Build a todo app")

            # Read manifest and check constraints
            manifest_path = Path(tmpdir) / ".tasks" / "manifest.json"
            manifest = json.loads(manifest_path.read_text())

            assert "constraints" in manifest
            assert manifest["constraints"]["full_feature"] is True
            assert manifest["constraints"]["scope"] == "comprehensive"


class TestCLIIntegration:
    """Tests for CLI integration with new flags."""

    def test_get_orchestrator_adaptive(self):
        """Test get_orchestrator returns AdaptiveOrchestrator."""
        from agentic_builder.common.types import OrchestratorType, WorkflowConstraints
        from agentic_builder.main import get_orchestrator
        from agentic_builder.orchestration.adaptive_orchestrator import AdaptiveOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            constraints = WorkflowConstraints(full_feature=True)
            orch = get_orchestrator(
                output_dir=Path(tmpdir),
                orchestrator_type=OrchestratorType.ADAPTIVE,
                constraints=constraints,
            )
            assert isinstance(orch, AdaptiveOrchestrator)
            assert orch.constraints.full_feature is True

    def test_get_orchestrator_sequential(self):
        """Test get_orchestrator returns WorkflowEngine for sequential."""
        from agentic_builder.common.types import OrchestratorType
        from agentic_builder.main import get_orchestrator
        from agentic_builder.orchestration.workflow_engine import WorkflowEngine

        with tempfile.TemporaryDirectory() as tmpdir:
            orch = get_orchestrator(
                output_dir=Path(tmpdir),
                orchestrator_type=OrchestratorType.SEQUENTIAL,
            )
            assert isinstance(orch, WorkflowEngine)

    def test_get_orchestrator_parallel(self):
        """Test get_orchestrator returns ParallelWorkflowEngine."""
        from agentic_builder.common.types import OrchestratorType
        from agentic_builder.main import get_orchestrator
        from agentic_builder.orchestration.parallel_engine import ParallelWorkflowEngine

        with tempfile.TemporaryDirectory() as tmpdir:
            orch = get_orchestrator(
                output_dir=Path(tmpdir),
                orchestrator_type=OrchestratorType.PARALLEL,
            )
            assert isinstance(orch, ParallelWorkflowEngine)
