from typing import Dict, List

from agentic_builder.common.types import Artifact, Task


class ContextSerializer:
    @staticmethod
    def serialize(task: Task, dependency_outputs: Dict[str, List[Artifact]] = None) -> str:
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
                    xml.append(f"      <artifact name='{art.name}' type='{art.type}'>")
                    # Ideally escape content to avoid XML injection, wrapping in CDATA is safest
                    # Sanitize content for CDATA
                    content = art.content.replace("]]>", "]]]]><![CDATA[>")
                    xml.append(f"<![CDATA[{content}]]>")
                    xml.append("      </artifact>")
                xml.append("    </dependency>")
            xml.append("  </dependencies>")

        # Add file context if any (not fully spec'd but good practice)
        if task.context_files:
            xml.append("  <files>")
            for f in task.context_files:
                xml.append(f"    <file path='{f}'/>")
            xml.append("  </files>")

        xml.append("</task_context>")
        return "\n".join(xml)
