# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Web Search operations for MCP server.

No API key required - uses DuckDuckGo search.
"""

import asyncio
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from pydantic import BaseModel

from dedalus_mcp import tool


# --- Response Models ---------------------------------------------------------


class WebSearchResult(BaseModel):
    """Generic web search result."""

    success: bool
    data: Any = None
    error: str | None = None


# --- Helper ------------------------------------------------------------------


async def _search_web(query: str, num_results: int = 5) -> list[dict[str, str]]:
    """Search the web using DuckDuckGo.

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        List of search results with title, url, description
    """
    try:
        # Run sync DuckDuckGo search in thread pool
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: list(DDGS().text(query, max_results=num_results)),
        )
        
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "description": r.get("body", ""),
            }
            for r in results
        ]
    except Exception as e:
        raise Exception(f"Search failed: {e}")


async def _extract_content(url: str, max_length: int | None = None) -> dict[str, Any]:
    """Extract content from a web page.

    Args:
        url: URL to extract content from
        max_length: Maximum content length (None for no limit)

    Returns:
        Dict with title, content, word_count
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()
            
            # Get title
            title = soup.title.string if soup.title else urlparse(url).netloc
            
            # Get main content - try common content containers
            main_content = None
            for selector in ["main", "article", '[role="main"]', ".content", "#content"]:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.body if soup.body else soup
            
            # Extract text
            text = main_content.get_text(separator="\n", strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            text = "\n".join(lines)
            
            # Apply max length
            if max_length and len(text) > max_length:
                text = text[:max_length] + f"\n\n[Content truncated at {max_length} characters]"
            
            word_count = len(text.split())
            
            return {
                "title": title,
                "content": text,
                "word_count": word_count,
                "content_length": len(text),
            }
    except Exception as e:
        return {
            "title": urlparse(url).netloc,
            "content": None,
            "error": str(e),
        }


# --- Web Search Tools --------------------------------------------------------


@tool(
    description=(
        "Search the web and fetch complete page content from top results. "
        "This is the most comprehensive web search tool - it searches the web "
        "and follows the resulting links to extract their full page content. "
        "Use get_web_search_summaries for a lightweight alternative."
    )
)
async def full_web_search(
    query: str,
    limit: int = 5,
    include_content: bool = True,
    max_content_length: int | None = None,
) -> WebSearchResult:
    """Search the web and optionally fetch full content.

    Args:
        query: Search query to execute.
        limit: Number of results to return (1-10, default 5).
        include_content: Whether to fetch full page content (default True).
        max_content_length: Maximum characters per result content (None = no limit).

    Returns:
        WebSearchResult with search results and content.
    """
    limit = max(1, min(limit, 10))

    try:
        # Search
        search_results = await _search_web(query, limit)
        
        if not search_results:
            return WebSearchResult(
                success=True,
                data={"query": query, "results": [], "message": "No results found."},
            )
        
        results = []
        for sr in search_results:
            result = {
                "title": sr["title"],
                "url": sr["url"],
                "description": sr["description"],
            }
            
            # Fetch content if requested
            if include_content and sr["url"]:
                content_data = await _extract_content(sr["url"], max_content_length)
                result["full_content"] = content_data.get("content")
                result["word_count"] = content_data.get("word_count")
                if content_data.get("error"):
                    result["fetch_error"] = content_data["error"]
            
            results.append(result)
        
        return WebSearchResult(
            success=True,
            data={
                "query": query,
                "total_results": len(results),
                "results": results,
            },
        )
    except Exception as e:
        return WebSearchResult(success=False, error=str(e))


@tool(
    description=(
        "Search the web and return only search result snippets/descriptions "
        "without following links to extract full page content. "
        "This is a lightweight alternative to full_web_search."
    )
)
async def get_web_search_summaries(
    query: str,
    limit: int = 5,
) -> WebSearchResult:
    """Search the web and return summaries only.

    Args:
        query: Search query to execute.
        limit: Number of search results to return (1-10, default 5).

    Returns:
        WebSearchResult with search summaries.
    """
    limit = max(1, min(limit, 10))

    try:
        search_results = await _search_web(query, limit)
        
        return WebSearchResult(
            success=True,
            data={
                "query": query,
                "total_results": len(search_results),
                "results": search_results,
            },
        )
    except Exception as e:
        return WebSearchResult(success=False, error=str(e))


@tool(
    description=(
        "Extract and return the full content from a single web page URL. "
        "Useful for getting detailed content from a specific webpage."
    )
)
async def get_single_web_page_content(
    url: str,
    max_content_length: int | None = None,
) -> WebSearchResult:
    """Extract content from a single web page.

    Args:
        url: The URL of the web page to extract content from.
        max_content_length: Maximum characters (None = no limit).

    Returns:
        WebSearchResult with page content.
    """
    try:
        content_data = await _extract_content(url, max_content_length)
        
        if content_data.get("error"):
            return WebSearchResult(success=False, error=content_data["error"])
        
        return WebSearchResult(
            success=True,
            data={
                "url": url,
                "title": content_data["title"],
                "content": content_data["content"],
                "word_count": content_data["word_count"],
                "content_length": content_data["content_length"],
            },
        )
    except Exception as e:
        return WebSearchResult(success=False, error=str(e))


# --- Export ------------------------------------------------------------------

web_search_tools = [
    full_web_search,
    get_web_search_summaries,
    get_single_web_page_content,
]
