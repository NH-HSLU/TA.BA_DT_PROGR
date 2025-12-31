"""
Centralized logging configuration for Streamlit app.

Uses Python's built-in logging module with custom formatting.
Logs to both console and file.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Import config
import os
import sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import LoggingConfig, LOGS_DIR


# Create logs directory
LOGS_DIR.mkdir(exist_ok=True)

# Log file path with date
log_file = LOGS_DIR / f"{LoggingConfig.LOG_FILE_PREFIX}_{datetime.now().strftime('%Y%m%d')}{LoggingConfig.LOG_FILE_SUFFIX}"


def setup_logging(level: Optional[int] = None) -> logging.Logger:
    """
    Konfiguriert Logging für die Streamlit App.

    Args:
        level: Log-Level (logging.DEBUG, logging.INFO, etc.)
              Falls None, wird LoggingConfig.LOG_LEVEL verwendet

    Returns:
        Configured logger
    """
    if level is None:
        level = getattr(logging, LoggingConfig.LOG_LEVEL)

    # Root logger
    logger = logging.getLogger('ebkp_suite')
    logger.setLevel(level)

    # Verhindere doppelte Handler
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        LoggingConfig.LOG_FORMAT,
        datefmt=LoggingConfig.LOG_DATE_FORMAT
    )

    # Console Handler (für Streamlit)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Immer DEBUG ins File
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Verhindere Propagation zum Root Logger
    logger.propagate = False

    return logger


# Globaler Logger
logger = setup_logging()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Gibt einen Logger für ein bestimmtes Modul zurück.

    Args:
        name: Modul-Name (z.B. __name__)

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f'ebkp_suite.{name}')
    return logger


def cleanup_old_logs(max_age_days: int = None, max_files: int = None) -> int:
    """
    Löscht alte Log-Dateien.

    Args:
        max_age_days: Maximales Alter in Tagen
        max_files: Maximale Anzahl zu behaltender Dateien

    Returns:
        Anzahl gelöschter Dateien
    """
    if max_age_days is None:
        max_age_days = LoggingConfig.MAX_LOG_AGE_DAYS
    if max_files is None:
        max_files = LoggingConfig.MAX_LOG_FILES

    if not LOGS_DIR.exists():
        return 0

    # Finde alle Log-Dateien
    log_files = list(LOGS_DIR.glob(f"{LoggingConfig.LOG_FILE_PREFIX}_*{LoggingConfig.LOG_FILE_SUFFIX}"))

    if not log_files:
        return 0

    # Sortiere nach Änderungsdatum (neueste zuerst)
    log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    deleted_count = 0
    current_time = datetime.now().timestamp()

    for i, log_file in enumerate(log_files):
        # Behalte neueste max_files Dateien
        if i >= max_files:
            try:
                log_file.unlink()
                deleted_count += 1
                logger.debug(f"Deleted old log file (max files): {log_file.name}")
                continue
            except Exception as e:
                logger.error(f"Could not delete {log_file.name}: {e}")
                continue

        # Prüfe Alter
        file_age_days = (current_time - log_file.stat().st_mtime) / 86400
        if file_age_days > max_age_days:
            try:
                log_file.unlink()
                deleted_count += 1
                logger.debug(f"Deleted old log file (age): {log_file.name}")
            except Exception as e:
                logger.error(f"Could not delete {log_file.name}: {e}")

    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old log files")

    return deleted_count
