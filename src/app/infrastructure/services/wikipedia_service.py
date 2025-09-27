"""Wikipedia search service for encyclopedic content retrieval."""

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WikipediaSearchService:
    """Service for searching Wikipedia content."""

    def __init__(self, max_docs: int = 2):
        self.max_docs = max_docs
        self._wikipedia_loader = None

        try:
            from langchain_community.document_loaders import WikipediaLoader

            self._wikipedia_loader = WikipediaLoader
            logger.info("Wikipedia search service initialized successfully")
        except ImportError:
            logger.warning(
                "Wikipedia search not available - langchain_community not installed"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Wikipedia search: {e}")

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search Wikipedia for relevant articles."""
        try:
            if self._wikipedia_loader:
                loader = self._wikipedia_loader(
                    query=query, load_max_docs=self.max_docs
                )
                documents = loader.load()
                return self._format_wikipedia_results(documents)
            else:
                return self._get_mock_results(query)
        except Exception as e:
            logger.error(f"Wikipedia search failed for query '{query}': {e}")
            return self._get_mock_results(query)

    def _format_wikipedia_results(self, documents) -> List[Dict[str, Any]]:
        """Format Wikipedia documents into consistent structure."""
        formatted_results = []

        for doc in documents:
            metadata = doc.metadata
            formatted_results.append(
                {
                    "url": metadata.get("source", ""),
                    "title": metadata.get("title", "Wikipedia Article"),
                    "content": doc.page_content,
                    "page": metadata.get("page", ""),
                    "source_type": "wikipedia",
                }
            )

        return formatted_results

    def _get_mock_results(self, query: str) -> List[Dict[str, Any]]:
        """Return mock Wikipedia results when service is not available."""
        return [
            {
                "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                "title": f"Wikipedia: {query}",
                "content": f"""
{query} is a concept that encompasses various aspects and applications. This mock Wikipedia article 
provides foundational knowledge about {query}, including its definition, history, and significance.

## Overview
{query} represents an important topic in its field. The term has evolved over time and continues to 
be relevant in contemporary discussions and applications.

## History
The concept of {query} has roots that can be traced back to earlier developments in the field. 
Historical context shows how understanding of {query} has developed and matured.

## Applications
Modern applications of {query} span multiple domains and continue to evolve with technological 
and theoretical advances.

## See Also
Related concepts and topics that connect to {query} provide additional context and understanding.

This is mock content that would be replaced with actual Wikipedia content in a real implementation.
                """.strip(),
                "page": query.replace(" ", "_"),
                "source_type": "wikipedia_mock",
            },
            {
                "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}_in_practice",
                "title": f"{query} in Practice",
                "content": f"""
Practical applications and implementations of {query} demonstrate its real-world significance and utility.

## Practical Implementation
The implementation of {query} concepts in real-world scenarios shows the practical value and 
applicability of theoretical knowledge.

## Case Studies
Various case studies demonstrate how {query} principles are applied across different contexts 
and environments.

## Best Practices
Industry best practices for {query} help ensure effective implementation and positive outcomes.

This mock Wikipedia content illustrates how encyclopedic knowledge would supplement research analysis.
                """.strip(),
                "page": f"{query.replace(' ', '_')}_in_practice",
                "source_type": "wikipedia_mock",
            },
        ]

    def format_documents_for_context(self, results: List[Dict[str, Any]]) -> str:
        """Format Wikipedia results for use as context in LLM prompts."""
        if not results:
            return "No Wikipedia results found."

        formatted_docs = []
        for doc in results:
            source = doc.get("url", "")
            page = doc.get("page", "")
            content = doc.get("content", "")

            doc_text = (
                f'<Document source="{source}" page="{page}">\n{content}\n</Document>'
            )
            formatted_docs.append(doc_text)

        return "\n\n---\n\n".join(formatted_docs)

    def is_available(self) -> bool:
        """Check if Wikipedia search is available."""
        return self._wikipedia_loader is not None

    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the service configuration."""
        return {
            "service_name": "Wikipedia Search",
            "is_available": self.is_available(),
            "max_docs": self.max_docs,
            "using_mock": not self.is_available(),
        }
