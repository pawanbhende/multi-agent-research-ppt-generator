"""
Agent 2 — The Analyst / Outline Editor Agent

Responsibilities:
  1. Fact-check / de-duplicate the Researcher's raw summary.
  2. Structure findings into a slide-by-slide outline (typed SlideContent).
  3. Assign each slide a layout hint so the Designer agent (Phase 2) knows
     which python-pptx template to use — this is the critical hand-off
     contract between Agent 2 and Agent 3.
"""

import json

from app.agents.state import AgentLogEvent, ResearchState, SlideContent
from app.core.llm_router import get_chat_model
from app.core.logging_config import logger

OUTLINE_PROMPT = """You are a senior presentation editor. Using the research summary \
below, produce a slide-by-slide outline for a professional presentation on \
"{topic}". Use at most {max_slides} slides.

Rules:
- Slide 1 is always layout "title".
- Include at least one "metrics" slide if the research contains quantifiable data.
- Use "comparison" for any before/after or X-vs-Y content.
- The last slide is always layout "conclusion".
- Each slide needs 3-5 concise bullets (under 18 words each), not full paragraphs.
- Include short speaker_notes per slide elaborating the bullets for the presenter.
- Cite source domains in `citations` where claims came from a specific source.

Return ONLY valid JSON — a list of objects matching this schema, nothing else:
[
  {{
    "slide_number": 1,
    "layout": "title" | "agenda" | "section_header" | "content" | "metrics" | "comparison" | "quote" | "image_focus" | "conclusion",
    "title": "string",
    "bullets": ["string", ...],
    "speaker_notes": "string",
    "key_metric": "string or null",
    "citations": ["string", ...]
  }}
]

RESEARCH SUMMARY:
{research_summary}
"""


def _safe_parse_outline(raw_text: str) -> list[dict]:
    """Strips markdown code fences if the model wraps JSON in ```json blocks."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        cleaned = cleaned.removeprefix("json").strip()
    return json.loads(cleaned)


async def analyst_node(state: ResearchState) -> dict:
    topic = state["topic"]
    max_slides = state.get("max_slides", 12)
    research_summary = state["research_summary"]

    logs = [AgentLogEvent(agent="analyst", message="Fact-checking and structuring outline...", status="started")]

    llm = get_chat_model("analyst", temperature=0.3)
    response = await llm.ainvoke(
        OUTLINE_PROMPT.format(topic=topic, max_slides=max_slides, research_summary=research_summary)
    )

    try:
        parsed = _safe_parse_outline(response.content)
        outline = [SlideContent(**slide) for slide in parsed]
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[Analyst] Failed to parse outline JSON: {exc}")
        logs.append(AgentLogEvent(agent="analyst", message=f"Outline parsing failed: {exc}", status="error"))
        return {"logs": logs, "current_stage": "error", "error": str(exc)}

    outline_markdown = "\n\n".join(
        f"## Slide {s.slide_number}: {s.title}\n" + "\n".join(f"- {b}" for b in s.bullets)
        for s in outline
    )

    logs.append(
        AgentLogEvent(agent="analyst", message=f"Outline complete: {len(outline)} slides drafted", status="completed")
    )
    logger.info(f"[Analyst] Produced {len(outline)} slides")

    return {
        "outline": outline,
        "outline_markdown": outline_markdown,
        "logs": logs,
        "current_stage": "designing",
    }
