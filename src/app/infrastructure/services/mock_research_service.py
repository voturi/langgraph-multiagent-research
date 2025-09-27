"""Mock research services for testing without external dependencies."""

import logging
from typing import Any, Dict, List, Optional

from ...domain.entities.research import Analyst

logger = logging.getLogger(__name__)


class MockResearchService:
    """Mock service providing research functionality for testing."""

    def __init__(self):
        logger.info("Mock research service initialized")

    async def create_analysts(
        self, topic: str, max_analysts: int = 3, human_feedback: Optional[str] = None
    ) -> List[Analyst]:
        """Create mock analysts for testing."""
        analysts = [
            Analyst(
                name="Dr. Sarah Chen",
                role="Technical Architect",
                affiliation="Enterprise Software Solutions Inc.",
                description=f"Specializes in scalable system architecture and design patterns for {topic}. "
                f"Focuses on performance optimization and maintainability in large-scale applications.",
            ),
            Analyst(
                name="Marcus Rodriguez",
                role="Senior Developer",
                affiliation="Tech Startup Collective",
                description=f"Experienced in implementing {topic} in fast-paced startup environments. "
                f"Expert in rapid prototyping and iterative development methodologies.",
            ),
            Analyst(
                name="Prof. Elena Kowalski",
                role="Research Scientist",
                affiliation="University Computer Science Department",
                description=f"Academic researcher studying theoretical foundations of {topic}. "
                f"Publishes on best practices and emerging trends in software engineering.",
            ),
        ][:max_analysts]

        if human_feedback and "startup" in human_feedback.lower():
            # Add an additional startup-focused analyst based on feedback
            startup_analyst = Analyst(
                name="Alex Kim",
                role="Startup CTO",
                affiliation="Venture Capital Portfolio Company",
                description=f"Serial entrepreneur with experience scaling {topic} solutions from prototype to production. "
                f"Specializes in lean development approaches and technical leadership.",
            )
            if len(analysts) < max_analysts:
                analysts.append(startup_analyst)
            else:
                analysts[-1] = startup_analyst

        logger.info(f"Created {len(analysts)} mock analysts for topic: {topic}")
        return analysts

    async def search_web(self, query: str) -> List[Dict[str, Any]]:
        """Mock web search results."""
        return [
            {
                "url": f"https://techblog.com/articles/{query.replace(' ', '-').lower()}",
                "title": f"Best Practices for {query}",
                "content": f"Comprehensive guide to implementing {query} in production environments. "
                f"This article covers key considerations, common pitfalls, and proven strategies "
                f"for successful deployment and maintenance.",
                "source_type": "web_mock",
            },
            {
                "url": f"https://stackoverflow.com/questions/tagged/{query.replace(' ', '+')}",
                "title": f"Common Questions about {query}",
                "content": f"Community-driven discussion of practical challenges when working with {query}. "
                f"Includes real-world examples and solutions from experienced practitioners.",
                "source_type": "web_mock",
            },
        ]

    async def search_wikipedia(self, query: str) -> List[Dict[str, Any]]:
        """Mock Wikipedia search results."""
        return [
            {
                "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                "title": f"Wikipedia: {query}",
                "content": f"{query} refers to a methodology and set of practices in software development. "
                f"It encompasses various approaches and techniques that have evolved over time to "
                f"address complexity in modern software systems. The concept has gained widespread "
                f"adoption in enterprise and startup environments alike.",
                "page": query.replace(" ", "_"),
                "source_type": "wikipedia_mock",
            }
        ]

    async def generate_interview_question(
        self, analyst: Analyst, messages: List[Dict[str, Any]]
    ) -> str:
        """Generate mock interview questions."""
        questions = [
            f"Hello, I'm {analyst.name}, and I work as a {analyst.role} at {analyst.affiliation}. "
            f"I'm researching the practical applications of this topic. Could you share some specific "
            f"examples of how you've seen these concepts implemented successfully?",
            f"That's interesting! Can you elaborate on any particular challenges you've encountered "
            f"when implementing these approaches? What strategies have you found most effective for "
            f"overcoming those obstacles?",
            f"Thank you so much for your help! This has been incredibly insightful.",
        ]

        # Cycle through questions based on conversation length
        question_index = min(len(messages) // 2, len(questions) - 1)
        return questions[question_index]

    async def generate_expert_answer(
        self, analyst: Analyst, messages: List[Dict[str, Any]], context: str
    ) -> str:
        """Generate mock expert answers."""
        answers = [
            f"Thank you for the question! Based on my experience, I've found that the key to successful "
            f"implementation lies in understanding the specific context and requirements of your project. "
            f"The approaches mentioned in the research literature [1] often need to be adapted to fit "
            f"real-world constraints and organizational needs.\n\n"
            f"[1] {context[:100]}..."
            if context
            else "Mock research source",
            f"Great follow-up question! The main challenges I've encountered typically fall into three "
            f"categories: technical complexity, team coordination, and stakeholder alignment. "
            f"For technical complexity, we've found that starting with simpler implementations and "
            f"gradually increasing sophistication tends to work well. The documentation suggests [1] "
            f"similar phased approaches.\n\n"
            f"[1] Technical implementation guide",
            f"You're very welcome! I'm always happy to share experiences with fellow practitioners. "
            f"Feel free to reach out if you have more questions as your research progresses.",
        ]

        # Select answer based on conversation progress
        answer_index = min(
            len([m for m in messages if m.get("name") == "expert"]), len(answers) - 1
        )
        return answers[answer_index]

    async def write_research_section(self, analyst: Analyst, context: str) -> str:
        """Generate mock research sections."""
        return f"""## {analyst.role} Perspective on Modern Implementation Approaches

### Summary

Based on extensive analysis of current practices and industry feedback, several key insights emerge regarding the implementation of these methodologies in contemporary software development environments. The {analyst.role} perspective reveals particularly interesting patterns around scalability and maintainability considerations.

From a {analyst.affiliation} standpoint, the most surprising finding is the significant impact that organizational culture has on technical implementation success [1]. Traditional approaches often underestimate the human factors involved in adopting new methodologies, leading to suboptimal outcomes even when the technical implementation is sound.

The research indicates that successful implementations typically follow a phased approach, beginning with pilot projects and gradually expanding to larger systems [1]. This finding challenges the conventional wisdom that suggests full-scale adoption from the start is more efficient.

### Sources

[1] {context[:200] if context else "Mock interview transcript and supporting research documents"}...
"""

    def format_documents_for_context(self, results: List[Dict[str, Any]]) -> str:
        """Format mock search results for context."""
        if not results:
            return "No search results available for this query."

        formatted_docs = []
        for doc in results:
            doc_text = f'<Document href="{doc.get("url", "")}">\n{doc.get("content", "")}\n</Document>'
            formatted_docs.append(doc_text)

        return "\n\n---\n\n".join(formatted_docs)

    def get_service_info(self) -> Dict[str, Any]:
        """Get mock service information."""
        return {
            "service_name": "Mock Research Service",
            "is_available": True,
            "using_mock": True,
            "capabilities": [
                "analyst_creation",
                "web_search",
                "wikipedia_search",
                "interview_questions",
                "expert_answers",
                "section_writing",
            ],
        }
