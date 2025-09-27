"""Research Unit of Work implementation."""

import logging
from typing import Optional

from ...domain.interfaces.repositories import UnitOfWork
from ...domain.interfaces.research_repositories import (
    AnalystRepository,
    InterviewRepository,
    ResearchProjectRepository,
    ResearchSectionRepository,
    ResearchTopicRepository,
)
from .memory_research_repositories import (
    MemoryAnalystRepository,
    MemoryInterviewRepository,
    MemoryResearchProjectRepository,
    MemoryResearchSectionRepository,
    MemoryResearchTopicRepository,
)

logger = logging.getLogger(__name__)


class ResearchUnitOfWork(UnitOfWork):
    """Unit of Work implementation for research repositories."""

    def __init__(self):
        # Research-specific repositories
        self._research_projects: Optional[ResearchProjectRepository] = None
        self._analysts: Optional[AnalystRepository] = None
        self._interviews: Optional[InterviewRepository] = None
        self._research_sections: Optional[ResearchSectionRepository] = None
        self._research_topics: Optional[ResearchTopicRepository] = None

        # Base UnitOfWork repositories (using research implementations as placeholders)
        self._users = None
        self._conversations = None
        self._messages = None
        self._tasks = None
        self._workflows = None

        logger.debug("Research Unit of Work initialized")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    @property
    def research_projects(self) -> ResearchProjectRepository:
        """Get research projects repository."""
        if self._research_projects is None:
            self._research_projects = MemoryResearchProjectRepository()
        return self._research_projects

    @property
    def analysts(self) -> AnalystRepository:
        """Get analysts repository."""
        if self._analysts is None:
            self._analysts = MemoryAnalystRepository()
        return self._analysts

    @property
    def interviews(self) -> InterviewRepository:
        """Get interviews repository."""
        if self._interviews is None:
            self._interviews = MemoryInterviewRepository()
        return self._interviews

    @property
    def research_sections(self) -> ResearchSectionRepository:
        """Get research sections repository."""
        if self._research_sections is None:
            self._research_sections = MemoryResearchSectionRepository()
        return self._research_sections

    @property
    def research_topics(self) -> ResearchTopicRepository:
        """Get research topics repository."""
        if self._research_topics is None:
            self._research_topics = MemoryResearchTopicRepository()
        return self._research_topics

    # Base UnitOfWork interface implementation (placeholders for research context)
    @property
    def users(self):
        """Users repository (not used in research context)."""
        if self._users is None:
            from ..memory_repositories import MemoryUserRepository

            self._users = MemoryUserRepository()
        return self._users

    @property
    def conversations(self):
        """Conversations repository (not used in research context)."""
        if self._conversations is None:
            from ..memory_repositories import MemoryConversationRepository

            self._conversations = MemoryConversationRepository()
        return self._conversations

    @property
    def messages(self):
        """Messages repository (not used in research context)."""
        if self._messages is None:
            from ..memory_repositories import MemoryMessageRepository

            self._messages = MemoryMessageRepository()
        return self._messages

    @property
    def tasks(self):
        """Tasks repository (not used in research context)."""
        if self._tasks is None:
            from ..memory_repositories import MemoryTaskRepository

            self._tasks = MemoryTaskRepository()
        return self._tasks

    @property
    def workflows(self):
        """Workflows repository (not used in research context)."""
        if self._workflows is None:
            from ..memory_repositories import MemoryWorkflowRepository

            self._workflows = MemoryWorkflowRepository()
        return self._workflows

    async def commit(self):
        """Commit the current transaction."""
        # For memory repositories, this is a no-op
        # In a real database implementation, this would commit the transaction
        logger.debug("Research UoW commit completed")

    async def rollback(self):
        """Rollback the current transaction."""
        # For memory repositories, this is a no-op
        # In a real database implementation, this would rollback the transaction
        logger.debug("Research UoW rollback completed")

    def create_project_associations(
        self,
        project_id: str,
        analyst_ids: list = None,
        interview_ids: list = None,
        section_ids: list = None,
    ):
        """Create associations between project and related entities."""
        # Associate analysts with project
        if analyst_ids:
            analyst_repo = self._analysts
            if isinstance(analyst_repo, MemoryAnalystRepository):
                for analyst_id in analyst_ids:
                    analyst_repo.associate_with_project(project_id, analyst_id)

        # Associate interviews with project
        if interview_ids:
            interview_repo = self._interviews
            if isinstance(interview_repo, MemoryInterviewRepository):
                for interview_id in interview_ids:
                    interview_repo.associate_with_project(project_id, interview_id)

        # Associate sections with project
        if section_ids:
            section_repo = self._research_sections
            if isinstance(section_repo, MemoryResearchSectionRepository):
                for section_id in section_ids:
                    section_repo.associate_with_project(project_id, section_id)

        logger.debug(f"Created project associations for project: {project_id}")
