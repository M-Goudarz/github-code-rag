from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Production-oriented RAG system for GitHub repositories.",
)

app.include_router(health_router)
