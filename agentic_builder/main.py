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


def get_engine():
    return WorkflowEngine(
        session_manager=SessionManager(),
        pms_manager=TaskManager(),
        git_manager=GitManager(),
        claude_client=ClaudeClient(),
        pr_manager=PRManager(),
    )


@app.command()
def run(workflow: str):
    """Start a new workflow."""
    console.print(f"[bold green]Starting workflow:[/bold green] {workflow}")

    engine = get_engine()

    # Event listeners for CLI feedback
    def on_stage_start(data):
        console.print(f"  [cyan]Starting Agent:[/cyan] {data['agent'].value}")

    def on_agent_complete(data):
        console.print(f"  [green]Completed:[/green] {data['agent'].value}")

    def on_fail(data):
        console.print(f"  [red]Failed:[/red] {data.get('error')}")

    engine.on("agent_spawned", on_stage_start)
    engine.on("agent_completed", on_agent_complete)
    engine.on("workflow_failed", on_fail)

    try:
        run_id = engine.start_workflow(workflow)
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
