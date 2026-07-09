import logging
import sys
import os
from loguru import logger


class InterceptHandler(logging.Handler):
    """
    Default handler to intercept standard library Logging messages and
    delegate them to Loguru.
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = sys._getframe(2), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_app_logging(log_dir: str = "logs", log_file: str = "traffic_violation.log"):
    """
    Reconfigure logging to use Loguru handlers and intercept standard logs.
    """
    # Create logs directory
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    # Clear default Loguru configurations
    logger.remove()

    # Add stdout handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # Add rotating file handler
    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )

    # Configure standard logging to use InterceptHandler
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.INFO)

    # Intercept Uvicorn loggers specifically
    for logger_name in ("uvicorn", "uvicorn.asgi", "uvicorn.access"):
        mod_logger = logging.getLogger(logger_name)
        mod_logger.handlers = [InterceptHandler()]
        mod_logger.propagate = False
