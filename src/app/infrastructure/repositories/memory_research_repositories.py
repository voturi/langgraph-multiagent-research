"""In-memory implementations of research repositories."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...domain.entities.research import (
    Analyst,
    Interview,
    ResearchProject,
    ResearchSection,
    ResearchTopic,
)
from ...domain.interfaces.research_repositories import (
    AnalystRepository,
    InterviewRepository,
    ResearchProjectRepository,
    ResearchSectionRepository,
    ResearchTopicRepository,
)

logger = logging.getLogger(__name__)


class MemoryResearchProjectRepository(ResearchProjectRepository):
    """In-memory implementation of research project repository."""

    def __init__(self):
        self._projects: Dict[str, ResearchProject] = {}
        logger.debug("Memory research project repository initialized")

    async def create(self, project: ResearchProject) -> ResearchProject:
        """Create a new research project."""
        self._projects[project.id] = project
        logger.debug(f"Created research project: {project.id}")
        return project

    async def get_by_id(self, project_id: str) -> Optional[ResearchProject]:
        """Get a research project by ID."""
        return self._projects.get(project_id)

    async def get_by_topic(self, topic: str) -> List[ResearchProject]:
        """Get research projects by topic."""
        return [
            project
            for project in self._projects.values()
            if topic.lower() in project.topic.lower()
        ]

    async def update(self, project: ResearchProject) -> ResearchProject:
        """Update a research project."""
        if project.id in self._projects:
            self._projects[project.id] = project
            logger.debug(f"Updated research project: {project.id}")
        return project

    async def delete(self, project_id: str) -> bool:
        """Delete a research project."""
        if project_id in self._projects:
            del self._projects[project_id]
            logger.debug(f"Deleted research project: {project_id}")
            return True
        return False

    async def list_all(self) -> List[ResearchProject]:
        """List all research projects."""
        return list(self._projects.values())

    async def get_by_status(self, status: str) -> List[ResearchProject]:
        """Get research projects by status."""
        return [
            project for project in self._projects.values() if project.status == status
        ]


class MemoryAnalystRepository(AnalystRepository):
    """In-memory implementation of analyst repository."""

    def __init__(self):
        self._analysts: Dict[str, Analyst] = {}
        self._project_analysts: Dict[str, List[str]] = {}  # project_id -> [analyst_ids]
        logger.debug("Memory analyst repository initialized")

    async def create(self, analyst: Analyst) -> Analyst:
        """Create a new analyst."""
        self._analysts[analyst.id] = analyst
        logger.debug(f"Created analyst: {analyst.id}")
        return analyst

    async def get_by_id(self, analyst_id: str) -> Optional[Analyst]:
        """Get an analyst by ID."""
        return self._analysts.get(analyst_id)

    async def get_by_project_id(self, project_id: str) -> List[Analyst]:
        """Get analysts associated with a project."""
        analyst_ids = self._project_analysts.get(project_id, [])
        return [
            self._analysts[analyst_id]
            for analyst_id in analyst_ids
            if analyst_id in self._analysts
        ]

    async def update(self, analyst: Analyst) -> Analyst:
        """Update an analyst."""
        if analyst.id in self._analysts:
            self._analysts[analyst.id] = analyst
            logger.debug(f"Updated analyst: {analyst.id}")
        return analyst

    async def delete(self, analyst_id: str) -> bool:
        """Delete an analyst."""
        if analyst_id in self._analysts:
            del self._analysts[analyst_id]
            # Remove from project associations
            for project_id, analyst_ids in self._project_analysts.items():
                if analyst_id in analyst_ids:
                    analyst_ids.remove(analyst_id)
            logger.debug(f"Deleted analyst: {analyst_id}")
            return True
        return False

    async def list_all(self) -> List[Analyst]:
        """List all analysts."""
        return list(self._analysts.values())

    async def get_by_role(self, role: str) -> List[Analyst]:
        """Get analysts by role."""
        return [
            analyst
            for analyst in self._analysts.values()
            if role.lower() in analyst.role.lower()
        ]

    async def get_by_affiliation(self, affiliation: str) -> List[Analyst]:
        """Get analysts by affiliation."""
        return [
            analyst
            for analyst in self._analysts.values()
            if affiliation.lower() in analyst.affiliation.lower()
        ]

    def associate_with_project(self, project_id: str, analyst_id: str):
        """Associate an analyst with a project."""
        if project_id not in self._project_analysts:
            self._project_analysts[project_id] = []
        if analyst_id not in self._project_analysts[project_id]:
            self._project_analysts[project_id].append(analyst_id)


class MemoryInterviewRepository(InterviewRepository):
    """In-memory implementation of interview repository."""

    def __init__(self):
        self._interviews: Dict[str, Interview] = {}
        self._analyst_interviews: Dict[
            str, List[str]
        ] = {}  # analyst_id -> [interview_ids]
        self._project_interviews: Dict[
            str, List[str]
        ] = {}  # project_id -> [interview_ids]
        logger.debug("Memory interview repository initialized")

    async def create(self, interview: Interview) -> Interview:
        """Create a new interview."""
        self._interviews[interview.id] = interview

        # Associate with analyst
        if interview.analyst_id not in self._analyst_interviews:
            self._analyst_interviews[interview.analyst_id] = []
        self._analyst_interviews[interview.analyst_id].append(interview.id)

        logger.debug(f"Created interview: {interview.id}")
        return interview

    async def get_by_id(self, interview_id: str) -> Optional[Interview]:
        """Get an interview by ID."""
        return self._interviews.get(interview_id)

    async def get_by_analyst_id(self, analyst_id: str) -> List[Interview]:
        """Get interviews by analyst ID."""
        interview_ids = self._analyst_interviews.get(analyst_id, [])
        return [
            self._interviews[interview_id]
            for interview_id in interview_ids
            if interview_id in self._interviews
        ]

    async def get_by_project_id(self, project_id: str) -> List[Interview]:
        """Get interviews associated with a project."""
        interview_ids = self._project_interviews.get(project_id, [])
        return [
            self._interviews[interview_id]
            for interview_id in interview_ids
            if interview_id in self._interviews
        ]

    async def update(self, interview: Interview) -> Interview:
        """Update an interview."""
        if interview.id in self._interviews:
            self._interviews[interview.id] = interview
            logger.debug(f"Updated interview: {interview.id}")
        return interview

    async def delete(self, interview_id: str) -> bool:
        """Delete an interview."""
        if interview_id in self._interviews:
            interview = self._interviews[interview_id]
            del self._interviews[interview_id]

            # Remove from analyst associations
            if interview.analyst_id in self._analyst_interviews:
                if interview_id in self._analyst_interviews[interview.analyst_id]:
                    self._analyst_interviews[interview.analyst_id].remove(interview_id)

            # Remove from project associations
            for project_id, interview_ids in self._project_interviews.items():
                if interview_id in interview_ids:
                    interview_ids.remove(interview_id)

            logger.debug(f"Deleted interview: {interview_id}")
            return True
        return False

    async def list_all(self) -> List[Interview]:
        """List all interviews."""
        return list(self._interviews.values())

    async def get_completed_interviews(self) -> List[Interview]:
        """Get all completed interviews."""
        return [
            interview
            for interview in self._interviews.values()
            if interview.completed_at is not None
        ]

    async def get_pending_interviews(self) -> List[Interview]:
        """Get all pending interviews."""
        return [
            interview
            for interview in self._interviews.values()
            if interview.completed_at is None
        ]

    def associate_with_project(self, project_id: str, interview_id: str):
        """Associate an interview with a project."""
        if project_id not in self._project_interviews:
            self._project_interviews[project_id] = []
        if interview_id not in self._project_interviews[project_id]:
            self._project_interviews[project_id].append(interview_id)


class MemoryResearchSectionRepository(ResearchSectionRepository):
    """In-memory implementation of research section repository."""

    def __init__(self):
        self._sections: Dict[str, ResearchSection] = {}
        self._interview_sections: Dict[
            str, List[str]
        ] = {}  # interview_id -> [section_ids]
        self._analyst_sections: Dict[str, List[str]] = {}  # analyst_id -> [section_ids]
        self._project_sections: Dict[str, List[str]] = {}  # project_id -> [section_ids]
        logger.debug("Memory research section repository initialized")

    async def create(self, section: ResearchSection) -> ResearchSection:
        """Create a new research section."""
        self._sections[section.id] = section

        # Associate with interview
        if section.interview_id not in self._interview_sections:
            self._interview_sections[section.interview_id] = []
        self._interview_sections[section.interview_id].append(section.id)

        # Associate with analyst
        if section.analyst_id not in self._analyst_sections:
            self._analyst_sections[section.analyst_id] = []
        self._analyst_sections[section.analyst_id].append(section.id)

        logger.debug(f"Created research section: {section.id}")
        return section

    async def get_by_id(self, section_id: str) -> Optional[ResearchSection]:
        """Get a research section by ID."""
        return self._sections.get(section_id)

    async def get_by_interview_id(self, interview_id: str) -> List[ResearchSection]:
        """Get research sections by interview ID."""
        section_ids = self._interview_sections.get(interview_id, [])
        return [
            self._sections[section_id]
            for section_id in section_ids
            if section_id in self._sections
        ]

    async def get_by_analyst_id(self, analyst_id: str) -> List[ResearchSection]:
        """Get research sections by analyst ID."""
        section_ids = self._analyst_sections.get(analyst_id, [])
        return [
            self._sections[section_id]
            for section_id in section_ids
            if section_id in self._sections
        ]

    async def get_by_project_id(self, project_id: str) -> List[ResearchSection]:
        """Get research sections associated with a project."""
        section_ids = self._project_sections.get(project_id, [])
        return [
            self._sections[section_id]
            for section_id in section_ids
            if section_id in self._sections
        ]

    async def update(self, section: ResearchSection) -> ResearchSection:
        """Update a research section."""
        if section.id in self._sections:
            self._sections[section.id] = section
            logger.debug(f"Updated research section: {section.id}")
        return section

    async def delete(self, section_id: str) -> bool:
        """Delete a research section."""
        if section_id in self._sections:
            section = self._sections[section_id]
            del self._sections[section_id]

            # Remove from associations
            if section.interview_id in self._interview_sections:
                if section_id in self._interview_sections[section.interview_id]:
                    self._interview_sections[section.interview_id].remove(section_id)

            if section.analyst_id in self._analyst_sections:
                if section_id in self._analyst_sections[section.analyst_id]:
                    self._analyst_sections[section.analyst_id].remove(section_id)

            for project_id, section_ids in self._project_sections.items():
                if section_id in section_ids:
                    section_ids.remove(section_id)

            logger.debug(f"Deleted research section: {section_id}")
            return True
        return False

    async def list_all(self) -> List[ResearchSection]:
        """List all research sections."""
        return list(self._sections.values())

    def associate_with_project(self, project_id: str, section_id: str):
        """Associate a section with a project."""
        if project_id not in self._project_sections:
            self._project_sections[project_id] = []
        if section_id not in self._project_sections[project_id]:
            self._project_sections[project_id].append(section_id)


class MemoryResearchTopicRepository(ResearchTopicRepository):
    """In-memory implementation of research topic repository."""

    def __init__(self):
        self._topics: Dict[str, ResearchTopic] = {}
        logger.debug("Memory research topic repository initialized")

    async def create(self, topic: ResearchTopic) -> ResearchTopic:
        """Create a new research topic."""
        self._topics[topic.id] = topic
        logger.debug(f"Created research topic: {topic.id}")
        return topic

    async def get_by_id(self, topic_id: str) -> Optional[ResearchTopic]:
        """Get a research topic by ID."""
        return self._topics.get(topic_id)

    async def get_by_topic_text(self, topic: str) -> List[ResearchTopic]:
        """Get research topics by topic text."""
        return [
            research_topic
            for research_topic in self._topics.values()
            if topic.lower() in research_topic.topic.lower()
        ]

    async def update(self, topic: ResearchTopic) -> ResearchTopic:
        """Update a research topic."""
        if topic.id in self._topics:
            self._topics[topic.id] = topic
            logger.debug(f"Updated research topic: {topic.id}")
        return topic

    async def delete(self, topic_id: str) -> bool:
        """Delete a research topic."""
        if topic_id in self._topics:
            del self._topics[topic_id]
            logger.debug(f"Deleted research topic: {topic_id}")
            return True
        return False

    async def list_all(self) -> List[ResearchTopic]:
        """List all research topics."""
        return list(self._topics.values())
