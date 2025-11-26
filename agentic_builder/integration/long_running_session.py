"""
Long-running Claude CLI session for efficient multi-agent orchestration.

This module provides streaming output handling and centralized logging for
Claude CLI invocations. Each prompt spawns a subprocess but output is streamed
in real-time with unified logging.

Key Benefits:
- Real-time streaming output with progress visibility
- Centralized logging of all messages to/from Claude
- Structured event parsing from Claude CLI's stream-json format
- Session state persistence across agent calls

Usage:
    session = LongRunningCLISession(project_root)
    session.start()

    # Send prompts with streaming output
    response = session.send_prompt("First agent task...")
    response = session.send_prompt("Second agent task...")

    session.stop()
"""

import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

from agentic_builder.common.logging_config import get_logger

logger = get_logger(__name__)


class MessageDirection(str, Enum):
    """Direction of a streamed message."""

    OUTGOING = "outgoing"  # Sent to Claude
    INCOMING = "incoming"  # Received from Claude


class StreamEventType(str, Enum):
    """Types of streaming events from Claude CLI."""

    # Content events
    CONTENT_START = "content_start"
    CONTENT_DELTA = "content_delta"
    CONTENT_DONE = "content_done"

    # Tool events
    TOOL_USE_START = "tool_use_start"
    TOOL_USE_DELTA = "tool_use_delta"
    TOOL_USE_DONE = "tool_use_done"
    TOOL_RESULT = "tool_result"

    # Message events
    MESSAGE_START = "message_start"
    MESSAGE_DELTA = "message_delta"
    MESSAGE_DONE = "message_done"

    # System events
    SYSTEM = "system"
    ERROR = "error"
    RESULT = "result"


@dataclass
class StreamEvent:
    """A single streaming event from Claude CLI."""

    event_type: StreamEventType
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    raw_line: str = ""


@dataclass
class StreamMessage:
    """A logged message with direction and content."""

    direction: MessageDirection
    timestamp: datetime
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class StreamLogger:
    """
    Logger for streaming messages to/from Claude CLI.

    Logs messages in real-time as they are sent or received, with
    configurable output destinations (file, console, callback).
    """

    def __init__(
        self,
        log_file: Optional[Path] = None,
        log_to_console: bool = False,
        on_message: Optional[Callable[[StreamMessage], None]] = None,
    ):
        """
        Initialize the stream logger.

        Args:
            log_file: Path to log file (creates if not exists)
            log_to_console: Whether to also print to console
            on_message: Optional callback for each message
        """
        self.log_file = log_file
        self.log_to_console = log_to_console
        self.on_message = on_message
        self._messages: List[StreamMessage] = []
        self._file_handle = None
        self._lock = threading.Lock()

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            self._file_handle = open(log_file, "a", encoding="utf-8")

    def log_outgoing(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log an outgoing message (sent to Claude)."""
        msg = StreamMessage(
            direction=MessageDirection.OUTGOING,
            timestamp=datetime.utcnow(),
            content=content,
            metadata=metadata or {},
        )
        self._log_message(msg)

    def log_incoming(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log an incoming message (received from Claude)."""
        msg = StreamMessage(
            direction=MessageDirection.INCOMING,
            timestamp=datetime.utcnow(),
            content=content,
            metadata=metadata or {},
        )
        self._log_message(msg)

    def log_event(self, event: StreamEvent) -> None:
        """Log a streaming event."""
        content = json.dumps(event.data) if event.data else event.raw_line
        msg = StreamMessage(
            direction=MessageDirection.INCOMING,
            timestamp=event.timestamp,
            content=content,
            metadata={"event_type": event.event_type.value},
        )
        self._log_message(msg)

    def _log_message(self, msg: StreamMessage) -> None:
        """Internal method to log a message to all destinations."""
        with self._lock:
            self._messages.append(msg)

            # Format for logging
            direction_symbol = ">>>" if msg.direction == MessageDirection.OUTGOING else "<<<"
            timestamp = msg.timestamp.strftime("%H:%M:%S.%f")[:-3]
            meta_str = f" [{msg.metadata}]" if msg.metadata else ""

            # Truncate long content for display
            display_content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
            log_line = f"[{timestamp}] {direction_symbol} {display_content}{meta_str}"

            if self.log_to_console:
                print(log_line, file=sys.stderr)

            if self._file_handle:
                # Full content to file
                self._file_handle.write(f"{log_line}\n")
                if len(msg.content) > 500:
                    self._file_handle.write(f"    [Full content: {len(msg.content)} chars]\n")
                self._file_handle.flush()

            if self.on_message:
                self.on_message(msg)

    def get_messages(self) -> List[StreamMessage]:
        """Get all logged messages."""
        with self._lock:
            return list(self._messages)

    def close(self) -> None:
        """Close the log file if open."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None


class LongRunningCLISession:
    """
    Manages Claude CLI invocations with streaming output and centralized logging.

    Each prompt spawns a new subprocess (Claude CLI requires -p flag), but output
    is streamed in real-time and logged centrally for debugging and transparency.

    This provides the benefits of:
    - Real-time progress visibility
    - Centralized logging across all agent calls
    - Structured event parsing from streaming JSON
    """

    def __init__(
        self,
        project_root: Path,
        stream_log_file: Optional[Path] = None,
        log_to_console: bool = False,
        on_stream_event: Optional[Callable[[StreamEvent], None]] = None,
    ):
        """
        Initialize the long-running session.

        Args:
            project_root: Working directory for the CLI
            stream_log_file: Optional path for stream logging
            log_to_console: Whether to log streams to console
            on_stream_event: Optional callback for each streaming event
        """
        self.project_root = Path(project_root)
        self.on_stream_event = on_stream_event
        self._running = False
        self._model = "sonnet"

        # Stream logger
        log_file = stream_log_file or (self.project_root / ".tasks" / "stream.log")
        self.stream_logger = StreamLogger(
            log_file=log_file,
            log_to_console=log_to_console,
        )

    def start(self, model: str = "sonnet") -> None:
        """
        Start the session (initialize logging).

        Args:
            model: Model to use (sonnet, opus, haiku)
        """
        if self._running:
            logger.warning("Session already running")
            return

        logger.info(f"Starting long-running Claude CLI session in {self.project_root}")
        self._model = model
        self._running = True
        logger.info("Long-running CLI session started")

    def is_running(self) -> bool:
        """Check if the session is running."""
        return self._running

    def send_prompt(self, prompt: str, timeout: float = 600.0) -> str:
        """
        Send a prompt to Claude CLI and get the response with streaming.

        Args:
            prompt: The prompt to send
            timeout: Maximum time to wait for response (seconds)

        Returns:
            The complete response text

        Raises:
            RuntimeError: If session is not running
            TimeoutError: If response takes too long
        """
        if not self._running:
            raise RuntimeError("Session is not running. Call start() first.")

        # Log outgoing prompt
        self.stream_logger.log_outgoing(prompt)
        logger.debug(f"Sending prompt ({len(prompt)} chars)")

        # Prepare environment
        env = os.environ.copy()
        local_claude_dir = self.project_root / ".claude"
        if local_claude_dir.exists():
            env["CLAUDE_CONFIG_DIR"] = str(local_claude_dir)

        # Build command with -p flag for non-interactive mode
        # Note: --output-format stream-json requires --verbose
        cmd = [
            "claude",
            "--model",
            self._model,
            "--output-format",
            "stream-json",
            "--verbose",
            "--dangerously-skip-permissions",
            "--allowedTools",
            "Task,Read,Write,Edit,Glob,Grep,Bash",
            "-p",
            prompt,
        ]

        logger.debug(f"Running CLI command: claude --model {self._model} -p <prompt>")

        # Start subprocess with streaming output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(self.project_root),
            env=env,
            bufsize=1,  # Line buffered
        )

        # Collect response with streaming
        response_parts: List[str] = []
        start_time = time.time()

        try:
            # Read stdout line by line for streaming
            while True:
                # Check timeout
                if time.time() - start_time > timeout:
                    process.kill()
                    raise TimeoutError(f"Response not received within {timeout}s")

                # Check if process has ended
                if process.poll() is not None:
                    # Process finished, read any remaining output
                    remaining = process.stdout.read()
                    if remaining:
                        for line in remaining.strip().split("\n"):
                            if line:
                                self._process_output_line(line, response_parts)
                    break

                # Read next line (with small timeout to allow checking process status)
                line = process.stdout.readline()
                if line:
                    self._process_output_line(line.strip(), response_parts)

            # Check for errors
            stderr = process.stderr.read()
            if stderr:
                self.stream_logger.log_incoming(stderr, {"source": "stderr"})
                logger.debug(f"Stderr: {stderr[:500]}")

            if process.returncode != 0:
                logger.warning(f"CLI exited with code {process.returncode}")

        except Exception as e:
            process.kill()
            raise RuntimeError(f"Error during CLI execution: {e}") from e

        response = "".join(response_parts)
        logger.debug(f"Received response ({len(response)} chars)")

        return response

    def _process_output_line(self, line: str, response_parts: List[str]) -> None:
        """Process a single line of output, extracting content and logging events."""
        if not line:
            return

        # Try to parse as JSON streaming event
        try:
            data = json.loads(line)
            event = self._parse_stream_event(data, line)

            # Log the event
            self.stream_logger.log_event(event)

            # Call callback if set
            if self.on_stream_event:
                self.on_stream_event(event)

            # Extract text content from various event types
            if event.event_type == StreamEventType.CONTENT_DELTA:
                # Content block delta
                text = data.get("delta", {}).get("text", "")
                if text:
                    response_parts.append(text)
            elif event.event_type == StreamEventType.RESULT:
                # Final result - extract from result field
                result = data.get("result", "")
                if result and not response_parts:
                    response_parts.append(result)
            elif "content" in data:
                # Generic content field
                content = data.get("content", "")
                if isinstance(content, str) and content:
                    response_parts.append(content)

        except json.JSONDecodeError:
            # Non-JSON output, treat as raw text
            self.stream_logger.log_incoming(line, {"format": "raw"})
            response_parts.append(line)

    def _parse_stream_event(self, data: Dict[str, Any], raw_line: str) -> StreamEvent:
        """Parse a streaming JSON event into a StreamEvent."""
        event_type_str = data.get("type", "unknown")

        # Map to StreamEventType
        type_mapping = {
            "content_block_start": StreamEventType.CONTENT_START,
            "content_block_delta": StreamEventType.CONTENT_DELTA,
            "content_block_stop": StreamEventType.CONTENT_DONE,
            "tool_use": StreamEventType.TOOL_USE_START,
            "tool_result": StreamEventType.TOOL_RESULT,
            "message_start": StreamEventType.MESSAGE_START,
            "message_delta": StreamEventType.MESSAGE_DELTA,
            "message_stop": StreamEventType.MESSAGE_DONE,
            "system": StreamEventType.SYSTEM,
            "error": StreamEventType.ERROR,
            "result": StreamEventType.RESULT,
        }

        event_type = type_mapping.get(event_type_str, StreamEventType.SYSTEM)

        return StreamEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            data=data,
            raw_line=raw_line,
        )

    def send_and_stream(
        self,
        prompt: str,
        on_chunk: Optional[Callable[[str], None]] = None,
        timeout: float = 600.0,
    ) -> Iterator[StreamEvent]:
        """
        Send a prompt and yield streaming events.

        Args:
            prompt: The prompt to send
            on_chunk: Optional callback for each text chunk
            timeout: Maximum time to wait

        Yields:
            StreamEvent objects as they arrive
        """
        if not self._running:
            raise RuntimeError("Session is not running. Call start() first.")

        # Log outgoing prompt
        self.stream_logger.log_outgoing(prompt)

        # Prepare environment
        env = os.environ.copy()
        local_claude_dir = self.project_root / ".claude"
        if local_claude_dir.exists():
            env["CLAUDE_CONFIG_DIR"] = str(local_claude_dir)

        # Build command
        # Note: --output-format stream-json requires --verbose
        cmd = [
            "claude",
            "--model",
            self._model,
            "--output-format",
            "stream-json",
            "--verbose",
            "--dangerously-skip-permissions",
            "--allowedTools",
            "Task,Read,Write,Edit,Glob,Grep,Bash",
            "-p",
            prompt,
        ]

        # Start subprocess
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(self.project_root),
            env=env,
            bufsize=1,
        )

        start_time = time.time()

        try:
            while True:
                # Check timeout
                if time.time() - start_time > timeout:
                    process.kill()
                    raise TimeoutError(f"Response not received within {timeout}s")

                # Check if process ended
                if process.poll() is not None:
                    remaining = process.stdout.read()
                    if remaining:
                        for line in remaining.strip().split("\n"):
                            if line:
                                try:
                                    data = json.loads(line)
                                    event = self._parse_stream_event(data, line)
                                    if on_chunk and event.event_type == StreamEventType.CONTENT_DELTA:
                                        text = data.get("delta", {}).get("text", "")
                                        if text:
                                            on_chunk(text)
                                    yield event
                                except json.JSONDecodeError:
                                    yield StreamEvent(
                                        event_type=StreamEventType.SYSTEM,
                                        timestamp=datetime.utcnow(),
                                        raw_line=line,
                                    )
                    break

                # Read next line
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    try:
                        data = json.loads(line)
                        event = self._parse_stream_event(data, line)
                        self.stream_logger.log_event(event)

                        if on_chunk and event.event_type == StreamEventType.CONTENT_DELTA:
                            text = data.get("delta", {}).get("text", "")
                            if text:
                                on_chunk(text)

                        yield event
                    except json.JSONDecodeError:
                        self.stream_logger.log_incoming(line, {"format": "raw"})
                        yield StreamEvent(
                            event_type=StreamEventType.SYSTEM,
                            timestamp=datetime.utcnow(),
                            raw_line=line,
                        )

        except Exception as e:
            process.kill()
            raise RuntimeError(f"Error during streaming: {e}") from e

    def stop(self) -> None:
        """Stop the session and close logging."""
        if not self._running:
            return

        logger.info("Stopping long-running CLI session")
        self._running = False

        # Close logger
        self.stream_logger.close()

        logger.info("Long-running CLI session stopped")

    def __enter__(self) -> "LongRunningCLISession":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


def create_session_with_logging(
    project_root: Path,
    session_id: Optional[str] = None,
    log_to_console: bool = False,
) -> LongRunningCLISession:
    """
    Convenience function to create a session with proper logging setup.

    Args:
        project_root: Working directory
        session_id: Optional session ID for log file naming
        log_to_console: Whether to log to console

    Returns:
        Configured LongRunningCLISession
    """
    log_dir = project_root / ".tasks" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_name = f"stream_{session_id}_{timestamp}.log" if session_id else f"stream_{timestamp}.log"
    log_file = log_dir / log_name

    return LongRunningCLISession(
        project_root=project_root,
        stream_log_file=log_file,
        log_to_console=log_to_console,
    )
