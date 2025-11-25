from typing import Dict, List

from agentic_builder.common.types import Task


class ContextSerializer:
    @staticmethod
    def serialize(task: Task, dependency_tasks: Dict[str, Task] = None) -> str:
        """
        Serialize task context to XML format.

        Includes:
        - Task info (id, role, description)
        - Dependency outputs (summary, next_steps, warnings, file paths)

        Note: We only include file paths, not content. Agents can read files
        directly from disk if they need the content.
        """
        if dependency_tasks is None:
            dependency_tasks = {}

        xml = ["<task_context>"]
        xml.append(f"  <task_id>{task.id}</task_id>")
        xml.append(f"  <agent_role>{task.agent_type.value}</agent_role>")
        xml.append(f"  <description>{task.description}</description>")

        if dependency_tasks:
            xml.append("  <dependencies>")
            for dep_id, dep_task in dependency_tasks.items():
                xml.append(f"    <dependency id='{dep_id}' agent='{dep_task.agent_type.value}'>")

                # Include the agent's summary
                if dep_task.output_summary:
                    xml.append(f"      <summary>{_escape_xml(dep_task.output_summary)}</summary>")

                # Include artifacts (file paths only)
                if dep_task.context_files:
                    xml.append("      <artifacts>")
                    for fpath in dep_task.context_files:
                        xml.append(f"        <artifact path='{fpath}'/>")
                    xml.append("      </artifacts>")

                # Include next steps
                if dep_task.output_next_steps:
                    xml.append("      <next_steps>")
                    for step in dep_task.output_next_steps:
                        xml.append(f"        <step>{_escape_xml(step)}</step>")
                    xml.append("      </next_steps>")

                # Include warnings
                if dep_task.output_warnings:
                    xml.append("      <warnings>")
                    for warning in dep_task.output_warnings:
                        xml.append(f"        <warning>{_escape_xml(warning)}</warning>")
                    xml.append("      </warnings>")

                xml.append("    </dependency>")
            xml.append("  </dependencies>")

        # Add file context if any (for this task specifically)
        if task.context_files:
            xml.append("  <files>")
            for f in task.context_files:
                xml.append(f"    <file path='{f}'/>")
            xml.append("  </files>")

        xml.append("</task_context>")
        return "\n".join(xml)


def _escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
