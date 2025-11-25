import re
from pathlib import Path

from agentic_builder.common.logging_config import get_logger, log_separator, truncate_for_log
from agentic_builder.common.types import AgentOutput, Artifact

# Module logger
logger = get_logger(__name__)


class ResponseParser:
    @staticmethod
    def parse(text: str) -> AgentOutput:
        log_separator(logger, "RESPONSE PARSING", char="-")
        logger.debug(f"Input text length: {len(text)} characters")

        # Simple XML parsing using regex for MVP
        # Robust implementation would use lxml or ElementTree, but LLM output might be malformed.

        # Extract summary
        logger.debug("Extracting <summary> tag...")
        summary_match = re.search(r"<summary>(.*?)</summary>", text, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else text.strip()[:100] + "..."
        if summary == text.strip()[:100] + "...":
            # If no summary tag, treat whole text as summary (fallback)
            logger.debug("No <summary> tag found, using full text as summary (fallback)")
            summary = text.strip()
        else:
            logger.debug(f"Found summary: {truncate_for_log(summary, max_length=200)}")

        # Extract artifacts - new format: <artifact path="..." action="created|modified"/>
        artifacts = []

        # New path-based format (self-closing or with empty content)
        logger.debug("Extracting artifacts (path-based format)...")
        path_pattern = re.compile(r'<artifact\s+path=["\'](.*?)["\']\s*(?:action=["\'](\w+)["\'])?\s*/?>', re.DOTALL)
        for match in path_pattern.finditer(text):
            file_path = match.group(1)
            action = match.group(2) if match.group(2) else "created"
            # Extract filename from path
            name = Path(file_path).name
            logger.debug(f"  Found artifact: path={file_path}, action={action}")
            artifacts.append(
                Artifact(
                    name=name,
                    type="file",
                    path=file_path,
                    content=None,  # Content is on disk, not in XML
                    action=action,
                )
            )

        # Legacy format fallback: <artifact name="..." type="...">content</artifact>
        # Only use if no path-based artifacts found
        if not artifacts:
            logger.debug("No path-based artifacts found, trying legacy format...")
            legacy_pattern = re.compile(
                r'<artifact\s+name=["\'](.*?)["\']\s+type=["\'](.*?)["\']\s*>(.*?)</artifact>', re.DOTALL
            )
            for match in legacy_pattern.finditer(text):
                name, type_, content = match.groups()
                logger.debug(f"  Found legacy artifact: name={name}, type={type_}, content_length={len(content)}")
                artifacts.append(Artifact(name=name, type=type_, content=content.strip()))

        logger.debug(f"Total artifacts found: {len(artifacts)}")

        # Extract next steps
        logger.debug("Extracting <next_steps> tag...")
        next_steps = []
        steps_match = re.search(r"<next_steps>(.*?)</next_steps>", text, re.DOTALL)
        if steps_match:
            lines = steps_match.group(1).strip().split("\n")
            next_steps = [line.strip().lstrip("- ").strip() for line in lines if line.strip()]
            logger.debug(f"Found {len(next_steps)} next steps: {next_steps}")
        else:
            logger.debug("No <next_steps> tag found")

        # Extract warnings
        logger.debug("Extracting <warnings> tag...")
        warnings = []
        warn_match = re.search(r"<warnings>(.*?)</warnings>", text, re.DOTALL)
        if warn_match:
            lines = warn_match.group(1).strip().split("\n")
            warnings = [line.strip().lstrip("- ").strip() for line in lines if line.strip()]
            logger.debug(f"Found {len(warnings)} warnings: {warnings}")
        else:
            logger.debug("No <warnings> tag found")

        logger.debug("Response parsing complete")
        return AgentOutput(
            success=True,  # Assume success if we got a response. In reality check for <error> tags
            summary=summary,
            artifacts=artifacts,
            next_steps=next_steps,
            warnings=warnings,
        )
