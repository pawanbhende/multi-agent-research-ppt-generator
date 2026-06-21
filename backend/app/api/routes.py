"""
REST API routes. The WebSocket streaming endpoint (real-time agent log)
is added in Phase 3 — this router exposes the synchronous fallback so the
pipeline is independently testable today (e.g. via curl / Swagger UI).
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.agents.graph import run_research_pipeline
from app.core.config import get_settings
from app.core.logging_config import logger
from app.models.schemas import GenerateRequest, GenerateResponse, HealthResponse

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", app_env=settings.app_env)


@router.post("/generate", response_model=GenerateResponse)
async def generate_presentation_endpoint(payload: GenerateRequest):
    """
    Runs the full Researcher -> Analyst -> Designer pipeline synchronously
    and returns the resulting .pptx path + outline + agent logs.
    """
    try:
        result = await run_research_pipeline(
            topic=payload.topic,
            max_sources=payload.max_sources,
            max_slides=payload.max_slides,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline execution failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if result.get("current_stage") == "error":
        return GenerateResponse(
            success=False,
            topic=payload.topic,
            logs=result.get("logs", []),
            error=result.get("error", "Unknown pipeline error"),
        )

    return GenerateResponse(
        success=True,
        topic=payload.topic,
        pptx_path=result.get("pptx_path"),
        outline=result.get("outline"),
        logs=result.get("logs", []),
    )


@router.get("/download/{filename}")
async def download_presentation(filename: str):
    file_path = settings.output_path / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename,
    )
