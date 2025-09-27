"""Analyst domain service for creating and managing AI analyst personas."""

from typing import List, Optional

from ..entities.research import Analyst, Perspectives, ResearchTopic
from ..interfaces.events import EventPublisher


class AnalystService:
    """Domain service for analyst persona management."""

    def __init__(self, event_publisher: EventPublisher):
        self._event_publisher = event_publisher

    def validate_analyst_requirements(self, topic: str, max_analysts: int = 3) -> bool:
        """Validate the requirements for creating analysts."""
        if not topic or topic.strip() == "":
            return False

        if max_analysts <= 0 or max_analysts > 10:  # Reasonable upper limit
            return False

        return True

    def prepare_analyst_creation_context(
        self, topic: str, human_feedback: Optional[str] = None, max_analysts: int = 3
    ) -> dict:
        """Prepare context for analyst creation."""
        return {
            "topic": topic,
            "human_analyst_feedback": human_feedback or "",
            "max_analysts": max_analysts,
        }

    def validate_analyst_personas(self, analysts: List[Analyst]) -> bool:
        """Validate that analyst personas are properly formed."""
        if not analysts:
            return False

        for analyst in analysts:
            # Check required fields are not empty
            if not all(
                [
                    analyst.name.strip(),
                    analyst.role.strip(),
                    analyst.affiliation.strip(),
                    analyst.description.strip(),
                ]
            ):
                return False

            # Check for reasonable length limits
            if len(analyst.description) < 10:  # Too short
                return False

        # Check for diversity (no duplicate names)
        names = [a.name for a in analysts]
        if len(names) != len(set(names)):
            return False

        return True

    def get_analyst_by_id(
        self, analysts: List[Analyst], analyst_id: str
    ) -> Optional[Analyst]:
        """Find an analyst by ID from a list."""
        return next((a for a in analysts if a.id == analyst_id), None)

    def get_analyst_specializations(self, analysts: List[Analyst]) -> List[str]:
        """Extract unique specializations/roles from analysts."""
        return list(set(analyst.role for analyst in analysts))

    def get_analyst_affiliations(self, analysts: List[Analyst]) -> List[str]:
        """Extract unique affiliations from analysts."""
        return list(set(analyst.affiliation for analyst in analysts))

    async def create_research_topic(
        self, topic: str, max_analysts: int = 3, human_feedback: Optional[str] = None
    ) -> ResearchTopic:
        """Create a research topic entity."""
        if not self.validate_analyst_requirements(topic, max_analysts):
            raise ValueError("Invalid analyst requirements")

        research_topic = ResearchTopic(
            topic=topic, max_analysts=max_analysts, human_feedback=human_feedback
        )

        # Publish domain event
        # await self._event_publisher.publish(
        #     ResearchTopicCreatedEvent(topic_id=research_topic.id, topic=topic)
        # )

        return research_topic

    def should_recreate_analysts(
        self, current_analysts: List[Analyst], human_feedback: Optional[str]
    ) -> bool:
        """Determine if analysts should be recreated based on human feedback."""
        # If there's new human feedback, recreate analysts
        if human_feedback and human_feedback.strip():
            return True

        # If no analysts exist, need to create them
        if not current_analysts:
            return True

        return False
