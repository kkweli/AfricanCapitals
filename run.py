import uvicorn
from app.main import app
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.core.logging import logger

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

if __name__ == "__main__":
    logger.info("Starting African Capitals API")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=4,  # Number of worker processes
        limit_concurrency=100,  # Max concurrent connections
        timeout_keep_alive=5,  # Keep-alive timeout
        loop="uvloop",  # Faster event loop implementation
        http="httptools",  # Faster HTTP protocol implementation
        proxy_headers=True,
        forwarded_allow_ips="*"
    )