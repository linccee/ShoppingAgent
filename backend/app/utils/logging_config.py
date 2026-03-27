"""
Logging configuration with structured directory layout and hourly rotation.

Directory structure:
    logs/
    └── {module}/
        └── {date}/
            ├── {module}_{HH}h.log          # Current hour
            ├── {module}_{HH}h.log.1        # Previous hour
            └── archive/                    # Old logs compressed
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

from logging.handlers import TimedRotatingFileHandler

# Base log directory (project root logs/)
LOG_DIR = Path(__file__).resolve().parents[3] / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log file names by category
LOG_FILES = {
    "auth": "auth",
    "chat": "chat",
    "session": "session",
    "user": "user",
    "tools": "tools",
    "db": "db",
    "agent": "agent",
    "api": "api",
}

# How many hourly rotations to keep (7 days * 24 hours = 168)
KEEP_HOURS = 168


def _configure_root_logger() -> None:
    """
    Configure the root logger to delegate to child loggers.
    This prevents logs from propagating to root handlers when
    modules use logging.getLogger(__name__).
    """
    root = logging.getLogger()
    root.setLevel(logging.WARNING)  # Only WARNING and above goes to root
    # Remove any existing handlers to prevent duplicate logging
    for h in root.handlers[:]:
        root.removeHandler(h)


def _get_module_log_dir(module: str) -> Path:
    """Get the log directory for a module, creating if needed."""
    log_dir = LOG_DIR / module / str(datetime.now().astimezone().date())
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logger(
    name: Literal[*LOG_FILES.keys()],
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Get or create a logger with file and console handlers.
    Uses hourly rotating file handler with structured directory layout.
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False  # Prevent duplicate to root logger

    # Determine log file path
    log_dir = _get_module_log_dir(name)
    current_hour = datetime.now().astimezone().strftime("%H")
    log_file = log_dir / f"{LOG_FILES[name]}_{current_hour}h.log"

    # Timed rotating handler - rotates every hour
    file_handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when="H",           # Rotate every hour
        interval=1,
        backupCount=KEEP_HOURS,
        encoding="utf-8",
        utc=False,
    )
    file_handler.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Formatter with timezone-aware time (shows local time in logs)
    fmt = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S %Z"
    formatter = logging.Formatter(fmt, datefmt=date_fmt)
    formatter.converter = lambda *args: datetime.now().astimezone().timetuple()

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Configure root logger once at module import
_configure_root_logger()

# Convenience loggers
auth_logger = setup_logger("auth")
chat_logger = setup_logger("chat")
session_logger = setup_logger("session")
user_logger = setup_logger("user")
tools_logger = setup_logger("tools")
db_logger = setup_logger("db")
agent_logger = setup_logger("agent")
api_logger = setup_logger("api")