import sys
import os
from loguru import logger

def configure_logging(log_dir: str = "logs", log_file: str = "traffic_violation.log"):
    """
    Configure loguru logger with custom formats and outputs (stdout + file).
    """
    # Ensure logs directory exists
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    # Remove default loguru handler
    logger.remove()

    # Add console logger
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )

    # Add file logger (with rotation and compression)
    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )

    logger.info("Structured logging pipeline initialized successfully with Loguru.")

# Auto-configure on import
configure_logging()
