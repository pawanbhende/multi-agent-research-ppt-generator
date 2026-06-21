"""
Agent 3 — The Designer / PPTX Architect Agent

Responsibilities (full implementation lands in Phase 2):
  1. Translate the Analyst's typed outline into layout/design instructions
     (color palette, typography, bounding boxes per layout type).
  2. Drive `app.services.pptx_engine` to render the final .pptx with
     python-pptx, ensuring no overlapping text / generic white slides.

For Phase 1 we wire the node into the graph with a working stub so the
end-to-end graph is runnable today; `pptx_engine.generate_presentation`
already has a real (if minimal) implementation to validate the contract.
"""

from app.agents.state import AgentLogEvent, ResearchState
from app.core.logging_config import logger
from app.services.pptx_engine import generate_presentation


async def designer_node(state: ResearchState) -> dict:
    topic = state["topic"]
    outline = state["outline"]

    logs = [AgentLogEvent(agent="designer", message="Designing slide layouts and compiling .pptx...", status="started")]

    pptx_path = await generate_presentation(topic=topic, outline=outline)

    logs.append(
        AgentLogEvent(agent="designer", message=f"Presentation generated at {pptx_path}", status="completed")
    )
    logger.info(f"[Designer] Saved presentation to {pptx_path}")

    return {
        "pptx_path": pptx_path,
        "logs": logs,
        "current_stage": "done",
    }
