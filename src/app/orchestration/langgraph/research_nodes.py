"""Research-specific LangGraph nodes for the research assistant workflow."""

import logging
from typing import Any, Dict

from ...application.workflows.research_workflow import ResearchWorkflow
from .research_state import (
    ResearchState,
    add_message_to_state,
    set_error_state,
    set_success_state,
    update_research_state,
)

logger = logging.getLogger(__name__)


class ResearchNodes:
    """LangGraph nodes for research assistant workflow."""

    def __init__(self, research_workflow: ResearchWorkflow):
        self.research_workflow = research_workflow
        logger.info("Research nodes initialized")

    async def create_project_node(self, state: ResearchState) -> Dict[str, Any]:
        """Node to create a research project."""
        try:
            logger.info(f"Creating research project for topic: {state.get('topic')}")

            topic = state.get("topic")
            max_analysts = state.get("max_analysts", 3)

            if not topic:
                return set_error_state("Topic is required to create a research project")

            # Create project using workflow
            project = await self.research_workflow.create_research_project(
                topic, max_analysts
            )

            return update_research_state(
                project_id=project.id,
                project_status=project.status,
                current_step="project_created",
                output_data={"project_created": True, "project_id": project.id},
            )

        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return set_error_state(f"Failed to create research project: {str(e)}")

    async def generate_analysts_node(self, state: ResearchState) -> Dict[str, Any]:
        """Node to generate analyst personas."""
        try:
            logger.info("Generating analyst personas")

            project_id = state.get("project_id")
            topic = state.get("topic")
            max_analysts = state.get("max_analysts", 3)
            human_feedback = state.get("human_feedback")

            if not project_id or not topic:
                return set_error_state(
                    "Project ID and topic are required to generate analysts"
                )

            # Generate analysts using workflow
            analysts = await self.research_workflow.generate_analysts(
                project_id, topic, max_analysts, human_feedback
            )

            return update_research_state(
                analysts=analysts,
                current_analyst_index=0,
                current_step="analysts_created",
                output_data={
                    "analysts_generated": len(analysts),
                    "analyst_names": [a.name for a in analysts],
                },
            )

        except Exception as e:
            logger.error(f"Failed to generate analysts: {e}")
            return set_error_state(f"Failed to generate analysts: {str(e)}")

    async def conduct_interview_node(self, state: ResearchState) -> Dict[str, Any]:
        """Node to conduct an interview with current analyst."""
        try:
            logger.info("Conducting interview")

            project_id = state.get("project_id")
            topic = state.get("topic")
            analysts = state.get("analysts", [])
            current_index = state.get("current_analyst_index", 0)
            max_turns = state.get("max_interview_turns", 2)

            if not project_id or not topic:
                return set_error_state(
                    "Project ID and topic are required for interviews"
                )

            if not analysts or current_index >= len(analysts):
                return set_error_state("No analysts available for interview")

            # Get current analyst
            current_analyst = analysts[current_index]

            # Conduct interview using workflow
            interview = await self.research_workflow.conduct_interview(
                project_id, current_analyst, topic, max_turns
            )

            # Update interviews list
            interviews = state.get("interviews", [])
            interviews.append(interview)

            return update_research_state(
                interviews=interviews,
                current_interview=interview,
                current_step="interview_completed",
                output_data={
                    "interview_completed": True,
                    "analyst_name": current_analyst.name,
                    "interview_id": interview.id,
                },
            )

        except Exception as e:
            logger.error(f"Failed to conduct interview: {e}")
            return set_error_state(f"Failed to conduct interview: {str(e)}")

    async def write_section_node(self, state: ResearchState) -> Dict[str, Any]:
        """Node to write a research section from interview."""
        try:
            logger.info("Writing research section")

            project_id = state.get("project_id")
            analysts = state.get("analysts", [])
            interviews = state.get("interviews", [])
            current_index = state.get("current_analyst_index", 0)

            if not project_id:
                return set_error_state("Project ID is required to write sections")

            if not analysts or current_index >= len(analysts):
                return set_error_state("No analysts available for section writing")

            if not interviews or len(interviews) <= current_index:
                return set_error_state(
                    "No corresponding interview found for section writing"
                )

            # Get current analyst and interview
            current_analyst = analysts[current_index]
            current_interview = interviews[current_index]

            # Write section using workflow
            section = await self.research_workflow.write_research_section(
                project_id, current_interview, current_analyst
            )

            # Update sections list
            sections = state.get("sections", [])
            sections.append(section)

            return update_research_state(
                sections=sections,
                current_step="section_written",
                output_data={
                    "section_written": True,
                    "section_title": section.title,
                    "section_id": section.id,
                },
            )

        except Exception as e:
            logger.error(f"Failed to write section: {e}")
            return set_error_state(f"Failed to write research section: {str(e)}")

    async def advance_analyst_node(self, state: ResearchState) -> Dict[str, Any]:
        """Node to advance to the next analyst."""
        try:
            current_index = state.get("current_analyst_index", 0)
            analysts = state.get("analysts", [])

            next_index = current_index + 1

            if next_index >= len(analysts):
                # All analysts processed, move to completion
                return update_research_state(
                    current_analyst_index=next_index,
                    current_step="all_analysts_processed",
                )
            else:
                # Move to next analyst
                return update_research_state(
                    current_analyst_index=next_index, current_step="next_analyst_ready"
                )

        except Exception as e:
            logger.error(f"Failed to advance analyst: {e}")
            return set_error_state(f"Failed to advance to next analyst: {str(e)}")

    async def complete_research_node(self, state: ResearchState) -> Dict[str, Any]:
        """Node to complete the research project."""
        try:
            logger.info("Completing research project")

            project_id = state.get("project_id")
            if not project_id:
                return set_error_state("Project ID is required to complete research")

            # Get project status
            status_info = await self.research_workflow.get_project_status(project_id)
            project = status_info["project"]

            # Update project status to completed if not already
            if project.status != "completed":
                async with self.research_workflow.uow:
                    project = (
                        self.research_workflow.research_service.update_project_status(
                            project, "completed"
                        )
                    )
                    await self.research_workflow.uow.research_projects.update(project)

            # Prepare final output
            output_data = {
                "research_completed": True,
                "project_id": project.id,
                "topic": project.topic,
                "total_analysts": len(status_info["analysts"]),
                "total_interviews": len(status_info["interviews"]),
                "total_sections": len(status_info["sections"]),
                "project_status": project.status,
                "sections": [
                    {
                        "title": section.title,
                        "content": section.content,  # Preserve full content
                        "content_preview": section.content[:200] + "..."
                        if len(section.content) > 200
                        else section.content,  # Keep preview for UI that needs it
                        "analyst_name": next(
                            (
                                a.name
                                for a in status_info["analysts"]
                                if a.id == section.analyst_id
                            ),
                            "Unknown",
                        ),
                        "sources": section.sources,
                    }
                    for section in status_info["sections"]
                ],
            }

            return set_success_state(output_data)

        except Exception as e:
            logger.error(f"Failed to complete research: {e}")
            return set_error_state(f"Failed to complete research: {str(e)}")

    async def human_feedback_node(self, state: ResearchState) -> Dict[str, Any]:
        """Node for human feedback interaction (no-op for interruption)."""
        logger.info("Human feedback node - waiting for user input")

        # If we have feedback, process it and clear it to prevent loops
        human_feedback = state.get("human_feedback")
        if human_feedback and human_feedback.strip():
            logger.info(f"Processing human feedback: {human_feedback[:100]}...")
            # Clear the feedback after processing to prevent loops
            return update_research_state(
                human_feedback=None, current_step="feedback_processed"  # Clear feedback
            )
        else:
            # No feedback provided, continue normally
            return update_research_state(current_step="awaiting_human_feedback")


# Routing functions
def should_continue_interviews(state: ResearchState) -> str:
    """Determine if more interviews should be conducted."""
    current_index = state.get("current_analyst_index", 0)
    analysts = state.get("analysts", [])

    if current_index < len(analysts):
        return "conduct_interview"
    else:
        return "complete_research"


def should_process_human_feedback(state: ResearchState) -> str:
    """Determine if human feedback should be processed."""
    current_step = state.get("current_step")
    human_feedback = state.get("human_feedback")

    # If we have feedback that hasn't been processed yet, process it
    if (
        human_feedback
        and human_feedback.strip()
        and current_step == "awaiting_human_feedback"
    ):
        return "process_feedback"
    # If feedback was processed (cleared), or no feedback, continue workflow
    else:
        return "continue_workflow"


def route_after_section(state: ResearchState) -> str:
    """Route after writing a section."""
    current_step = state.get("current_step")

    if current_step == "section_written":
        return "advance_analyst"
    else:
        return "complete_research"
