"""
The Orchestrator — wires Researcher -> Analyst -> Designer into a single
LangGraph StateGraph over the shared `ResearchState`.

Conditional routing: if the Analyst fails to parse a valid outline, the
graph routes straight to END with `current_stage="error"` rather than
calling the Designer agent on bad data.
"""

from langgraph.graph import END, StateGraph

from app.agents.analyst_agent import analyst_node
from app.agents.designer_agent import designer_node
from app.agents.researcher_agent import researcher_node
from app.agents.state import ResearchState


def _route_after_analyst(state: ResearchState) -> str:
    if state.get("current_stage") == "error":
        return "end"
    return "designer"


def build_research_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("researcher", researcher_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("designer", designer_node)

    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_conditional_edges(
        "analyst",
        _route_after_analyst,
        {"designer": "designer", "end": END},
    )
    graph.add_edge("designer", END)

    return graph.compile()


# Compiled once at import time and reused across requests.
research_graph = build_research_graph()


async def run_research_pipeline(topic: str, max_sources: int = 8, max_slides: int = 12) -> ResearchState:
    """Convenience entrypoint used by the API layer."""
    initial_state: ResearchState = {
        "topic": topic,
        "max_sources": max_sources,
        "max_slides": max_slides,
        "logs": [],
        "current_stage": "researching",
    }
    final_state = await research_graph.ainvoke(initial_state)
    return final_state
