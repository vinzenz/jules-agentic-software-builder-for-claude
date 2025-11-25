from unittest.mock import MagicMock, patch

import pytest

from agentic_builder.common.types import WorkflowStatus
from agentic_builder.orchestration.session_manager import SessionManager
from agentic_builder.orchestration.workflow_engine import WorkflowEngine


@pytest.fixture
def session_manager(tmp_path):
    # Point session manager to a temp dir
    with patch("agentic_builder.orchestration.session_manager.get_project_root", return_value=tmp_path):
        yield SessionManager()


def test_session_create(session_manager):
    session = session_manager.create_session("test-flow")
    assert session.id is not None
    assert session.workflow_name == "test-flow"
    assert session.status == WorkflowStatus.PENDING

    # Check persistence
    loaded = session_manager.load_session(session.id)
    assert loaded.id == session.id


def test_session_update_status(session_manager):
    session = session_manager.create_session("test-flow")
    session_manager.update_status(session.id, WorkflowStatus.RUNNING)

    loaded = session_manager.load_session(session.id)
    assert loaded.status == WorkflowStatus.RUNNING


def test_workflow_engine_start(session_manager):
    # Mock dependencies
    mock_pms = MagicMock()
    mock_git = MagicMock()
    mock_claude = MagicMock()
    mock_pr = MagicMock()

    engine = WorkflowEngine(session_manager, mock_pms, mock_git, mock_claude, mock_pr)

    # Mock run_loop so it doesn't actually run agents (we test that separately)
    with patch.object(engine, "run_loop") as mock_loop:
        # Start workflow
        run_id = engine.start_workflow("FULL_APP_GENERATION")

        assert run_id is not None
        assert engine.get_run(run_id) is not None

        # Verify events or initial state
        session = session_manager.load_session(run_id)
        assert session.status == WorkflowStatus.RUNNING

        # Verify loop was called
        mock_loop.assert_called_once_with(run_id)
