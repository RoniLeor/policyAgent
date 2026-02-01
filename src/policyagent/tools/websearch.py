"""Web search tool using DuckDuckGo."""

from __future__ import annotations

import logging
from typing import Any

from duckduckgo_search import DDGS

from policyagent.config.settings import Settings
from policyagent.core.response import ToolResult
from policyagent.core.tool import Tool


logger = logging.getLogger(__name__)


class WebSearchTool(Tool):
    """Tool for searching the web using DuckDuckGo."""

    name = "web_search"
    description = "Search the web for information about medical billing rules and CPT codes."

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize web search tool.

        Args:
            settings: Application settings. If None, loads from environment.
        """
        if settings is None:
            settings = Settings()
        self.max_results = settings.websearch.max_results

    @classmethod
    def get_parameters_schema(cls) -> dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for finding medical billing information.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Search the web for information.

        Args:
            **kwargs: Must include 'query', optionally 'max_results'.

        Returns:
            ToolResult with search results.
        """
        query = kwargs.get("query")
        if not query:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Missing required parameter: query",
            )

        max_results = kwargs.get("max_results", self.max_results)

        try:
            results = self._search(query, max_results)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "query": query,
                    "results": results,
                    "count": len(results),
                },
            )
        except Exception as e:
            logger.exception("Web search failed")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Web search failed: {e}",
            )

    def _search(self, query: str, max_results: int) -> list[dict[str, str]]:
        """Perform web search.

        Args:
            query: Search query string.
            max_results: Maximum number of results.

        Returns:
            List of search results with title, url, and snippet.
        """
        results: list[dict[str, str]] = []

        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    }
                )

        return results
