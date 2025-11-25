
from pathlib import Path
from unittest.mock import MagicMock, patch

from agentic_builder.common.types import AgentOutput, AgentType, Artifact, ModelTier
from agentic_builder.integration.claude_client import ClaudeClient
from agentic_builder.orchestration.workflow_engine import WorkflowEngine

# --- Tests for Security Fixes ---

def test_workflow_engine_prevents_path_traversal():
    """
    Verifies that WorkflowEngine blocks writing files to paths outside the current working directory.
    """
    # Setup
    session_manager = MagicMock()
    session = MagicMock()
    session.id = "test_session"
    session.workflow_name = "FULL_APP_GENERATION"
    session.completed_tasks = []
    session_manager.load_session.return_value = session
    session_manager.session_dir = Path("/tmp")
    # Mock the output_dir property to return the temp directory
    type(session_manager).output_dir = property(lambda self: Path("/tmp"))

    pms = MagicMock()
    git = MagicMock()
    claude = MagicMock()
    pr_manager = MagicMock()

    engine = WorkflowEngine(session_manager, pms, git, claude, pr_manager)
    engine._active_runs = {"test_session": True}

    # Mock PMS task creation
    task = MagicMock()
    task.id = "task_1"
    task.agent_type = AgentType.PM
    pms.create_task.return_value = task

    # Mock Claude response with malicious artifact path
    malicious_path = "../escaped_file.txt"
    response = AgentOutput(
        success=True,
        summary="Done",
        artifacts=[
            Artifact(name=malicious_path, type="file", path=malicious_path, content="hacked")
        ],
        next_steps=[],
        metadata={}
    )

    # We need to test the logic inside run_loop.
    # To avoid running the full loop, we can test the specific block if extracted,
    # but since it's embedded, we'll mock the dependencies to run one iteration.

    # Mock get_agent_config to return a dummy config
    with patch("agentic_builder.orchestration.workflow_engine.get_agent_config") as mock_config:
        mock_config.return_value = MagicMock()
        mock_config.return_value.dependencies = []
        mock_config.return_value.model_tier = ModelTier.HAIKU

        # Mock WorkflowMapper to return just PM agent
        with patch("agentic_builder.orchestration.workflow_engine.WorkflowMapper") as mock_mapper:
            mock_mapper.get_execution_order.return_value = [AgentType.PM]

            with patch("agentic_builder.orchestration.workflow_engine.ContextSerializer"):
                # Mock claude to return our malicious response
                claude.call_agent.return_value = response

                # Stop the loop after the first agent (PM)
                def side_effect(*args, **kwargs):
                    # Remove from active runs to break the loop
                    del engine._active_runs["test_session"]
                    return response
                claude.call_agent.side_effect = side_effect

                # Run in a temp directory to be safe
                with patch("pathlib.Path.write_text") as mock_write:
                    engine.run_loop("test_session")

                    # Verify write_text was NOT called
                    mock_write.assert_not_called()

def test_claude_client_uses_stdin():
    """
    Verifies that ClaudeClient uses stdin for input.
    """
    client = ClaudeClient()
    user_input = "some input"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "<response>Success</response>"
        mock_run.return_value.returncode = 0

        # We must also mock get_agent_prompt since it tries to read files
        with patch("agentic_builder.integration.claude_client.get_agent_prompt") as mock_prompt:
            mock_prompt.return_value = "System Prompt"

            client.call_agent(
                agent_type=AgentType.PM,
                prompt="Execute task",
                user_input=user_input,
                model=ModelTier.HAIKU
            )

            args, kwargs = mock_run.call_args

            # Check that user_input was passed as 'input' kwarg
            assert kwargs.get("input") == user_input
            # Check that command uses "-" for input file if applicable, or just reads stdin
            cmd = args[0]
            assert "-" in cmd
            assert "--system-prompt" in cmd
            assert "System Prompt" in cmd
            assert "-p" in cmd
