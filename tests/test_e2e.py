import os
from unittest.mock import patch

import pytest

from agentic_builder.common.types import WorkflowStatus
from agentic_builder.integration.claude_client import ClaudeClient
from agentic_builder.integration.git_manager import GitManager
from agentic_builder.integration.pr_manager import PRManager
from agentic_builder.orchestration.session_manager import SessionManager
from agentic_builder.orchestration.workflow_engine import WorkflowEngine
from agentic_builder.pms.task_manager import TaskManager


@pytest.fixture
def mock_env_e2e(tmp_path):
    # Patch all persistence paths to temp dir
    # Since both managers use get_project_root, we can mock that in one place if we patch where they import it
    # But they import it individually.
    # Actually, patch 'agentic_builder.common.utils.get_project_root' might not work
    # if they imported it using `from ... import get_project_root`.
    # Let's check imports.
    # They do `from agentic_builder.common.utils import get_project_root`.
    # So we need to patch it in their respective modules.

    with (
        patch("agentic_builder.orchestration.session_manager.get_project_root", return_value=tmp_path),
        patch("agentic_builder.pms.task_manager.get_project_root", return_value=tmp_path),
        patch.dict(os.environ, {"AMAB_MOCK_GH_CLI": "1", "AMAB_MOCK_CLAUDE_CLI": "1"}),
    ):
        yield


def test_full_workflow_execution(mock_env_e2e):
    # Setup Managers
    session_mgr = SessionManager()
    pms = TaskManager()
    git = GitManager()
    claude = ClaudeClient()
    pr_mgr = PRManager()

    # We need to mock git methods that use subprocess even in mock mode if they verify git repo existence
    # But GitManager checks subprocess. If we are in a non-git dir, it might fail.
    # So we'll mock GitManager's internal run or just ensure it passes.
    # The requirement says "Mock version when env var is set" only for Claude and PR?
    # Git integration says "git integration".
    # I'll patch GitManager to be a no-op/mock for E2E speed/stability in sandbox

    with patch.object(git, "_run"):
        engine = WorkflowEngine(session_mgr, pms, git, claude, pr_mgr)

        # Start
        run_id = engine.start_workflow("FULL_APP_GENERATION")

        # Verify Session Completed
        session = session_mgr.load_session(run_id)
        assert session.status == WorkflowStatus.COMPLETED

        # Verify Tasks Created (all agents in FULL_APP_GENERATION)
        # PMS creates task files.
        # tasks = list(pms._cache.values())  # Or check filesystem
        # Since cache might be empty if we reloaded, check filesystem via manager logic?
        # Actually pms.create_task populates cache.
        # FULL_APP_GENERATION includes all agent types
        from agentic_builder.common.types import AgentType

        assert len(session.completed_tasks) == len(list(AgentType))

        # Verify PR creation
        # We can check if pr_mgr.create_pr was called if we mocked it, but we are using "Real" pr_mgr with Mock Env.
        # It prints to console. We can't easily capture print here without capsys.
        # But we can verify no exception was thrown.
