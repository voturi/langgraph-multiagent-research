"""Research domain service for managing research projects."""

from datetime import datetime
from typing import List, Optional

from ..entities.research import (
    Analyst,
    Interview,
    ResearchProject,
    ResearchSection,
    ResearchTopic,
)
from ..interfaces.events import EventPublisher


class ResearchService:
    """Domain service for research project management."""

    def __init__(self, event_publisher: EventPublisher):
        self._event_publisher = event_publisher

    async def create_research_project(
        self, topic: str, max_analysts: int = 3
    ) -> ResearchProject:
        """Create a new research project."""
        project = ResearchProject(topic=topic, status="created")

        # Publish domain event
        # await self._event_publisher.publish(
        #     ResearchProjectCreatedEvent(project_id=project.id, topic=topic)
        # )

        return project

    def update_project_status(
        self, project: ResearchProject, status: str
    ) -> ResearchProject:
        """Update the status of a research project."""
        project.status = status

        if status == "completed":
            project.completed_at = datetime.utcnow()

        return project

    def add_analysts_to_project(
        self, project: ResearchProject, analysts: List[Analyst]
    ) -> ResearchProject:
        """Add analysts to a research project."""
        project.analysts.extend(analysts)
        return project

    def add_interview_to_project(
        self, project: ResearchProject, interview: Interview
    ) -> ResearchProject:
        """Add an interview to a research project."""
        project.interviews.append(interview)
        return project

    def add_section_to_project(
        self, project: ResearchProject, section: ResearchSection
    ) -> ResearchProject:
        """Add a research section to a project."""
        project.sections.append(section)
        return project

    def get_project_progress(self, project: ResearchProject) -> dict:
        """Get progress information about a research project."""
        return {
            "total_analysts": len(project.analysts),
            "completed_interviews": len(
                [i for i in project.interviews if i.completed_at]
            ),
            "pending_interviews": len(
                [i for i in project.interviews if not i.completed_at]
            ),
            "sections_written": len(project.sections),
            "status": project.status,
        }

    def is_project_complete(self, project: ResearchProject) -> bool:
        """Check if a research project is complete."""
        if not project.analysts:
            return False

        # All analysts should have completed interviews
        completed_interviews = len([i for i in project.interviews if i.completed_at])
        expected_interviews = len(project.analysts)

        # All interviews should have corresponding sections
        sections_count = len(project.sections)

        return (
            completed_interviews == expected_interviews
            and sections_count == expected_interviews
            and project.status == "completed"
        )
