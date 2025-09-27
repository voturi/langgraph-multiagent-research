"""Tavily search service for web search functionality."""

import logging
import os
from typing import Any, Dict, List, Optional

from ...domain.entities.research import SearchQuery

logger = logging.getLogger(__name__)


class TavilySearchService:
    """Service for performing web searches using Tavily API."""

    def __init__(self, api_key: Optional[str] = None, max_results: int = 3):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.max_results = max_results
        self._search_tool = None

        if self.api_key:
            try:
                from langchain_community.tools.tavily_search import TavilySearchResults

                self._search_tool = TavilySearchResults(max_results=self.max_results)
                logger.info("Tavily search service initialized successfully")
            except ImportError:
                logger.warning(
                    "Tavily search not available - langchain_community not installed"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Tavily search: {e}")
        else:
            logger.warning("TAVILY_API_KEY not found - search will use mock results")

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Perform web search using Tavily."""
        try:
            if self._search_tool:
                results = self._search_tool.invoke(query)
                return self._format_search_results(results)
            else:
                return self._get_mock_results(query)
        except Exception as e:
            logger.error(f"Tavily search failed for query '{query}': {e}")
            return self._get_mock_results(query)

    def _format_search_results(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format Tavily search results into consistent structure."""
        formatted_results = []

        for doc in results:
            formatted_results.append(
                {
                    "url": doc.get("url", ""),
                    "title": doc.get("title", ""),
                    "content": doc.get("content", ""),
                    "source_type": "web",
                }
            )

        return formatted_results

    def _get_mock_results(self, query: str) -> List[Dict[str, Any]]:
        """Return mock search results when Tavily is not available."""
        return [
            {
                "url": f"https://example.com/search?q={query.replace(' ', '+')}",
                "title": f"Mock Result 1 for: {query}",
                "content": f"This is a mock search result for the query: {query}. "
                f"In a real implementation, this would contain actual web search results "
                f"from Tavily API providing relevant information about the topic.",
                "source_type": "web_mock",
            },
            {
                "url": f"https://example.org/article/{query.replace(' ', '-').lower()}",
                "title": f"Mock Article: {query}",
                "content": f"Mock article content discussing various aspects of {query}. "
                f"This mock result demonstrates how web search results would be "
                f"integrated into the research assistant workflow.",
                "source_type": "web_mock",
            },
            {
                "url": f"https://example.net/research/{query.replace(' ', '_')}",
                "title": f"Research Paper: {query}",
                "content": f"Mock research paper abstract about {query}. "
                f"This would typically contain academic or technical information "
                f"relevant to the research topic being investigated.",
                "source_type": "web_mock",
            },
        ]

    def format_documents_for_context(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for use as context in LLM prompts."""
        if not results:
            return "No search results found."

        formatted_docs = []
        for doc in results:
            doc_text = f'<Document href="{doc.get("url", "")}">\n{doc.get("content", "")}\n</Document>'
            formatted_docs.append(doc_text)

        return "\n\n---\n\n".join(formatted_docs)

    def is_available(self) -> bool:
        """Check if Tavily search is available and configured."""
        return self._search_tool is not None and bool(self.api_key)

    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the service configuration."""
        return {
            "service_name": "Tavily Search",
            "is_available": self.is_available(),
            "has_api_key": bool(self.api_key),
            "max_results": self.max_results,
            "using_mock": not self.is_available(),
        }
