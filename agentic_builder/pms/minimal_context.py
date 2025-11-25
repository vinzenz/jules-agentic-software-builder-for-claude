"""
Minimal Context Injection - Ultra-low token context for agents.

Instead of passing full context (~5000 tokens), we pass a minimal pointer
(~50 tokens) that tells the agent where to find context on disk.

Token Comparison:
    Old approach: 2,000-15,000 tokens per agent
    New approach: ~50 tokens per agent

Agents are instructed to read .tasks/ files directly for the context they need.
"""

from typing import List, Optional

from agentic_builder.common.types import AgentType


class MinimalContextSerializer:
    """Generate minimal context pointers for agents (~50 tokens)."""

    TASKS_DIR = ".tasks"

    @staticmethod
    def serialize(
        agent_type: AgentType,
        dependencies: List[AgentType],
        project_idea: Optional[str] = None,
    ) -> str:
        """
        Generate minimal context pointer.

        Args:
            agent_type: The agent being invoked
            dependencies: List of dependency agents to read from
            project_idea: Project idea (only for first agent, PM)

        Returns:
            Minimal XML context (~50 tokens instead of ~5000)
        """
        deps_str = ", ".join(d.value for d in dependencies) if dependencies else "none"

        # Only include project idea for PM (first agent)
        if agent_type == AgentType.PM and project_idea:
            return f"""<task>
  <agent>{agent_type.value}</agent>
  <manifest>.tasks/manifest.json</manifest>
  <project_idea>{_escape_xml(project_idea)}</project_idea>
</task>"""

        return f"""<task>
  <agent>{agent_type.value}</agent>
  <manifest>.tasks/manifest.json</manifest>
  <read_from>{deps_str}</read_from>
</task>"""

    @staticmethod
    def get_context_instructions(agent_type: AgentType) -> str:
        """
        Generate context loading instructions for the agent's system prompt.

        These instructions tell the agent how to read context from disk
        instead of receiving it in the prompt.
        """
        return f"""<context_loading>
  Your context is stored in the .tasks/ directory. Read files as needed.

  Available context files:
  - .tasks/manifest.json - Session state, project idea, task registry
  - .tasks/{{AGENT}}/output.json - Agent outputs (summary, next_steps, warnings)
  - .tasks/{{AGENT}}/artifacts.json - Created file paths
  - .tasks/{{AGENT}}/decisions.json - Architectural/design decisions (if any)

  As {agent_type.value}, read ONLY what you need:
  1. Read .tasks/manifest.json for project_idea and session context
  2. Read .tasks/{{DEP}}/output.json for each dependency's output
  3. Read actual source files from paths in artifacts.json when needed

  After completing your work:
  1. Write files directly to the project (not .tasks/)
  2. Your output will be automatically captured and stored
</context_loading>"""

    @staticmethod
    def get_recommended_reads(agent_type: AgentType) -> List[str]:
        """
        Get recommended context files for an agent type.

        This helps agents know what to prioritize reading.
        """
        # Universal reads
        reads = [".tasks/manifest.json"]

        # Agent-specific recommendations
        recommendations = {
            AgentType.ARCHITECT: [
                ".tasks/PM/output.json",
                ".tasks/PM/artifacts.json",
            ],
            AgentType.UIUX_GUI: [
                ".tasks/PM/output.json",
            ],
            AgentType.UIUX_CLI: [
                ".tasks/PM/output.json",
            ],
            AgentType.TL_UI_WEB: [
                ".tasks/ARCHITECT/output.json",
                ".tasks/ARCHITECT/decisions.json",
                ".tasks/UIUX_GUI/output.json",
            ],
            AgentType.TL_UI_MOBILE: [
                ".tasks/ARCHITECT/output.json",
                ".tasks/ARCHITECT/decisions.json",
                ".tasks/UIUX_GUI/output.json",
            ],
            AgentType.TL_UI_DESKTOP: [
                ".tasks/ARCHITECT/output.json",
                ".tasks/ARCHITECT/decisions.json",
                ".tasks/UIUX_GUI/output.json",
            ],
            AgentType.TL_UI_CLI: [
                ".tasks/ARCHITECT/output.json",
                ".tasks/ARCHITECT/decisions.json",
                ".tasks/UIUX_CLI/output.json",
            ],
            AgentType.TL_CORE_API: [
                ".tasks/ARCHITECT/output.json",
                ".tasks/ARCHITECT/decisions.json",
            ],
            AgentType.TL_CORE_SYSTEMS: [
                ".tasks/ARCHITECT/output.json",
                ".tasks/ARCHITECT/decisions.json",
            ],
            AgentType.TL_CORE_LIBRARY: [
                ".tasks/ARCHITECT/output.json",
                ".tasks/ARCHITECT/decisions.json",
            ],
            AgentType.TEST: [
                ".tasks/ARCHITECT/decisions.json",
            ],
            AgentType.CQR: [
                ".tasks/ARCHITECT/decisions.json",
            ],
            AgentType.SR: [
                ".tasks/ARCHITECT/decisions.json",
            ],
            AgentType.DOE: [
                ".tasks/ARCHITECT/decisions.json",
            ],
        }

        # DEV agents read from their TL
        dev_to_tl = {
            AgentType.DEV_UI_WEB: AgentType.TL_UI_WEB,
            AgentType.DEV_UI_MOBILE: AgentType.TL_UI_MOBILE,
            AgentType.DEV_UI_DESKTOP: AgentType.TL_UI_DESKTOP,
            AgentType.DEV_UI_CLI: AgentType.TL_UI_CLI,
            AgentType.DEV_CORE_API: AgentType.TL_CORE_API,
            AgentType.DEV_CORE_SYSTEMS: AgentType.TL_CORE_SYSTEMS,
            AgentType.DEV_CORE_LIBRARY: AgentType.TL_CORE_LIBRARY,
        }

        if agent_type in dev_to_tl:
            tl = dev_to_tl[agent_type]
            reads.extend([
                f".tasks/{tl.value}/output.json",
                f".tasks/{tl.value}/artifacts.json",
                ".tasks/ARCHITECT/decisions.json",
            ])
        elif agent_type in recommendations:
            reads.extend(recommendations[agent_type])

        return reads


def _escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
