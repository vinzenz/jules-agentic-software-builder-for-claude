import os
import subprocess

from agentic_builder.agents.response_parser import ResponseParser
from agentic_builder.common.types import AgentOutput, AgentType, ModelTier


class ClaudeClient:
    def call_agent(self, agent_type: AgentType, system_prompt: str, user_input: str, model: ModelTier) -> AgentOutput:
        if os.environ.get("AMAB_MOCK_CLAUDE_CLI") == "1":
            return self._mock_response(agent_type)

        # Real implementation: Call `claude` CLI or API
        # Assuming `claude` CLI takes input via stdin or args.
        # The spec says "Call Claude CLI (headless)".
        # We'll assume a command `claude` exists.

        # Example command construction:
        # claude -m <model> -s <system_prompt> "user input"

        cmd = ["claude", "-m", model.value, "-p", system_prompt, user_input]
        # Note: -p for prompt or system prompt might differ based on actual CLI.
        # Assuming typical structure. If system prompt is separate, might be --system.

        try:
            # We might need to pass large text via stdin if too long for args
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
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
