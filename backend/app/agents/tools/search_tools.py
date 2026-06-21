"""
Search tools used by the Researcher / OSINT agent.

Tavily is primary (built for LLM-agent research: returns clean snippets +
relevance scoring). Serper is a fallback for redundancy/cost balancing.
"""

from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agents.state import SourceDocument
from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
async def tavily_search(query: str, max_results: int = 8) -> List[SourceDocument]:
    """Primary search provider — optimized for agentic/RAG-style research."""
    if not settings.tavily_api_key:
        logger.warning("TAVILY_API_KEY not set — skipping Tavily search.")
        return []

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.tavily_api_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": False,
            },
        )
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("results", []):
        results.append(
            SourceDocument(
                url=item.get("url", ""),
                title=item.get("title", "Untitled"),
                snippet=item.get("content", "")[:500],
                content=item.get("content", ""),
                credibility_score=min(max(item.get("score", 0.5), 0.0), 1.0),
            )
        )
    logger.info(f"[Tavily] '{query}' -> {len(results)} results")
    return results


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=6))
async def serper_search(query: str, max_results: int = 8) -> List[SourceDocument]:
    """Fallback search provider via Serper (Google SERP API)."""
    if not settings.serper_api_key:
        logger.warning("SERPER_API_KEY not set — skipping Serper search.")
        return []

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": settings.serper_api_key},
            json={"q": query, "num": max_results},
        )
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("organic", [])[:max_results]:
        results.append(
            SourceDocument(
                url=item.get("link", ""),
                title=item.get("title", "Untitled"),
                snippet=item.get("snippet", ""),
                content=item.get("snippet", ""),
                credibility_score=0.6,
            )
        )
    logger.info(f"[Serper] '{query}' -> {len(results)} results")
    return results


async def run_web_search(query: str, max_results: int = 8) -> List[SourceDocument]:
    """
    Orchestrates the search step: try Tavily first, fall back to Serper,
    and de-duplicate by URL across both.
    """
    results = await tavily_search(query, max_results)

    if len(results) < max_results:
        fallback = await serper_search(query, max_results - len(results))
        seen_urls = {r.url for r in results}
        results.extend([r for r in fallback if r.url not in seen_urls])

    return results
