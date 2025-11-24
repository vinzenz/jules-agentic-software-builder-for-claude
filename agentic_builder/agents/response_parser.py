import re

from agentic_builder.common.types import AgentOutput, Artifact


class ResponseParser:
    @staticmethod
    def parse(text: str) -> AgentOutput:
        # Simple XML parsing using regex for MVP
        # Robust implementation would use lxml or ElementTree, but LLM output might be malformed.

        # Extract summary
        summary_match = re.search(r"<summary>(.*?)</summary>", text, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else text.strip()[:100] + "..."
        if summary == text.strip()[:100] + "...":
            # If no summary tag, treat whole text as summary (fallback)
            summary = text.strip()

        # Extract artifacts
        artifacts = []
        # Regex for artifacts: <artifact name="..." type="...">content</artifact>
        artifact_pattern = re.compile(
            r'<artifact\s+name=["\'](.*?)["\']\s+type=["\'](.*?)["\']\s*>(.*?)</artifact>', re.DOTALL
        )
        for match in artifact_pattern.finditer(text):
            name, type_, content = match.groups()
            artifacts.append(Artifact(name=name, type=type_, content=content.strip()))

        # Extract next steps
        next_steps = []
        steps_match = re.search(r"<next_steps>(.*?)</next_steps>", text, re.DOTALL)
        if steps_match:
            lines = steps_match.group(1).strip().split("\n")
            next_steps = [line.strip().lstrip("- ").strip() for line in lines if line.strip()]

        # Extract warnings
        warnings = []
        warn_match = re.search(r"<warnings>(.*?)</warnings>", text, re.DOTALL)
        if warn_match:
            lines = warn_match.group(1).strip().split("\n")
            warnings = [line.strip().lstrip("- ").strip() for line in lines if line.strip()]

        return AgentOutput(
            success=True,  # Assume success if we got a response. In reality check for <error> tags
            summary=summary,
            artifacts=artifacts,
            next_steps=next_steps,
            warnings=warnings,
        )
