import subprocess
from typing import List

from agentic_builder.common.utils import get_project_root


class GitManager:
    def __init__(self):
        # Always operate in the project root directory
        self._cwd = get_project_root()

    def create_branch(self, branch_name: str):
        self._run(["git", "checkout", "-b", branch_name])

    def checkout_branch(self, branch_name: str):
        self._run(["git", "checkout", branch_name])

    def commit_files(self, files: List[str], message: str):
        if not files:
            return
        self._run(["git", "add"] + files)
        self._run(["git", "commit", "-m", message])

    def get_status(self) -> str:
        return self._run(["git", "status", "--porcelain"], capture_output=True)

    def _run(self, cmd: List[str], capture_output=False, check=True):
        try:
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=True,  # Always capture to avoid spam
                text=True,
                cwd=self._cwd,  # Run git commands in project root
            )
            return result.stdout if capture_output else ""
        except subprocess.CalledProcessError as e:
            # Check if we are mocking environment where git might not exist or fail
            # For this specific tool, we might want to log error
            raise e
