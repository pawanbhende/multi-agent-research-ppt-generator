"""
Scraper tools — used by the Researcher agent to pull full article text
from promising URLs, since search snippets alone are often too thin for
the Analyst agent to synthesize a credible deep-dive slide.
"""

import asyncio
from typing import List

import httpx
import trafilatura

from app.agents.state import SourceDocument
from app.core.logging_config import logger

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ResearchAgentBot/1.0; "
        "+https://example.com/bot)"
    )
}


async def scrape_url(url: str, timeout: float = 15.0) -> str:
    """Fetch and extract clean main-body text from a single URL."""
    try:
        async with httpx.AsyncClient(
            timeout=timeout, headers=HEADERS, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        extracted = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=True,
            favor_precision=True,
        )
        return extracted or ""
    except Exception as exc:  # noqa: BLE001 — log and degrade gracefully
        logger.warning(f"[Scraper] Failed to scrape {url}: {exc}")
        return ""


async def enrich_sources_with_full_text(
    sources: List[SourceDocument], concurrency: int = 5
) -> List[SourceDocument]:
    """
    Concurrently scrapes full-page content for each source and fills in
    `.content` when richer than the search snippet already had.
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def _enrich(source: SourceDocument) -> SourceDocument:
        async with semaphore:
            full_text = await scrape_url(source.url)
            if full_text and len(full_text) > len(source.content):
                source.content = full_text[:8000]  # cap to keep token usage sane
            return source

    enriched = await asyncio.gather(*[_enrich(s) for s in sources])
    return list(enriched)
