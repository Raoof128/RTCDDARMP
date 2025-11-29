"""
Logging configuration and utilities
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Setup structured logging for the application.

    Parameters:
    -----------
    log_level : str
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
    --------
    logging.Logger
        Configured logger
    """
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    logger = logging.getLogger("RCD2")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    log_file = log_dir / f"rcd2_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Parameters:
    -----------
    name : str
        Logger name (typically __name__)

    Returns:
    --------
    logging.Logger
        Logger instance
    """
    return logging.getLogger(f"RCD2.{name}")
