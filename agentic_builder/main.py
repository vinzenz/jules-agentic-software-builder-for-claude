from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentic_builder.common.logging_config import setup_debug_logging
from agentic_builder.common.types import WorkflowStatus
from agentic_builder.integration.claude_client import ClaudeClient
from agentic_builder.integration.git_manager import GitManager
from agentic_builder.integration.pr_manager import PRManager
from agentic_builder.orchestration.session_manager import SessionManager
from agentic_builder.orchestration.workflow_engine import WorkflowEngine
from agentic_builder.pms.task_manager import TaskManager

app = typer.Typer(help="Agentic Mobile App Builder CLI")
console = Console()


# Callback for global options
@app.callback()
def main_callback(
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug logging to see prompts, responses, and internal operations",
    ),
):
    """
    Agentic Mobile App Builder - Build software with AI agents.

    Use --debug to enable verbose debug logging that shows:
    - Prompts sent to Claude agents
    - Responses received from agents
    - Internal workflow operations
    - Context serialization details

    Debug logs are written to both stderr and .sessions/debug_logs/
    """
    if debug:
        setup_debug_logging(enabled=True, log_to_console=True, log_to_file=True)
        console.print("[yellow]Debug logging enabled[/yellow]")


def get_engine(output_dir: Optional[Path] = None):
    """
    Create a WorkflowEngine with all required dependencies.

    Args:
        output_dir: Optional project root directory for all file operations.
                   Defaults to current working directory if not specified.
    """
    # Default to CWD if no output_dir specified
    resolved_output_dir = output_dir.resolve() if output_dir else Path.cwd()

    return WorkflowEngine(
        session_manager=SessionManager(output_dir=resolved_output_dir),
        pms_manager=TaskManager(output_dir=resolved_output_dir),
        git_manager=GitManager(output_dir=resolved_output_dir),
        claude_client=ClaudeClient(output_dir=resolved_output_dir),
        pr_manager=PRManager(),
    )


@app.command()
def run(
    workflow: str = typer.Argument(..., help="Workflow type (e.g., FULL_APP_GENERATION, FEATURE_ADDITION)"),
    idea: str = typer.Option(
        None,
        "--idea",
        "-i",
        help="Project idea or description. This will be passed to agents and written to CLAUDE.md",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Project root directory for all file operations. Defaults to current working directory.",
        exists=False,  # Don't require directory to exist - we'll create it if needed
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
):
    """
    Start a new workflow.

    Examples:
        agentic-builder run FULL_APP_GENERATION --idea "Build a todo app with React and FastAPI"
        agentic-builder run FEATURE_ADDITION -i "Add user authentication with OAuth2"
        agentic-builder run FULL_APP_GENERATION --idea "Build a CLI tool" -o ./my-project
    """
    # Use provided output_dir or default to CWD
    resolved_output_dir = output_dir if output_dir else Path.cwd()

    console.print(f"[bold green]Starting workflow:[/bold green] {workflow}")
    if idea:
        console.print(f"[bold blue]Project Idea:[/bold blue] {idea}")
    console.print(f"[bold cyan]Output Directory:[/bold cyan] {resolved_output_dir}")

    # Create output directory if it doesn't exist
    if not resolved_output_dir.exists():
        console.print(f"[yellow]Creating output directory:[/yellow] {resolved_output_dir}")
        resolved_output_dir.mkdir(parents=True, exist_ok=True)

    engine = get_engine(output_dir=resolved_output_dir)

    # Event listeners for CLI feedback
    def on_stage_start(data):
        console.print(f"  [cyan]Starting Agent:[/cyan] {data['agent'].value}")

    def on_agent_complete(data):
        console.print(f"  [green]Completed:[/green] {data['agent'].value}")

    def on_fail(data):
        console.print(f"  [red]Failed:[/red] {data.get('error')}")

    def on_claude_md_created(data):
        console.print(f"  [blue]Created CLAUDE.md:[/blue] {data['path']}")

    engine.on("agent_spawned", on_stage_start)
    engine.on("agent_completed", on_agent_complete)
    engine.on("workflow_failed", on_fail)
    engine.on("claude_md_created", on_claude_md_created)

    try:
        run_id = engine.start_workflow(workflow, idea=idea)
        console.print(f"[bold green]Workflow Completed![/bold green] Run ID: {run_id}")
    except Exception as e:
        console.print(f"[bold red]Workflow Failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("list")
def list_sessions(
    all: bool = typer.Option(False, "--all", help="Show all sessions including completed"),
    zombies: bool = typer.Option(False, "--zombies", help="Show zombie sessions"),
    status: str = typer.Option(None, "--status", help="Filter by status"),
):
    """List sessions."""
    console.print("[bold]Sessions[/bold]")
    table = Table(title="Active Sessions")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Workflow", style="green")

    manager = SessionManager()
    sessions = manager.list_sessions()

    for sess in sessions:
        # Filters
        if not all and sess.status == WorkflowStatus.COMPLETED:
            continue
        if status and sess.status != status:
            continue
        # Zombies check (simplified)

        table.add_row(sess.id, sess.status.value, sess.workflow_name)

    console.print(table)


@app.command()
def status(id: str):
    """Show details of a session."""
    console.print(f"Status for session: {id}")


@app.command()
def cancel(id: str, force: bool = False, cleanup: bool = False):
    """Cancel a workflow."""
    console.print(f"Cancelling session: {id}")


@app.command()
def resume(id: str):
    """Resume a workflow from the last checkpoint."""
    console.print(f"Resuming session: {id}")


@app.command()
def usage():
    """Show token usage statistics."""
    manager = SessionManager()
    sessions = manager.list_sessions()

    table = Table(title="Token Usage")
    table.add_column("Session ID", style="cyan")
    table.add_column("Tokens", justify="right", style="green")

    total = 0
    for sess in sessions:
        table.add_row(sess.id, str(sess.total_tokens))
        total += sess.total_tokens

    console.print(table)
    console.print(f"[bold]Total Tokens Used across all sessions:[/bold] {total}")


@app.command()
def logs(id: str):
    """View execution logs."""
    manager = SessionManager()
    log_file = manager.session_dir / f"{id}.log"

    if not log_file.exists():
        console.print(f"[red]No logs found for session {id}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[bold]Logs for {id}:[/bold]")
    console.print(log_file.read_text())


if __name__ == "__main__":
    app()
