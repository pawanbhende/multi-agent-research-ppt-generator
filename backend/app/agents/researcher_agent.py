"""
Agent 1 — The Researcher / OSINT Agent

Responsibilities:
  1. Expand the user's topic into targeted search queries.
  2. Run web search (Tavily/Serper) across those queries.
  3. Deep-scrape the most promising URLs for full text.
  4. Score/filter for credibility and produce a condensed research summary
     that Agent 2 (Analyst) will fact-check and structure.
"""

from app.agents.state import AgentLogEvent, ResearchState
from app.agents.tools.scraper_tools import enrich_sources_with_full_text
from app.agents.tools.search_tools import run_web_search
from app.core.llm_router import get_chat_model
from app.core.logging_config import logger

QUERY_EXPANSION_PROMPT = """You are a research strategist. Given the topic below, \
produce {n} distinct, high-signal search queries that together would surface \
comprehensive, credible, up-to-date information for a professional presentation.

Topic: "{topic}"

Return ONLY a plain list, one query per line, no numbering, no commentary."""

SUMMARY_PROMPT = """You are an OSINT research analyst. Below are raw source excerpts \
gathered on the topic "{topic}". Produce a dense, fact-rich research summary \
(800-1200 words) that an editorial team can use to build a slide deck. \
Preserve concrete numbers, dates, named entities, and attribute claims to sources \
by domain name. Do not editorialize or add information not present in the sources.

SOURCES:
{sources_block}
"""


async def researcher_node(state: ResearchState) -> dict:
    topic = state["topic"]
    max_sources = state.get("max_sources", 8)
    logs = [AgentLogEvent(agent="researcher", message=f"Starting research on: '{topic}'", status="started")]

    llm = get_chat_model("researcher", temperature=0.4)

    # 1. Expand into targeted queries
    expansion_resp = await llm.ainvoke(
        QUERY_EXPANSION_PROMPT.format(topic=topic, n=4)
    )
    queries = [q.strip("-• ").strip() for q in expansion_resp.content.splitlines() if q.strip()]
    queries = queries[:4] or [topic]
    logs.append(AgentLogEvent(agent="researcher", message=f"Generated {len(queries)} search queries"))

    # 2. Search across all queries, dedupe by URL
    all_sources = []
    seen_urls = set()
    for q in queries:
        logs.append(AgentLogEvent(agent="researcher", message=f"Searching: \"{q}\""))
        results = await run_web_search(q, max_results=max(2, max_sources // len(queries)))
        for r in results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                all_sources.append(r)

    all_sources = all_sources[:max_sources]
    logs.append(AgentLogEvent(agent="researcher", message=f"Collected {len(all_sources)} unique sources"))

    # 3. Deep scrape for full text
    logs.append(AgentLogEvent(agent="researcher", message="Deep-scraping top sources for full content..."))
    enriched_sources = await enrich_sources_with_full_text(all_sources)

    # 4. Synthesize a research summary for the Analyst
    sources_block = "\n\n".join(
        f"[{s.title}] ({s.url})\n{(s.content or s.snippet)[:1500]}" for s in enriched_sources
    )
    summary_resp = await llm.ainvoke(SUMMARY_PROMPT.format(topic=topic, sources_block=sources_block))
    research_summary = summary_resp.content

    logs.append(AgentLogEvent(agent="researcher", message="Research phase complete", status="completed"))
    logger.info(f"[Researcher] Completed with {len(enriched_sources)} sources")

    return {
        "raw_sources": enriched_sources,
        "research_summary": research_summary,
        "logs": logs,
        "current_stage": "analyzing",
    }
