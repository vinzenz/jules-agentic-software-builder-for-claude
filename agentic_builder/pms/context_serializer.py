from typing import Dict, List, Optional

from agentic_builder.common.logging_config import get_logger, log_separator
from agentic_builder.common.types import Task

# Module logger
logger = get_logger(__name__)


class ContextSerializer:
    @staticmethod
    def serialize(
        task: Task,
        dependency_tasks: Dict[str, Task] = None,
        project_idea: Optional[str] = None,
    ) -> str:
        """
        Serialize task context to XML format.

        Includes:
        - Project idea (if provided - passed to first agent like PM)
        - Task info (id, role, description)
        - Dependency outputs (summary, next_steps, warnings, file paths)

        Note: We only include file paths, not content. Agents can read files
        directly from disk if they need the content.
        """
        log_separator(logger, "SERIALIZING CONTEXT", char="-")
        logger.debug(f"Task ID: {task.id}")
        logger.debug(f"Agent Type: {task.agent_type.value}")
        logger.debug(f"Description: {task.description}")
        if project_idea:
            logger.debug(f"Project Idea: {project_idea[:100]}..." if len(project_idea) > 100 else f"Project Idea: {project_idea}")

        if dependency_tasks is None:
            dependency_tasks = {}

        logger.debug(f"Number of dependency tasks: {len(dependency_tasks)}")

        xml = ["<task_context>"]

        # Include project idea at the top for agents to understand what to build
        if project_idea:
            xml.append("  <project_idea>")
            xml.append(f"    {_escape_xml(project_idea)}")
            xml.append("  </project_idea>")

        xml.append(f"  <task_id>{task.id}</task_id>")
        xml.append(f"  <agent_role>{task.agent_type.value}</agent_role>")
        xml.append(f"  <description>{task.description}</description>")

        if dependency_tasks:
            xml.append("  <dependencies>")
            for dep_id, dep_task in dependency_tasks.items():
                logger.debug(f"Adding dependency: {dep_id} (agent: {dep_task.agent_type.value})")
                xml.append(f"    <dependency id='{dep_id}' agent='{dep_task.agent_type.value}'>")

                # Include the agent's summary
                if dep_task.output_summary:
                    logger.debug(f"  - Summary: {dep_task.output_summary[:100]}...")
                    xml.append(f"      <summary>{_escape_xml(dep_task.output_summary)}</summary>")

                # Include artifacts (file paths only)
                if dep_task.context_files:
                    logger.debug(f"  - Artifacts: {len(dep_task.context_files)} files")
                    xml.append("      <artifacts>")
                    for fpath in dep_task.context_files:
                        logger.debug(f"    - {fpath}")
                        xml.append(f"        <artifact path='{fpath}'/>")
                    xml.append("      </artifacts>")

                # Include next steps
                if dep_task.output_next_steps:
                    logger.debug(f"  - Next steps: {len(dep_task.output_next_steps)} items")
                    xml.append("      <next_steps>")
                    for step in dep_task.output_next_steps:
                        xml.append(f"        <step>{_escape_xml(step)}</step>")
                    xml.append("      </next_steps>")

                # Include warnings
                if dep_task.output_warnings:
                    logger.debug(f"  - Warnings: {len(dep_task.output_warnings)} items")
                    xml.append("      <warnings>")
                    for warning in dep_task.output_warnings:
                        xml.append(f"        <warning>{_escape_xml(warning)}</warning>")
                    xml.append("      </warnings>")

                xml.append("    </dependency>")
            xml.append("  </dependencies>")

        # Add file context if any (for this task specifically)
        if task.context_files:
            logger.debug(f"Adding task context files: {len(task.context_files)} files")
            xml.append("  <files>")
            for f in task.context_files:
                logger.debug(f"  - {f}")
                xml.append(f"    <file path='{f}'/>")
            xml.append("  </files>")

        xml.append("</task_context>")
        result = "\n".join(xml)
        logger.debug(f"Serialized context length: {len(result)} characters")
        return result


def _escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
