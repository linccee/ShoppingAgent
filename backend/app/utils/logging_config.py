"""
Logging configuration with separate log files for different modules.
"""
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Literal

# Base log directory
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
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


def setup_logger(
    name: Literal[*LOG_FILES.keys()],
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Get or create a logger with file and console handlers.
    Each logger writes to its own dedicated log file.
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Determine log file path
    log_file = LOG_DIR / f"{LOG_FILES[name]}_{date.today()}.log"

    # File handler (rotated daily)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Formatter
    fmt = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=date_fmt)

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Convenience loggers
auth_logger = setup_logger("auth")
chat_logger = setup_logger("chat")
session_logger = setup_logger("session")
user_logger = setup_logger("user")
tools_logger = setup_logger("tools")
db_logger = setup_logger("db")
agent_logger = setup_logger("agent")
api_logger = setup_logger("api")