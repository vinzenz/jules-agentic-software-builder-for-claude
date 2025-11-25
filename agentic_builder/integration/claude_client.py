import json
import os
import shutil
import subprocess
from pathlib import Path

from agentic_builder.agents.configs import get_agent_config, get_agent_prompt
from agentic_builder.agents.response_parser import ResponseParser
from agentic_builder.common.types import AgentOutput, AgentType, ModelTier
from agentic_builder.common.utils import get_project_root


# Default permission denies for agent security
DEFAULT_PERMISSION_DENIES = [
    "Read(./.env)",
    "Read(./.env.*)",
    "Read(./secrets/**)",
    "Read(./config/credentials.json)",
    "Read(./build)",
]


class ClaudeClient:
    def __init__(self):
        self._local_claude_dir = None

    def _setup_local_claude_config(self, project_root: Path) -> Path:
        """
        Set up a project-local .claude folder with credentials and settings.

        This allows per-project configuration and security settings for the Claude CLI.
        """
        local_claude_dir = project_root / ".claude"
        local_claude_dir.mkdir(exist_ok=True)

        # Symlink or copy credentials from ~/.claude
        home_claude_dir = Path.home() / ".claude"
        home_credentials = home_claude_dir / ".credentials.json"
        local_credentials = local_claude_dir / ".credentials.json"

        if home_credentials.exists() and not local_credentials.exists():
            try:
                # Try to create a symlink first (more efficient)
                local_credentials.symlink_to(home_credentials)
            except OSError:
                # Fall back to copying if symlink fails (e.g., on Windows)
                shutil.copy2(home_credentials, local_credentials)

        # Create or update settings.json with permission denies
        settings_path = local_claude_dir / "settings.json"
        settings = {}

        if settings_path.exists():
            try:
                with open(settings_path, "r") as f:
                    settings = json.load(f)
            except (json.JSONDecodeError, IOError):
                settings = {}

        # Ensure permissions.deny exists and has required entries
        if "permissions" not in settings:
            settings["permissions"] = {}

        current_denies = set(settings["permissions"].get("deny", []))
        required_denies = set(DEFAULT_PERMISSION_DENIES)

        # Add any missing denies
        if not required_denies.issubset(current_denies):
            settings["permissions"]["deny"] = list(current_denies | required_denies)

            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=2)

        return local_claude_dir

    def call_agent(self, agent_type: AgentType, prompt: str, user_input: str, model: ModelTier) -> AgentOutput:
        if os.environ.get("AMAB_MOCK_CLAUDE_CLI") == "1":
            return self._mock_response(agent_type)

        # Real implementation: Call `claude` CLI or API
        # Retrieve system prompt (Agent Identity/Purpose)
        system_prompt = get_agent_prompt(agent_type)

        # Build Command:
        # -m: Model
        # -s: System Prompt (Who I am)
        # -p: Prompt (What I should do)
        # - : Stdin (Context)

        # Use stdin for user input to avoid ARG_MAX limits with large context
        cmd = ["claude", "--model", model.value, "--system-prompt", system_prompt, "--dangerously-skip-permissions", "--tools", "default", "-p", prompt, "-"]

        # Run Claude CLI in the project root directory so agents write files
        # to the correct location when using relative paths
        project_root = get_project_root()

        # Set up local .claude config directory with credentials and security settings
        local_claude_dir = self._setup_local_claude_config(project_root)

        # Create environment with CLAUDE_CONFIG_DIR pointing to local .claude
        env = os.environ.copy()
        env["CLAUDE_CONFIG_DIR"] = str(local_claude_dir)

        try:
            result = subprocess.run(
                cmd,
                input=user_input,
                capture_output=True,
                text=True,
                check=True,
                cwd=project_root,  # Ensure agent writes files relative to project root
                env=env,  # Use local .claude config
            )
            return ResponseParser.parse(result.stdout)
        except subprocess.CalledProcessError as e:
            # Fallback or error
            return AgentOutput(success=False, summary=f"Claude CLI failed: {e.stderr}")
        except FileNotFoundError:
            return AgentOutput(success=False, summary="Claude CLI not found.")

    def _mock_response(self, agent_type: AgentType) -> AgentOutput:
        # Generate a plausible mock response based on agent type
        summary = f"Mock response for {agent_type.value}"
        return AgentOutput(
            success=True,
            summary=summary,
            artifacts=[],
            next_steps=["Review output", "Proceed to next stage"],
            metadata={"tokensUsed": 150},
        )
