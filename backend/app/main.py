"""
FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

The WebSocket route for real-time agent activity streaming is added in
Phase 3 and will be mounted alongside `api_router` below.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.core.logging_config import configure_logging, logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info(f"Starting Multi-Agent Research/PPTX backend [env={settings.app_env}]")
    settings.output_path  # ensures output dir exists on boot
    yield
    logger.info("Shutting down backend.")


app = FastAPI(
    title="Multi-Agent AI Research & Presentation Generator",
    description="Orchestrates Researcher, Analyst, and Designer agents to produce a downloadable .pptx",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Multi-Agent Research & Presentation Generator API", "docs": "/docs"}
