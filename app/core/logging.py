import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from app.core.config import settings

# Configure logging
def setup_logging():
    log_level = getattr(logging, getattr(settings, "LOG_LEVEL", "INFO").upper(), logging.INFO)
    log_dir = getattr(settings, "LOG_DIR", "logs")
    log_file = getattr(settings, "LOG_FILE", "app.log")
    max_bytes = getattr(settings, "LOG_MAX_BYTES", 5 * 1024 * 1024)  # 5 MB
    backup_count = getattr(settings, "LOG_BACKUP_COUNT", 5)

    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    # Format for logs
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Rotating file handler
    file_handler = RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(log_format))

    # Root logger setup
    logging.basicConfig(
        level=log_level,
        handlers=[console_handler, file_handler],
        format=log_format,
        force=True  # Overwrite any existing handlers
    )

    logger = logging.getLogger("app")
    logger.setLevel(log_level)
    
    return logger

logger = setup_logging()