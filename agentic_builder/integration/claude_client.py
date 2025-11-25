import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from agentic_builder.agents.configs import get_agent_prompt
from agentic_builder.agents.response_parser import ResponseParser
from agentic_builder.common.logging_config import get_logger, log_separator, truncate_for_log
from agentic_builder.common.types import AgentOutput, AgentType, ModelTier
from agentic_builder.common.utils import get_project_root

# Module logger
logger = get_logger(__name__)

# Default permission denies for agent security
DEFAULT_PERMISSION_DENIES = [
    "Read(./.env)",
    "Read(./.env.*)",
    "Read(./secrets/**)",
    "Read(./config/credentials.json)",
    "Read(./build)",
]


class ClaudeClient:
    def __init__(self, output_dir: Optional[Path] = None):
        self._local_claude_dir = None
        # Use provided output_dir or fall back to get_project_root()
        self._output_dir = output_dir.resolve() if output_dir else get_project_root()
        logger.debug(f"ClaudeClient initialized with output_dir: {self._output_dir}")

    @property
    def output_dir(self) -> Path:
        """Return the project root directory for agent operations."""
        return self._output_dir

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
        log_separator(logger, f"AGENT CALL: {agent_type.value}")
        logger.debug(f"Agent Type: {agent_type.value}")
        logger.debug(f"Model Tier: {model.value}")

        if os.environ.get("AMAB_MOCK_CLAUDE_CLI") == "1":
            logger.debug("MOCK MODE: Returning mock response (AMAB_MOCK_CLAUDE_CLI=1)")
            mock_response = self._mock_response(agent_type)
            logger.debug(f"Mock Response Summary: {mock_response.summary}")
            return mock_response

        # Real implementation: Call `claude` CLI or API
        # Retrieve system prompt (Agent Identity/Purpose)
        system_prompt = get_agent_prompt(agent_type)

        log_separator(logger, "SYSTEM PROMPT", char="-")
        logger.debug(f"System Prompt:\n{truncate_for_log(system_prompt, max_length=5000)}")

        log_separator(logger, "TASK PROMPT (-p)", char="-")
        logger.debug(f"Task Prompt:\n{prompt}")

        log_separator(logger, "USER INPUT (stdin context)", char="-")
        logger.debug(f"User Input / Context XML:\n{truncate_for_log(user_input, max_length=5000)}")
        logger.debug(f"User Input Length: {len(user_input)} characters")

        # Build Command:
        # -m: Model
        # -s: System Prompt (Who I am)
        # -p: Prompt (What I should do)
        # - : Stdin (Context)

        # Use stdin for user input to avoid ARG_MAX limits with large context
        cmd = [
            "claude", "--model", model.value, "--system-prompt", system_prompt,
            "--dangerously-skip-permissions", "--tools", "default", "-p", prompt, "-"
        ]

        log_separator(logger, "CLI COMMAND", char="-")
        # Log command without full system prompt (it's logged above)
        cmd_display = [
            "claude", "--model", model.value, "--system-prompt", "[SYSTEM_PROMPT]",
            "--dangerously-skip-permissions", "--tools", "default", "-p", prompt, "-"
        ]
        logger.debug(f"Command: {' '.join(cmd_display)}")

        # Run Claude CLI in the project root directory so agents write files
        # to the correct location when using relative paths
        project_root = self._output_dir
        logger.debug(f"Working Directory: {project_root}")

        # Set up local .claude config directory with credentials and security settings
        local_claude_dir = self._setup_local_claude_config(project_root)
        logger.debug(f"Claude Config Directory: {local_claude_dir}")

        # Create environment with CLAUDE_CONFIG_DIR pointing to local .claude
        env = os.environ.copy()
        env["CLAUDE_CONFIG_DIR"] = str(local_claude_dir)

        try:
            logger.debug("Executing Claude CLI...")
            result = subprocess.run(
                cmd,
                input=user_input,
                capture_output=True,
                text=True,
                check=True,
                cwd=project_root,  # Ensure agent writes files relative to project root
                env=env,  # Use local .claude config
            )

            log_separator(logger, "RAW RESPONSE (stdout)", char="-")
            logger.debug(f"Response Length: {len(result.stdout)} characters")
            logger.debug(f"Raw Response:\n{truncate_for_log(result.stdout, max_length=10000)}")

            if result.stderr:
                log_separator(logger, "STDERR", char="-")
                logger.debug(f"Stderr:\n{truncate_for_log(result.stderr, max_length=2000)}")

            parsed_output = ResponseParser.parse(result.stdout)

            log_separator(logger, "PARSED OUTPUT", char="-")
            logger.debug(f"Success: {parsed_output.success}")
            logger.debug(f"Summary: {parsed_output.summary}")
            logger.debug(f"Artifacts: {len(parsed_output.artifacts)}")
            for i, artifact in enumerate(parsed_output.artifacts):
                logger.debug(f"  Artifact {i+1}: path={artifact.path}, action={artifact.action}, type={artifact.type}")
            logger.debug(f"Next Steps: {parsed_output.next_steps}")
            logger.debug(f"Warnings: {parsed_output.warnings}")
            logger.debug(f"Metadata: {parsed_output.metadata}")

            log_separator(logger, f"END AGENT CALL: {agent_type.value}")
            return parsed_output

        except subprocess.CalledProcessError as e:
            log_separator(logger, "CLI ERROR", char="!")
            logger.error(f"Claude CLI failed with return code: {e.returncode}")
            logger.error(f"Stderr: {truncate_for_log(e.stderr or '', max_length=2000)}")
            logger.error(f"Stdout: {truncate_for_log(e.stdout or '', max_length=2000)}")
            return AgentOutput(success=False, summary=f"Claude CLI failed: {e.stderr}")

        except FileNotFoundError:
            logger.error("Claude CLI executable not found. Ensure 'claude' is installed and in PATH.")
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
