"""Interview domain service for managing interview processes."""

from datetime import datetime
from typing import List, Optional

from ..entities.research import Analyst, Interview, ResearchSection, SearchQuery
from ..interfaces.events import EventPublisher


class InterviewService:
    """Domain service for interview management."""

    def __init__(self, event_publisher: EventPublisher):
        self._event_publisher = event_publisher

    def create_interview(
        self, analyst: Analyst, topic: str, max_turns: int = 2
    ) -> Interview:
        """Create a new interview session."""
        interview = Interview(
            analyst_id=analyst.id, topic=topic, transcript="", max_turns=max_turns
        )

        return interview

    def is_interview_complete(self, interview: Interview) -> bool:
        """Check if an interview is complete."""
        return interview.completed_at is not None

    def complete_interview(self, interview: Interview) -> Interview:
        """Mark an interview as completed."""
        interview.completed_at = datetime.utcnow()
        return interview

    def add_context_to_interview(
        self, interview: Interview, context_documents: List[str]
    ) -> Interview:
        """Add context documents to an interview."""
        interview.context_documents.extend(context_documents)
        return interview

    def update_interview_transcript(
        self, interview: Interview, transcript: str
    ) -> Interview:
        """Update the interview transcript."""
        interview.transcript = transcript
        return interview

    def should_continue_interview(
        self, messages: List[dict], max_turns: int, expert_name: str = "expert"
    ) -> bool:
        """Determine if interview should continue based on conversation state."""
        # Count expert responses
        expert_responses = [msg for msg in messages if msg.get("name") == expert_name]

        # End if max turns reached
        if len(expert_responses) >= max_turns:
            return False

        # Check if interview was concluded by analyst
        if len(messages) >= 2:
            last_question = messages[-2].get("content", "")
            if "Thank you so much for your help" in last_question:
                return False

        return True

    def extract_search_context(self, messages: List[dict]) -> str:
        """Extract context for search query generation from messages."""
        if not messages:
            return ""

        # Get the last analyst question for context
        analyst_messages = [msg for msg in messages if msg.get("name") != "expert"]

        if analyst_messages:
            return analyst_messages[-1].get("content", "")

        return ""

    def validate_interview_progression(
        self, interview: Interview, messages: List[dict]
    ) -> bool:
        """Validate that interview is progressing properly."""
        if not messages:
            return False

        # Should have alternating analyst and expert messages
        analyst_count = len([m for m in messages if m.get("name") != "expert"])
        expert_count = len([m for m in messages if m.get("name") == "expert"])

        # Analyst should have one more message than expert (starts conversation)
        return analyst_count == expert_count + 1 or analyst_count == expert_count

    def get_interview_summary(self, interview: Interview) -> dict:
        """Get a summary of interview status."""
        return {
            "id": interview.id,
            "analyst_id": interview.analyst_id,
            "topic": interview.topic,
            "is_complete": self.is_interview_complete(interview),
            "has_context": len(interview.context_documents) > 0,
            "has_transcript": bool(interview.transcript),
            "max_turns": interview.max_turns,
        }


class SectionService:
    """Domain service for research section management."""

    def __init__(self, event_publisher: EventPublisher):
        self._event_publisher = event_publisher

    def create_section(
        self,
        interview: Interview,
        analyst: Analyst,
        title: str,
        content: str,
        sources: List[str],
    ) -> ResearchSection:
        """Create a research section from interview data."""
        section = ResearchSection(
            interview_id=interview.id,
            analyst_id=analyst.id,
            title=title,
            content=content,
            sources=sources,
        )

        return section

    def extract_sources_from_content(self, content: str) -> List[str]:
        """Extract source citations from content."""
        import re

        # Look for markdown links and citations
        # Pattern for [1] Source name, [2] Another source, etc.
        source_pattern = r"\[(\d+)\]\s*([^\n\[]+)"
        matches = re.findall(source_pattern, content)

        return [match[1].strip() for match in matches]

    def validate_section_content(self, content: str) -> bool:
        """Validate that section content meets quality standards."""
        if not content or len(content.strip()) < 100:  # Minimum length
            return False

        # Should contain markdown headers
        if not any(line.startswith("#") for line in content.split("\n")):
            return False

        return True

    def generate_section_title(self, analyst: Analyst, topic: str) -> str:
        """Generate a section title based on analyst focus and topic."""
        # Use analyst role/description to create relevant title
        if analyst.role:
            return f"{analyst.role} Perspective on {topic}"
        return f"{analyst.name}'s Analysis of {topic}"
