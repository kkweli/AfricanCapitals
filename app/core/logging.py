import logging
import sys
from app.core.config import settings

# Configure logging
def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create logger for the app
    logger = logging.getLogger("app")
    logger.setLevel(log_level)
    
    return logger

logger = setup_logging()