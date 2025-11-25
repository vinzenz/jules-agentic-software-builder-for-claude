"""
Long-running Claude CLI session for efficient multi-agent orchestration.

Instead of spawning a new Claude CLI process for each agent, this module
maintains a single persistent session that can handle multiple prompts.

Key Benefits:
- Single CLI startup overhead (not 40+)
- Streaming output with real-time logging
- Session state persistence across agent calls
- Reduced memory and process overhead

Usage:
    session = LongRunningCLISession(project_root)
    session.start()

    # Send multiple prompts to the same session
    response = session.send_prompt("First agent task...")
    response = session.send_prompt("Second agent task...")

    session.stop()
"""

import json
import os
import queue
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
    Maintains a long-running Claude CLI session for multi-agent orchestration.

    Instead of spawning a new process for each agent call, this class
    maintains a single CLI process that handles multiple prompts in sequence.
    All streamed messages are logged for debugging and transparency.
    """

    # Delimiter for message boundaries in streaming mode
    MESSAGE_DELIMITER = "\n---END_OF_RESPONSE---\n"

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

        # Process state
        self._process: Optional[subprocess.Popen] = None
        self._stdout_queue: queue.Queue = queue.Queue()
        self._stderr_queue: queue.Queue = queue.Queue()
        self._reader_threads: List[threading.Thread] = []
        self._running = False

        # Stream logger
        log_file = stream_log_file or (self.project_root / ".tasks" / "stream.log")
        self.stream_logger = StreamLogger(
            log_file=log_file,
            log_to_console=log_to_console,
        )

        # Response accumulator
        self._current_response: List[str] = []
        self._response_complete = threading.Event()

    def start(self, model: str = "sonnet") -> None:
        """
        Start the Claude CLI process in conversation mode.

        Args:
            model: Model to use (sonnet, opus, haiku)
        """
        if self._running:
            logger.warning("Session already running")
            return

        logger.info(f"Starting long-running Claude CLI session in {self.project_root}")

        # Prepare environment
        env = os.environ.copy()
        local_claude_dir = self.project_root / ".claude"
        if local_claude_dir.exists():
            env["CLAUDE_CONFIG_DIR"] = str(local_claude_dir)

        # Start Claude CLI in conversation mode with JSON streaming
        # Using --output-format stream-json for parseable streaming output
        cmd = [
            "claude",
            "--model",
            model,
            "--output-format",
            "stream-json",
            "--dangerously-skip-permissions",
            "--allowedTools",
            "Task,Read,Write,Edit,Glob,Grep,Bash",
        ]

        logger.debug(f"Starting CLI with command: {' '.join(cmd)}")

        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(self.project_root),
            env=env,
            bufsize=1,  # Line buffered
        )

        self._running = True

        # Start reader threads
        self._start_reader_threads()

        logger.info("Long-running CLI session started")

    def _start_reader_threads(self) -> None:
        """Start background threads to read stdout and stderr."""

        def read_stdout():
            """Read stdout line by line."""
            try:
                while self._running and self._process and self._process.stdout:
                    line = self._process.stdout.readline()
                    if not line:
                        if self._process.poll() is not None:
                            break
                        continue

                    self._stdout_queue.put(line)
                    self._process_stdout_line(line)

            except Exception as e:
                logger.error(f"Error reading stdout: {e}")

        def read_stderr():
            """Read stderr line by line."""
            try:
                while self._running and self._process and self._process.stderr:
                    line = self._process.stderr.readline()
                    if not line:
                        if self._process.poll() is not None:
                            break
                        continue

                    self._stderr_queue.put(line)
                    self.stream_logger.log_incoming(line.strip(), {"source": "stderr"})

            except Exception as e:
                logger.error(f"Error reading stderr: {e}")

        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)

        stdout_thread.start()
        stderr_thread.start()

        self._reader_threads = [stdout_thread, stderr_thread]

    def _process_stdout_line(self, line: str) -> None:
        """Process a line from stdout, parsing streaming JSON."""
        line = line.strip()
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

            # Accumulate content for final response
            if event.event_type == StreamEventType.CONTENT_DELTA:
                content = data.get("delta", {}).get("text", "")
                self._current_response.append(content)
            elif event.event_type == StreamEventType.RESULT:
                # Message complete
                self._response_complete.set()

        except json.JSONDecodeError:
            # Non-JSON output, log as raw
            self.stream_logger.log_incoming(line, {"format": "raw"})
            self._current_response.append(line)

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

    def send_prompt(self, prompt: str, timeout: float = 600.0) -> str:
        """
        Send a prompt to the CLI and get the response.

        Args:
            prompt: The prompt to send
            timeout: Maximum time to wait for response (seconds)

        Returns:
            The complete response text

        Raises:
            RuntimeError: If session is not running
            TimeoutError: If response takes too long
        """
        if not self._running or not self._process:
            raise RuntimeError("Session is not running. Call start() first.")

        # Reset response state
        self._current_response = []
        self._response_complete.clear()

        # Log outgoing prompt
        self.stream_logger.log_outgoing(prompt)

        # Send prompt to stdin
        logger.debug(f"Sending prompt ({len(prompt)} chars)")
        try:
            self._process.stdin.write(prompt + "\n")
            self._process.stdin.flush()
        except BrokenPipeError:
            raise RuntimeError("CLI process has terminated unexpectedly")

        # Wait for response
        if not self._response_complete.wait(timeout=timeout):
            raise TimeoutError(f"Response not received within {timeout}s")

        # Combine response
        response = "".join(self._current_response)
        logger.debug(f"Received response ({len(response)} chars)")

        return response

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
        if not self._running or not self._process:
            raise RuntimeError("Session is not running. Call start() first.")

        # Reset state
        self._current_response = []
        self._response_complete.clear()

        # Log and send
        self.stream_logger.log_outgoing(prompt)

        try:
            self._process.stdin.write(prompt + "\n")
            self._process.stdin.flush()
        except BrokenPipeError:
            raise RuntimeError("CLI process has terminated unexpectedly")

        # Yield events from queue
        start_time = time.time()
        while not self._response_complete.is_set():
            try:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    raise TimeoutError(f"Response not received within {timeout}s")

                # Get next line with timeout
                line = self._stdout_queue.get(timeout=1.0)

                try:
                    data = json.loads(line.strip())
                    event = self._parse_stream_event(data, line)

                    # Call chunk callback for content
                    if on_chunk and event.event_type == StreamEventType.CONTENT_DELTA:
                        content = data.get("delta", {}).get("text", "")
                        if content:
                            on_chunk(content)

                    yield event

                except json.JSONDecodeError:
                    # Raw output
                    yield StreamEvent(
                        event_type=StreamEventType.SYSTEM,
                        timestamp=datetime.utcnow(),
                        raw_line=line,
                    )

            except queue.Empty:
                continue

    def is_running(self) -> bool:
        """Check if the session is still running."""
        if not self._process:
            return False
        return self._process.poll() is None

    def stop(self) -> None:
        """Stop the CLI session gracefully."""
        if not self._running:
            return

        logger.info("Stopping long-running CLI session")

        self._running = False

        # Close stdin to signal EOF
        if self._process and self._process.stdin:
            try:
                self._process.stdin.close()
            except Exception:
                pass

        # Wait for process to terminate
        if self._process:
            try:
                self._process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                logger.warning("Process did not terminate gracefully, killing...")
                self._process.kill()
                self._process.wait()

        # Wait for reader threads
        for thread in self._reader_threads:
            thread.join(timeout=2.0)

        # Close logger
        self.stream_logger.close()

        self._process = None
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
