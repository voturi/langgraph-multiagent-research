"""Research workflow orchestrating the complete research assistant process."""

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
from ...domain.interfaces.events import EventPublisher
from ...domain.services.analyst_service import AnalystService
from ...domain.services.interview_service import InterviewService, SectionService
from ...domain.services.research_service import ResearchService
from ...infrastructure.repositories.research_unit_of_work import ResearchUnitOfWork
from ...infrastructure.services.mock_research_service import MockResearchService
from ...infrastructure.services.research_llm_service import ResearchLLMService
from ...infrastructure.services.tavily_service import TavilySearchService
from ...infrastructure.services.wikipedia_service import WikipediaSearchService

logger = logging.getLogger(__name__)


class ResearchWorkflow:
    """Main workflow orchestrating the research assistant process."""

    def __init__(
        self,
        research_service: ResearchService,
        analyst_service: AnalystService,
        interview_service: InterviewService,
        section_service: SectionService,
        uow: ResearchUnitOfWork,
        event_publisher: EventPublisher,
        llm_service: Optional[ResearchLLMService] = None,
        tavily_service: Optional[TavilySearchService] = None,
        wikipedia_service: Optional[WikipediaSearchService] = None,
        mock_service: Optional[MockResearchService] = None,
        use_mock: bool = False,
    ):
        self.research_service = research_service
        self.analyst_service = analyst_service
        self.interview_service = interview_service
        self.section_service = section_service
        self.uow = uow
        self.event_publisher = event_publisher

        # External services
        self.llm_service = llm_service
        self.tavily_service = tavily_service
        self.wikipedia_service = wikipedia_service
        self.mock_service = mock_service
        self.use_mock = use_mock

        logger.info(f"Research workflow initialized (using_mock={use_mock})")

    async def create_research_project(
        self, topic: str, max_analysts: int = 3
    ) -> ResearchProject:
        """Create a new research project and initialize it."""
        async with self.uow:
            # Create the project
            project = await self.research_service.create_research_project(
                topic, max_analysts
            )
            project = await self.uow.research_projects.create(project)

            # Create research topic entity
            research_topic = await self.analyst_service.create_research_topic(
                topic, max_analysts
            )
            await self.uow.research_topics.create(research_topic)

            logger.info(f"Created research project: {project.id} for topic: {topic}")
            return project

    async def generate_analysts(
        self,
        project_id: str,
        topic: str,
        max_analysts: int = 3,
        human_feedback: Optional[str] = None,
    ) -> List[Analyst]:
        """Generate AI analyst personas for the research project."""
        try:
            async with self.uow:
                project = await self.uow.research_projects.get_by_id(project_id)
                if not project:
                    raise ValueError(f"Project not found: {project_id}")

                # Generate analysts using LLM or mock service
                if self.use_mock and self.mock_service:
                    analysts = await self.mock_service.create_analysts(
                        topic, max_analysts, human_feedback
                    )
                elif self.llm_service:
                    analysts = await self.llm_service.create_analysts(
                        topic, max_analysts, human_feedback
                    )
                else:
                    raise ValueError("No analyst generation service available")

                # Validate analysts
                if not self.analyst_service.validate_analyst_personas(analysts):
                    raise ValueError("Generated analysts failed validation")

                # Store analysts
                analyst_ids = []
                for analyst in analysts:
                    saved_analyst = await self.uow.analysts.create(analyst)
                    analyst_ids.append(saved_analyst.id)

                # Update project with analysts
                project = self.research_service.add_analysts_to_project(
                    project, analysts
                )
                await self.uow.research_projects.update(project)

                # Create associations
                self.uow.create_project_associations(
                    project_id, analyst_ids=analyst_ids
                )

                logger.info(
                    f"Generated {len(analysts)} analysts for project: {project_id}"
                )
                return analysts

        except Exception as e:
            logger.error(f"Failed to generate analysts: {e}")
            raise

    async def conduct_interview(
        self, project_id: str, analyst: Analyst, topic: str, max_turns: int = 2
    ) -> Interview:
        """Conduct an interview between an analyst and expert."""
        try:
            async with self.uow:
                # Create interview
                interview = self.interview_service.create_interview(
                    analyst, topic, max_turns
                )
                interview = await self.uow.interviews.create(interview)

                # Initialize conversation
                messages = []

                # Conduct interview conversation
                for turn in range(max_turns):
                    # Generate analyst question
                    question = await self._generate_interview_question(
                        analyst, messages
                    )
                    messages.append(
                        {"type": "human", "content": question, "name": "analyst"}
                    )

                    # Search for context
                    search_context = await self._search_for_context(messages)

                    # Add context to interview
                    if search_context:
                        interview = self.interview_service.add_context_to_interview(
                            interview, [search_context]
                        )

                    # Generate expert answer
                    answer = await self._generate_expert_answer(
                        analyst, messages, search_context
                    )
                    messages.append({"type": "ai", "content": answer, "name": "expert"})

                    # Check if interview should continue
                    if not self.interview_service.should_continue_interview(
                        messages, max_turns, "expert"
                    ):
                        break

                # Complete interview
                transcript = self._format_interview_transcript(messages)
                interview = self.interview_service.update_interview_transcript(
                    interview, transcript
                )
                interview = self.interview_service.complete_interview(interview)

                # Update in repository
                interview = await self.uow.interviews.update(interview)

                # Associate with project
                self.uow.create_project_associations(
                    project_id, interview_ids=[interview.id]
                )

                logger.info(
                    f"Completed interview: {interview.id} with analyst: {analyst.name}"
                )
                return interview

        except Exception as e:
            logger.error(f"Failed to conduct interview: {e}")
            raise

    async def write_research_section(
        self, project_id: str, interview: Interview, analyst: Analyst
    ) -> ResearchSection:
        """Write a research section based on interview data."""
        try:
            async with self.uow:
                # Get context from interview
                context = (
                    "\n\n".join(interview.context_documents)
                    if interview.context_documents
                    else interview.transcript
                )

                # Generate section content
                if self.use_mock and self.mock_service:
                    content = await self.mock_service.write_research_section(
                        analyst, context
                    )
                elif self.llm_service:
                    content = await self.llm_service.write_research_section(
                        analyst, context
                    )
                else:
                    content = f"## {analyst.role} Analysis\n\nResearch section based on interview data."

                # Validate content
                if not self.section_service.validate_section_content(content):
                    logger.warning(
                        f"Generated section content may be low quality for analyst: {analyst.name}"
                    )

                # Extract sources and title
                sources = self.section_service.extract_sources_from_content(content)
                title = self.section_service.generate_section_title(
                    analyst, interview.topic
                )

                # Create section
                section = self.section_service.create_section(
                    interview, analyst, title, content, sources
                )

                # Save section
                section = await self.uow.research_sections.create(section)

                # Associate with project
                self.uow.create_project_associations(
                    project_id, section_ids=[section.id]
                )

                logger.info(
                    f"Created research section: {section.id} for analyst: {analyst.name}"
                )
                return section

        except Exception as e:
            logger.error(f"Failed to write research section: {e}")
            raise

    async def run_complete_research(
        self,
        topic: str,
        max_analysts: int = 3,
        max_interview_turns: int = 2,
        human_feedback: Optional[str] = None,
    ) -> ResearchProject:
        """Run the complete research workflow from start to finish."""
        try:
            # Step 1: Create project
            project = await self.create_research_project(topic, max_analysts)

            # Step 2: Generate analysts
            analysts = await self.generate_analysts(
                project.id, topic, max_analysts, human_feedback
            )

            # Step 3: Conduct interviews for each analyst
            interviews = []
            for analyst in analysts:
                interview = await self.conduct_interview(
                    project.id, analyst, topic, max_interview_turns
                )
                interviews.append(interview)

            # Step 4: Write research sections
            sections = []
            for i, analyst in enumerate(analysts):
                if i < len(interviews):
                    section = await self.write_research_section(
                        project.id, interviews[i], analyst
                    )
                    sections.append(section)

            # Step 5: Complete project
            async with self.uow:
                project = self.research_service.update_project_status(
                    project, "completed"
                )
                project = await self.uow.research_projects.update(project)

            logger.info(f"Completed full research workflow for project: {project.id}")
            return project

        except Exception as e:
            logger.error(f"Failed to run complete research: {e}")
            raise

    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get detailed status information about a research project."""
        async with self.uow:
            project = await self.uow.research_projects.get_by_id(project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            analysts = await self.uow.analysts.get_by_project_id(project_id)
            interviews = await self.uow.interviews.get_by_project_id(project_id)
            sections = await self.uow.research_sections.get_by_project_id(project_id)

            progress = self.research_service.get_project_progress(project)
            is_complete = self.research_service.is_project_complete(project)

            return {
                "project": project,
                "analysts": analysts,
                "interviews": interviews,
                "sections": sections,
                "progress": progress,
                "is_complete": is_complete,
            }

    # Private helper methods

    async def _generate_interview_question(
        self, analyst: Analyst, messages: List[Dict[str, Any]]
    ) -> str:
        """Generate an interview question."""
        if self.use_mock and self.mock_service:
            return await self.mock_service.generate_interview_question(
                analyst, messages
            )
        elif self.llm_service:
            return await self.llm_service.generate_interview_question(analyst, messages)
        else:
            return f"Hello, I'm {analyst.name}. Could you share your thoughts on this topic?"

    async def _search_for_context(self, messages: List[Dict[str, Any]]) -> str:
        """Search for context to support the interview."""
        try:
            # Generate search query
            if self.use_mock and self.mock_service:
                # Use mock search
                web_results = await self.mock_service.search_web("research query")
                wikipedia_results = await self.mock_service.search_wikipedia(
                    "research query"
                )
            else:
                # Generate search query using LLM
                search_query = "research topic"  # Fallback
                if self.llm_service:
                    search_query = await self.llm_service.generate_search_query(
                        messages
                    )

                # Search web and Wikipedia
                web_results = []
                wikipedia_results = []

                if self.tavily_service:
                    web_results = await self.tavily_service.search(search_query)

                if self.wikipedia_service:
                    wikipedia_results = await self.wikipedia_service.search(
                        search_query
                    )

            # Format results for context
            all_results = web_results + wikipedia_results
            if self.tavily_service:
                return self.tavily_service.format_documents_for_context(all_results)
            elif self.wikipedia_service:
                return self.wikipedia_service.format_documents_for_context(all_results)
            elif self.mock_service:
                return self.mock_service.format_documents_for_context(all_results)
            else:
                return "No search context available"

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return "Search context unavailable"

    async def _generate_expert_answer(
        self, analyst: Analyst, messages: List[Dict[str, Any]], context: str
    ) -> str:
        """Generate an expert answer."""
        if self.use_mock and self.mock_service:
            return await self.mock_service.generate_expert_answer(
                analyst, messages, context
            )
        elif self.llm_service:
            return await self.llm_service.generate_expert_answer(
                analyst, messages, context
            )
        else:
            return "Thank you for the question. Based on available information, here are some key insights."

    def _format_interview_transcript(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages into a readable transcript."""
        transcript_lines = []

        for msg in messages:
            role = "Analyst" if msg.get("name") == "analyst" else "Expert"
            content = msg.get("content", "")
            transcript_lines.append(f"{role}: {content}")

        return "\n\n".join(transcript_lines)
