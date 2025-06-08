import time
import uuid
import asyncio
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.logging import logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Add request timing header
        request.state.start_time = start_time
        request.state.request_id = request_id

        try:
            response = await asyncio.wait_for(
                call_next(request),
                timeout=60.0  # 60 second timeout
            )
            
            process_time = time.time() - start_time
            response.headers.update({
                "X-Request-ID": request_id,
                "X-Process-Time": f"{process_time:.3f}",
                "X-Rate-Limit": "60;w=60"  # Basic rate limiting info
            })
            
            return response
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timed out"}
            )
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )