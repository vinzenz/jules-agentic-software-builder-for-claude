"""Integration - External service integrations."""

from agentic_builder.integration.batched_git import BatchedGitManager, PhaseCommitStrategy
from agentic_builder.integration.claude_client import ClaudeClient
from agentic_builder.integration.git_manager import GitManager
from agentic_builder.integration.pr_manager import PRManager

__all__ = [
    "ClaudeClient",
    "GitManager",
    "PRManager",
    "BatchedGitManager",
    "PhaseCommitStrategy",
]
