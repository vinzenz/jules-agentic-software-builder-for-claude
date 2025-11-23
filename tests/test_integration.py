import os
from unittest.mock import patch

import pytest

from agentic_builder.common.types import AgentType, ModelTier
from agentic_builder.integration.claude_client import ClaudeClient
from agentic_builder.integration.git_manager import GitManager
from agentic_builder.integration.pr_manager import PRManager


@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {"AMAB_MOCK_GH_CLI": "1", "AMAB_MOCK_CLAUDE_CLI": "1"}):
        yield


def test_git_manager_create_branch():
    gm = GitManager()
    # In mock mode or unit test, we might just verify subprocess calls
    with patch("subprocess.run") as mock_run:
        gm.create_branch("feature/test")
        mock_run.assert_called_with(
            ["git", "checkout", "-b", "feature/test"], check=True, capture_output=True, text=True
        )


def test_pr_manager_create(mock_env):
    pm = PRManager()
    # Should not call subprocess if mocked
    with patch("subprocess.run") as mock_run:
        pm.create_pr("feature/test", "Title", "Body")
        mock_run.assert_not_called()


def test_claude_client_mock(mock_env):
    client = ClaudeClient()
    response = client.call_agent(
        agent_type=AgentType.PM, system_prompt="You are PM", user_input="Build app", model=ModelTier.OPUS
    )

    assert response.success
    assert "Mock response" in response.summary or "Mock" in response.summary


def test_claude_client_real_attempt():
    # If we unset the mock env, it should try to execute claude (and fail in sandbox or we mock subprocess)
    with patch.dict(os.environ, {"AMAB_MOCK_CLAUDE_CLI": ""}):
        client = ClaudeClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "<summary>Real output</summary>"
            mock_run.return_value.returncode = 0

            resp = client.call_agent(AgentType.PM, "sys", "in", ModelTier.OPUS)
            assert resp.summary == "Real output"
            # Verify command structure if needed
            args = mock_run.call_args[0][0]
            assert "claude" in args or "anthropic" in args  # Depends on implementation
