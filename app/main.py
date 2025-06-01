from fastapi import FastAPI
from app.routers import capitals, health
from app.core.config import settings

app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(capitals.router, tags=["capitals"])