from typing import Dict, List

from agentic_builder.common.types import Artifact, Task


class ContextSerializer:
    @staticmethod
    def serialize(task: Task, dependency_outputs: Dict[str, List[Artifact]] = None) -> str:
        """
        Serialize task context to XML format.

        Note: We only include file paths, not content. This saves tokens as agents
        can read files directly from disk if they need the content.
        """
        if dependency_outputs is None:
            dependency_outputs = {}

        xml = ["<task_context>"]
        xml.append(f"  <task_id>{task.id}</task_id>")
        xml.append(f"  <agent_role>{task.agent_type.value}</agent_role>")
        xml.append(f"  <description>{task.description}</description>")

        if dependency_outputs:
            xml.append("  <dependencies>")
            for dep_id, artifacts in dependency_outputs.items():
                xml.append(f"    <dependency id='{dep_id}'>")
                for art in artifacts:
                    # Only include file path reference, not content (saves tokens)
                    path = art.path or art.name
                    xml.append(f"      <file path='{path}'/>")
                xml.append("    </dependency>")
            xml.append("  </dependencies>")

        # Add file context if any
        if task.context_files:
            xml.append("  <files>")
            for f in task.context_files:
                xml.append(f"    <file path='{f}'/>")
            xml.append("  </files>")

        xml.append("</task_context>")
        return "\n".join(xml)
