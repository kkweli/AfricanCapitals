import uvicorn
from app.main import app
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.core.logging import logger

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

if __name__ == "__main__":
    logger.info("Starting African Capitals API")
    uvicorn.run(app, host="0.0.0.0", port=8000)