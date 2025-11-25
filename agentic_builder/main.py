from pathlib import Path
from typing import Optional, Union

import typer
from rich.console import Console
from rich.table import Table

from agentic_builder.common.logging_config import setup_debug_logging
from agentic_builder.common.types import (
    OrchestratorType,
    ScopeLevel,
    WorkflowConstraints,
    WorkflowStatus,
)
from agentic_builder.integration.claude_client import ClaudeClient
from agentic_builder.integration.git_manager import GitManager
from agentic_builder.integration.pr_manager import PRManager
from agentic_builder.orchestration.adaptive_orchestrator import AdaptiveOrchestrator
from agentic_builder.orchestration.parallel_engine import ParallelWorkflowEngine
from agentic_builder.orchestration.session_manager import SessionManager
from agentic_builder.orchestration.workflow_engine import WorkflowEngine
from agentic_builder.pms.task_manager import TaskManager

app = typer.Typer(help="Agentic Software Builder CLI")
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


def get_engine(output_dir: Optional[Path] = None) -> WorkflowEngine:
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


def get_orchestrator(
    output_dir: Path,
    orchestrator_type: OrchestratorType = OrchestratorType.ADAPTIVE,
    constraints: Optional[WorkflowConstraints] = None,
) -> Union[WorkflowEngine, ParallelWorkflowEngine, AdaptiveOrchestrator]:
    """
    Factory function to create the appropriate orchestrator.

    Args:
        output_dir: Project root directory for all file operations.
        orchestrator_type: Type of orchestrator to use.
        constraints: Workflow constraints (scope, full_feature, etc.)

    Returns:
        Configured orchestrator instance.
    """
    resolved_output_dir = output_dir.resolve() if output_dir else Path.cwd()

    if orchestrator_type == OrchestratorType.ADAPTIVE:
        return AdaptiveOrchestrator(
            project_root=resolved_output_dir,
            constraints=constraints,
        )

    elif orchestrator_type == OrchestratorType.PARALLEL:
        return ParallelWorkflowEngine(
            session_manager=SessionManager(output_dir=resolved_output_dir),
            git_manager=GitManager(output_dir=resolved_output_dir),
            claude_client=ClaudeClient(output_dir=resolved_output_dir),
            pr_manager=PRManager(),
        )

    else:  # SEQUENTIAL
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
    orchestrator: str = typer.Option(
        "adaptive",
        "--orchestrator",
        "-e",
        help="Orchestrator engine: adaptive (default, fastest), parallel (5x faster), sequential (legacy)",
    ),
    full_feature: bool = typer.Option(
        False,
        "--full-feature",
        "-f",
        help="Include all features (not MVP). Overrides PM's tendency to recommend minimal scope.",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Enable/disable user prompts for decisions",
    ),
    scope: Optional[str] = typer.Option(
        None,
        "--scope",
        "-s",
        help="Feature scope: mvp (minimal), standard (common features), comprehensive (all features)",
    ),
):
    """
    Start a new workflow.

    Examples:
        agentic-builder run FULL_APP_GENERATION --idea "Build a todo app with React and FastAPI"
        agentic-builder run FEATURE_ADDITION -i "Add user authentication with OAuth2"
        agentic-builder run FULL_APP_GENERATION --idea "Build a CLI tool" -o ./my-project

    With full features (not MVP):
        agentic-builder run FULL_APP_GENERATION --idea "Build a todo app" --full-feature
        agentic-builder run FULL_APP_GENERATION --idea "Build a todo app" -f

    With different orchestrators:
        agentic-builder run FULL_APP_GENERATION --idea "Build a todo app" --orchestrator adaptive
        agentic-builder run FULL_APP_GENERATION --idea "Build a todo app" -e parallel

    Non-interactive mode:
        agentic-builder run FULL_APP_GENERATION --idea "Build a todo app" --no-interactive
    """
    # Use provided output_dir or default to CWD
    resolved_output_dir = output_dir if output_dir else Path.cwd()

    # Parse orchestrator type
    try:
        orch_type = OrchestratorType(orchestrator.lower())
    except ValueError:
        console.print(f"[bold red]Invalid orchestrator:[/bold red] {orchestrator}")
        console.print("Valid options: adaptive, parallel, sequential")
        raise typer.Exit(code=1)

    # Parse scope if provided
    scope_level = ScopeLevel.MVP
    if scope:
        try:
            scope_level = ScopeLevel(scope.lower())
        except ValueError:
            console.print(f"[bold red]Invalid scope:[/bold red] {scope}")
            console.print("Valid options: mvp, standard, comprehensive")
            raise typer.Exit(code=1)

    # Create constraints
    constraints = WorkflowConstraints(
        scope=scope_level,
        full_feature=full_feature,
        interactive=interactive,
    )

    console.print(f"[bold green]Starting workflow:[/bold green] {workflow}")
    if idea:
        console.print(f"[bold blue]Project Idea:[/bold blue] {idea}")
    console.print(f"[bold cyan]Output Directory:[/bold cyan] {resolved_output_dir}")
    console.print(f"[bold magenta]Orchestrator:[/bold magenta] {orch_type.value}")

    if full_feature:
        console.print("[bold yellow]Mode:[/bold yellow] Full-Feature (not MVP)")
    elif scope_level != ScopeLevel.MVP:
        console.print(f"[bold yellow]Scope:[/bold yellow] {scope_level.value}")

    if not interactive:
        console.print("[bold yellow]Interactive:[/bold yellow] Disabled")

    # Create output directory if it doesn't exist
    if not resolved_output_dir.exists():
        console.print(f"[yellow]Creating output directory:[/yellow] {resolved_output_dir}")
        resolved_output_dir.mkdir(parents=True, exist_ok=True)

    # Get appropriate orchestrator
    engine = get_orchestrator(
        output_dir=resolved_output_dir,
        orchestrator_type=orch_type,
        constraints=constraints,
    )

    # Handle different orchestrator types
    if orch_type == OrchestratorType.ADAPTIVE:
        # AdaptiveOrchestrator has its own run method
        try:
            result = engine.run_workflow(idea)
            console.print("[bold green]Workflow Completed![/bold green]")
            console.print(f"  Agents run: {result.get('agents_run', 'N/A')}")
            console.print(f"  Agents skipped: {result.get('agents_skipped', 'N/A')}")
        except Exception as e:
            console.print(f"[bold red]Workflow Failed:[/bold red] {e}")
            raise typer.Exit(code=1)
    else:
        # WorkflowEngine and ParallelWorkflowEngine use event-based approach
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
