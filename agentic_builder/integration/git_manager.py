import subprocess
from typing import List


class GitManager:
    def create_branch(self, branch_name: str):
        self._run(["git", "checkout", "-b", branch_name])

    def commit_files(self, files: List[str], message: str):
        if not files:
            return
        self._run(["git", "add"] + files)
        self._run(["git", "commit", "-m", message])

    def get_status(self) -> str:
        return self._run(["git", "status", "--porcelain"], capture_output=True)

    def _run(self, cmd: List[str], capture_output=False, check=True):
        # We assume we are in the repo root or handled by CWD
        try:
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=True,  # Always capture to avoid spam
                text=True,
            )
            return result.stdout if capture_output else ""
        except subprocess.CalledProcessError as e:
            # Check if we are mocking environment where git might not exist or fail
            # For this specific tool, we might want to log error
            raise e
