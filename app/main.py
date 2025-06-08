from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.routers import capitals, health, economic_data, geo_data
from app.core.config import settings
import asyncio
import os
from typing import Callable
import time

# Custom middleware for timeout handling
class TimeoutMiddleware:
    def __init__(self, app: FastAPI, timeout: float = 10.0):
        self.app = app
        self.timeout = timeout

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        timeout_handler = asyncio.create_task(
            asyncio.wait_for(
                self.app(scope, receive, send),
                timeout=self.timeout
            )
        )
        
        try:
            await timeout_handler
        except asyncio.TimeoutError:
            return await JSONResponse(
                status_code=504,
                content={"detail": "Request timeout"}
            )(scope, receive, send)

# Update app configuration
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    default_response_class=JSONResponse
)

# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TimeoutMiddleware, timeout=60.0)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(capitals.router, prefix="/api/v1", tags=["capitals"])
app.include_router(economic_data.router, prefix="/api/v1", tags=["economic-data"])
app.include_router(geo_data.router, prefix="/api/v1", tags=["geo-data"])

# Mount static files for the WebGL frontend
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")