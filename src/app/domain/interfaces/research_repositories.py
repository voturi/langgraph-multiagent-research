"""Repository interfaces for research domain entities."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.research import (
    Analyst,
    Interview,
    ResearchProject,
    ResearchSection,
    ResearchTopic,
)


class ResearchProjectRepository(ABC):
    """Repository interface for research projects."""

    @abstractmethod
    async def create(self, project: ResearchProject) -> ResearchProject:
        """Create a new research project."""
        pass

    @abstractmethod
    async def get_by_id(self, project_id: str) -> Optional[ResearchProject]:
        """Get a research project by ID."""
        pass

    @abstractmethod
    async def get_by_topic(self, topic: str) -> List[ResearchProject]:
        """Get research projects by topic."""
        pass

    @abstractmethod
    async def update(self, project: ResearchProject) -> ResearchProject:
        """Update a research project."""
        pass

    @abstractmethod
    async def delete(self, project_id: str) -> bool:
        """Delete a research project."""
        pass

    @abstractmethod
    async def list_all(self) -> List[ResearchProject]:
        """List all research projects."""
        pass

    @abstractmethod
    async def get_by_status(self, status: str) -> List[ResearchProject]:
        """Get research projects by status."""
        pass


class AnalystRepository(ABC):
    """Repository interface for analysts."""

    @abstractmethod
    async def create(self, analyst: Analyst) -> Analyst:
        """Create a new analyst."""
        pass

    @abstractmethod
    async def get_by_id(self, analyst_id: str) -> Optional[Analyst]:
        """Get an analyst by ID."""
        pass

    @abstractmethod
    async def get_by_project_id(self, project_id: str) -> List[Analyst]:
        """Get analysts associated with a project."""
        pass

    @abstractmethod
    async def update(self, analyst: Analyst) -> Analyst:
        """Update an analyst."""
        pass

    @abstractmethod
    async def delete(self, analyst_id: str) -> bool:
        """Delete an analyst."""
        pass

    @abstractmethod
    async def list_all(self) -> List[Analyst]:
        """List all analysts."""
        pass

    @abstractmethod
    async def get_by_role(self, role: str) -> List[Analyst]:
        """Get analysts by role."""
        pass

    @abstractmethod
    async def get_by_affiliation(self, affiliation: str) -> List[Analyst]:
        """Get analysts by affiliation."""
        pass


class InterviewRepository(ABC):
    """Repository interface for interviews."""

    @abstractmethod
    async def create(self, interview: Interview) -> Interview:
        """Create a new interview."""
        pass

    @abstractmethod
    async def get_by_id(self, interview_id: str) -> Optional[Interview]:
        """Get an interview by ID."""
        pass

    @abstractmethod
    async def get_by_analyst_id(self, analyst_id: str) -> List[Interview]:
        """Get interviews by analyst ID."""
        pass

    @abstractmethod
    async def get_by_project_id(self, project_id: str) -> List[Interview]:
        """Get interviews associated with a project."""
        pass

    @abstractmethod
    async def update(self, interview: Interview) -> Interview:
        """Update an interview."""
        pass

    @abstractmethod
    async def delete(self, interview_id: str) -> bool:
        """Delete an interview."""
        pass

    @abstractmethod
    async def list_all(self) -> List[Interview]:
        """List all interviews."""
        pass

    @abstractmethod
    async def get_completed_interviews(self) -> List[Interview]:
        """Get all completed interviews."""
        pass

    @abstractmethod
    async def get_pending_interviews(self) -> List[Interview]:
        """Get all pending interviews."""
        pass


class ResearchSectionRepository(ABC):
    """Repository interface for research sections."""

    @abstractmethod
    async def create(self, section: ResearchSection) -> ResearchSection:
        """Create a new research section."""
        pass

    @abstractmethod
    async def get_by_id(self, section_id: str) -> Optional[ResearchSection]:
        """Get a research section by ID."""
        pass

    @abstractmethod
    async def get_by_interview_id(self, interview_id: str) -> List[ResearchSection]:
        """Get research sections by interview ID."""
        pass

    @abstractmethod
    async def get_by_analyst_id(self, analyst_id: str) -> List[ResearchSection]:
        """Get research sections by analyst ID."""
        pass

    @abstractmethod
    async def get_by_project_id(self, project_id: str) -> List[ResearchSection]:
        """Get research sections associated with a project."""
        pass

    @abstractmethod
    async def update(self, section: ResearchSection) -> ResearchSection:
        """Update a research section."""
        pass

    @abstractmethod
    async def delete(self, section_id: str) -> bool:
        """Delete a research section."""
        pass

    @abstractmethod
    async def list_all(self) -> List[ResearchSection]:
        """List all research sections."""
        pass


class ResearchTopicRepository(ABC):
    """Repository interface for research topics."""

    @abstractmethod
    async def create(self, topic: ResearchTopic) -> ResearchTopic:
        """Create a new research topic."""
        pass

    @abstractmethod
    async def get_by_id(self, topic_id: str) -> Optional[ResearchTopic]:
        """Get a research topic by ID."""
        pass

    @abstractmethod
    async def get_by_topic_text(self, topic: str) -> List[ResearchTopic]:
        """Get research topics by topic text."""
        pass

    @abstractmethod
    async def update(self, topic: ResearchTopic) -> ResearchTopic:
        """Update a research topic."""
        pass

    @abstractmethod
    async def delete(self, topic_id: str) -> bool:
        """Delete a research topic."""
        pass

    @abstractmethod
    async def list_all(self) -> List[ResearchTopic]:
        """List all research topics."""
        pass
