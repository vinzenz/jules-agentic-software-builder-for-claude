"""
Centralized logging configuration for the Agentic Builder.

This module provides:
- Configurable debug logging that can be enabled via CLI flag or environment variable
- Consistent log formatting across all modules
- Session-specific and global debug log files
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from agentic_builder.common.utils import get_project_root

# Module-level logger
_debug_enabled = False
_console_handler: Optional[logging.Handler] = None
_file_handler: Optional[logging.Handler] = None

# Log format with timestamp, level, module, and message
DEBUG_FORMAT = "%(asctime)s - %(levelname)s - [%(name)s] %(message)s"
DEBUG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the given module name.

    Args:
        name: The module name (typically __name__)

    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    return logger


def setup_debug_logging(
    enabled: bool = False,
    log_to_console: bool = True,
    log_to_file: bool = True,
    session_id: Optional[str] = None,
) -> None:
    """
    Configure debug logging for the entire application.

    Args:
        enabled: Whether to enable debug logging
        log_to_console: Whether to output debug logs to console (stderr)
        log_to_file: Whether to output debug logs to a file
        session_id: Optional session ID to create session-specific debug log
    """
    global _debug_enabled, _console_handler, _file_handler

    _debug_enabled = enabled or os.environ.get("AMAB_DEBUG", "0") == "1"

    if not _debug_enabled:
        return

    # Get the root logger for our package
    root_logger = logging.getLogger("agentic_builder")
    root_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(DEBUG_FORMAT, datefmt=DEBUG_DATE_FORMAT)

    # Console handler (stderr so it doesn't mix with normal output)
    if log_to_console:
        _console_handler = logging.StreamHandler(sys.stderr)
        _console_handler.setLevel(logging.DEBUG)
        _console_handler.setFormatter(formatter)
        root_logger.addHandler(_console_handler)

    # File handler
    if log_to_file:
        log_dir = get_project_root() / ".sessions" / "debug_logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if session_id:
            log_file = log_dir / f"debug_{session_id}_{timestamp}.log"
        else:
            log_file = log_dir / f"debug_{timestamp}.log"

        _file_handler = logging.FileHandler(log_file)
        _file_handler.setLevel(logging.DEBUG)
        _file_handler.setFormatter(formatter)
        root_logger.addHandler(_file_handler)

        # Log the debug log file location
        root_logger.info(f"Debug logging enabled. Log file: {log_file}")


def is_debug_enabled() -> bool:
    """Check if debug logging is currently enabled."""
    return _debug_enabled or os.environ.get("AMAB_DEBUG", "0") == "1"


def log_separator(logger: logging.Logger, title: str = "", char: str = "=", length: int = 80) -> None:
    """
    Log a visual separator for better readability in debug logs.

    Args:
        logger: The logger to use
        title: Optional title to center in the separator
        char: Character to use for the separator line
        length: Total length of the separator line
    """
    if title:
        padding = (length - len(title) - 2) // 2
        line = f"{char * padding} {title} {char * padding}"
        # Ensure exact length
        if len(line) < length:
            line += char
    else:
        line = char * length

    logger.debug(line)


def truncate_for_log(text: str, max_length: int = 2000, show_truncated: bool = True) -> str:
    """
    Truncate text for logging while preserving useful information.

    Args:
        text: The text to potentially truncate
        max_length: Maximum length before truncation
        show_truncated: Whether to show "[TRUNCATED]" marker

    Returns:
        The truncated text
    """
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    if show_truncated:
        truncated += f"\n... [TRUNCATED - {len(text) - max_length} more characters]"

    return truncated
