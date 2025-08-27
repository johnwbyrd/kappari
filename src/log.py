#!/usr/bin/env python3
"""
Clean logging interface.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global flag to ensure initialization happens only once
_initialized = False


def _setup_logging() -> None:
    """Internal function to set up logging configuration."""
    global _initialized
    if _initialized:
        return
    
    # Get configuration from environment
    log_level = os.getenv('KAPPARI_LOG_LEVEL', 'INFO')
    log_path = Path(os.getenv('KAPPARI_LOG_PATH', './logs'))
    
    # Create log directory
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.addHandler(console_handler)
    
    # Main log with rotation
    main_log = log_path / 'main.log'
    main_handler = logging.handlers.RotatingFileHandler(
        main_log, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    main_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(main_handler)
    
    # Error log
    error_log = log_path / 'errors.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_log, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    error_handler.setFormatter(detailed_formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)
    
    # Quiet third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    _initialized = True


# Clean public interface - these are the ONLY functions other modules should use

def debug(msg: str, *args) -> None:
    """Log a debug message."""
    _setup_logging()
    logging.debug(msg, *args)


def info(msg: str, *args) -> None:
    """Log an info message."""
    _setup_logging()
    logging.info(msg, *args)


def warning(msg: str, *args) -> None:
    """Log a warning message."""
    _setup_logging()
    logging.warning(msg, *args)


def error(msg: str, *args) -> None:
    """Log an error message."""
    _setup_logging()
    logging.error(msg, *args)


def critical(msg: str, *args) -> None:
    """Log a critical message."""
    _setup_logging()
    logging.critical(msg, *args)


if __name__ == "__main__":
    # Test the logging interface
    info("Testing info message")
    debug("Testing debug message") 
    warning("Testing warning message")
    error("Testing error message")
    critical("Testing critical message")
    
    print("Logging test complete. Check log files.")