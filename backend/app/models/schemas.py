"""Pydantic models for the FastAPI request/response layer."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.agents.state import AgentLogEvent, SlideContent


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=300, description="Research topic / presentation subject")
    max_sources: int = Field(default=8, ge=2, le=20)
    max_slides: int = Field(default=12, ge=3, le=25)


class GenerateResponse(BaseModel):
    success: bool
    topic: str
    pptx_path: Optional[str] = None
    outline: Optional[List[SlideContent]] = None
    logs: List[AgentLogEvent] = Field(default_factory=list)
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    app_env: str
