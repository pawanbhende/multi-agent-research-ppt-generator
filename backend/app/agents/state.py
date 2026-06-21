"""
Shared state object passed between nodes in the LangGraph pipeline.

Flow:  researcher_node -> analyst_node -> designer_node -> END

Each node reads what it needs from `ResearchState` and returns a partial
dict of updates that LangGraph merges back in. Keeping this as a single
typed dict (not scattered globals) is what makes the graph debuggable and
lets us stream intermediate state over the WebSocket in Phase 3.
"""

from typing import Annotated, List, Literal, Optional, TypedDict

from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    """A single piece of raw research evidence gathered by Agent 1."""

    url: str
    title: str
    snippet: str
    content: str = ""
    credibility_score: float = Field(default=0.5, ge=0.0, le=1.0)
    fetched_at: Optional[str] = None


class SlideContent(BaseModel):
    """A single slide as structured by Agent 2, ready for Agent 3 to design."""

    slide_number: int
    layout: Literal[
        "title", "agenda", "section_header", "content", "metrics", "comparison",
        "quote", "image_focus", "conclusion",
    ] = "content"
    title: str
    bullets: List[str] = Field(default_factory=list)
    speaker_notes: str = ""
    key_metric: Optional[str] = None  # e.g. "73%" highlighted big on metrics slides
    citations: List[str] = Field(default_factory=list)


class AgentLogEvent(BaseModel):
    """One line of the real-time activity log streamed to the frontend."""

    agent: Literal["researcher", "analyst", "designer", "system"]
    message: str
    status: Literal["started", "in_progress", "completed", "error"] = "in_progress"


def _append_logs(existing: List[AgentLogEvent], new: List[AgentLogEvent]) -> List[AgentLogEvent]:
    return existing + new


class ResearchState(TypedDict, total=False):
    # --- Input ---
    topic: str
    max_sources: int
    max_slides: int

    # --- Agent 1 output ---
    raw_sources: List[SourceDocument]
    research_summary: str

    # --- Agent 2 output ---
    outline: List[SlideContent]
    outline_markdown: str

    # --- Agent 3 output ---
    pptx_path: str
    theme: str

    # --- Pipeline control / observability ---
    logs: Annotated[List[AgentLogEvent], _append_logs]
    current_stage: Literal["researching", "analyzing", "designing", "done", "error"]
    error: Optional[str]
