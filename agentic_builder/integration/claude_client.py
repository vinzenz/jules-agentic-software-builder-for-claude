import os
import subprocess

from agentic_builder.agents.configs import get_agent_config, get_agent_prompt
from agentic_builder.agents.response_parser import ResponseParser
from agentic_builder.common.types import AgentOutput, AgentType, ModelTier


class ClaudeClient:
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
        cmd = ["claude", "-m", model.value, "-s", system_prompt, "-p", prompt, "-"]

        try:
            result = subprocess.run(
                cmd,
                input=user_input,
                capture_output=True,
                text=True,
                check=True
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
