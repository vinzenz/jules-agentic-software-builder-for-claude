import os
import subprocess

from rich.console import Console

console = Console()


class PRManager:
    def create_pr(self, branch: str, title: str, body: str, draft: bool = True):
        if os.environ.get("AMAB_MOCK_GH_CLI") == "1":
            console.print(f"[bold yellow]MOCK PR CREATION:[/bold yellow] Branch={branch}, Title={title}")
            return "https://github.com/mock/repo/pull/123"

        cmd = ["gh", "pr", "create", "--head", branch, "--title", title, "--body", body]
        if draft:
            cmd.append("--draft")

        try:
            res = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return res.stdout.strip()
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to create PR: {e.stderr}[/red]")
            raise e
