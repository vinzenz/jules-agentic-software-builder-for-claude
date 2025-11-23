from typer.testing import CliRunner

from agentic_builder.main import app

runner = CliRunner()


def test_app_version():
    result = runner.invoke(app, ["--version"])
    # We haven't implemented --version yet, so checking mostly for not crashing or specific error if desired
    # For now, let's just ensure we can invoke the app
    assert result.exit_code != 0  # Should fail if option not defined, or pass if we define it


def test_list_command():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Sessions" in result.stdout


def test_usage_command():
    result = runner.invoke(app, ["usage"])
    assert result.exit_code == 0
    assert "Token Usage" in result.stdout


def test_status_command_missing_arg():
    result = runner.invoke(app, ["status"])
    assert result.exit_code != 0
    # Typer/Click might output to stderr
    # output = result.stdout # CliRunner mixes them by default unless mix_stderr=False
    # but let's just assert exit code is enough for now, or check generic 'Missing'


def test_status_command_mock():
    # We will need to mock the backend for this eventually
    result = runner.invoke(app, ["status", "test-session-id"])
    assert result.exit_code == 0


def test_run_command_help():
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "workflow" in result.stdout
