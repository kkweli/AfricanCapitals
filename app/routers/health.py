from fastapi import APIRouter, Depends
from datetime import datetime
from app.services.dependencies import get_timezone
from app.core.logging import logger

router = APIRouter()

@router.get("/health", summary="Health check endpoint")
def health_check(tz=Depends(get_timezone)):
    """
    Simple health check endpoint.
    Returns OK status and the current timestamp (host local timezone).
    """
    logger.info("Health check requested")
    now = datetime.now(tz)
    return {
        "status": "ok",
        "time": now.isoformat()
    }