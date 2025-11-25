"""Integration - External service integrations."""

from agentic_builder.integration.batched_git import BatchedGitManager, PhaseCommitStrategy
from agentic_builder.integration.claude_client import ClaudeClient
from agentic_builder.integration.git_manager import GitManager
from agentic_builder.integration.long_running_session import (
    LongRunningCLISession,
    MessageDirection,
    StreamEvent,
    StreamEventType,
    StreamLogger,
    StreamMessage,
    create_session_with_logging,
)
from agentic_builder.integration.pr_manager import PRManager

__all__ = [
    "ClaudeClient",
    "GitManager",
    "PRManager",
    "BatchedGitManager",
    "PhaseCommitStrategy",
    # Long-running CLI session
    "LongRunningCLISession",
    "StreamLogger",
    "StreamMessage",
    "StreamEvent",
    "StreamEventType",
    "MessageDirection",
    "create_session_with_logging",
]
