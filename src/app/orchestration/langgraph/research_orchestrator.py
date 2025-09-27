"""Research LangGraph orchestrator that builds and manages the research workflow graph."""

import logging
from typing import Any, Dict, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from ...application.workflows.research_workflow import ResearchWorkflow
from .research_nodes import (
    ResearchNodes,
    route_after_section,
    should_continue_interviews,
    should_process_human_feedback,
)
from .research_state import ResearchState

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """LangGraph orchestrator for research assistant workflow."""

    def __init__(self, research_workflow: ResearchWorkflow):
        self.research_workflow = research_workflow
        self.nodes = ResearchNodes(research_workflow)
        self._graph = None
        logger.info("Research orchestrator initialized")

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        try:
            # Create the graph
            workflow = StateGraph(ResearchState)

            # Add nodes
            workflow.add_node("create_project", self.nodes.create_project_node)
            workflow.add_node("generate_analysts", self.nodes.generate_analysts_node)
            workflow.add_node("human_feedback", self.nodes.human_feedback_node)
            workflow.add_node("conduct_interview", self.nodes.conduct_interview_node)
            workflow.add_node("write_section", self.nodes.write_section_node)
            workflow.add_node("advance_analyst", self.nodes.advance_analyst_node)
            workflow.add_node("complete_research", self.nodes.complete_research_node)

            # Set entry point
            workflow.add_edge(START, "create_project")

            # Project creation flow
            workflow.add_edge("create_project", "generate_analysts")

            # Human feedback flow (with interruption)
            workflow.add_edge("generate_analysts", "human_feedback")
            workflow.add_conditional_edges(
                "human_feedback",
                should_process_human_feedback,
                {
                    "process_feedback": "generate_analysts",  # Re-generate with feedback
                    "continue_workflow": "conduct_interview",
                },
            )

            # Interview and section writing loop
            workflow.add_edge("conduct_interview", "write_section")
            workflow.add_edge("write_section", "advance_analyst")
            workflow.add_conditional_edges(
                "advance_analyst",
                should_continue_interviews,
                {
                    "conduct_interview": "conduct_interview",
                    "complete_research": "complete_research",
                },
            )

            # End of workflow
            workflow.add_edge("complete_research", END)

            # Compile graph with checkpointer for state persistence
            memory = MemorySaver()
            self._graph = workflow.compile(
                checkpointer=memory,
                interrupt_before=["human_feedback"]  # Allow human intervention
            )

            logger.info("Research workflow graph built successfully")
            return self._graph

        except Exception as e:
            logger.error(f"Failed to build research workflow graph: {e}")
            raise

    def get_graph(self):
        """Get the compiled graph, building if necessary."""
        if self._graph is None:
            self._graph = self.build_graph()
        return self._graph

    async def run_research(
        self,
        topic: str,
        max_analysts: int = 3,
        max_interview_turns: int = 2,
        human_feedback: Optional[str] = None,
        thread_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run the complete research workflow."""
        try:
            graph = self.get_graph()

            # Prepare initial state
            initial_state = {
                "topic": topic,
                "max_analysts": max_analysts,
                "max_interview_turns": max_interview_turns,
                "human_feedback": human_feedback,
                "project_id": None,
                "project_status": "created",
                "analysts": [],
                "current_analyst_index": 0,
                "interviews": [],
                "current_interview": None,
                "messages": [],
                "search_context": [],
                "sections": [],
                "current_step": "start",
                "workflow_complete": False,
                "output_data": {},
                "error": None,
                "success": False,
                "execution_metadata": {"started_at": None, "completed_at": None},
            }

            # Default thread config
            if thread_config is None:
                thread_config = {
                    "configurable": {"thread_id": f"research_{topic[:10]}"}
                }

            # Run the workflow
            result = None
            async for event in graph.astream(
                initial_state, thread_config, stream_mode="values"
            ):
                result = event
                logger.debug(f"Workflow step completed: {event.get('current_step')}")

            return result or {"error": "No result from workflow"}

        except Exception as e:
            logger.error(f"Failed to run research workflow: {e}")
            return {"error": str(e), "success": False, "workflow_complete": True}

    async def run_research_with_interruption(
        self,
        topic: str,
        max_analysts: int = 3,
        max_interview_turns: int = 2,
        thread_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run research workflow with human feedback interruption."""
        try:
            graph = self.get_graph()

            # Prepare initial state
            initial_state = {
                "topic": topic,
                "max_analysts": max_analysts,
                "max_interview_turns": max_interview_turns,
                "human_feedback": None,
                "project_id": None,
                "project_status": "created",
                "analysts": [],
                "current_analyst_index": 0,
                "interviews": [],
                "current_interview": None,
                "messages": [],
                "search_context": [],
                "sections": [],
                "current_step": "start",
                "workflow_complete": False,
                "output_data": {},
                "error": None,
                "success": False,
                "execution_metadata": {},
            }

            # Default thread config
            if thread_config is None:
                thread_config = {
                    "configurable": {"thread_id": f"research_interactive_{topic[:10]}"}
                }

            # Run until interruption
            result = None
            async for event in graph.astream(
                initial_state, thread_config, stream_mode="values"
            ):
                result = event

                # Check if we hit the interruption point
                if event.get("current_step") == "awaiting_human_feedback":
                    logger.info("Workflow paused for human feedback")
                    break

            return {
                "status": "paused_for_feedback",
                "current_state": result,
                "thread_config": thread_config,
                "message": "Workflow paused for human feedback. Use continue_research_with_feedback to proceed.",
            }

        except Exception as e:
            logger.error(f"Failed to run research workflow with interruption: {e}")
            return {"error": str(e), "success": False, "workflow_complete": True}

    async def continue_research_with_feedback(
        self, human_feedback: str, thread_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Continue research workflow with human feedback."""
        try:
            graph = self.get_graph()

            # Update state with human feedback
            graph.update_state(
                thread_config,
                {"human_feedback": human_feedback},
                as_node="human_feedback",
            )

            # Continue the workflow
            result = None
            async for event in graph.astream(None, thread_config, stream_mode="values"):
                result = event
                logger.debug(f"Workflow step completed: {event.get('current_step')}")

            return result or {"error": "No result from continued workflow"}

        except Exception as e:
            logger.error(f"Failed to continue research workflow: {e}")
            return {"error": str(e), "success": False, "workflow_complete": True}

    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the research workflow."""
        return {
            "workflow_name": "Research Assistant",
            "workflow_type": "LangGraph",
            "nodes": [
                "create_project",
                "generate_analysts",
                "human_feedback",
                "conduct_interview",
                "write_section",
                "advance_analyst",
                "complete_research",
            ],
            "supports_interruption": True,
            "interrupt_points": ["human_feedback"],
            "description": "Multi-analyst research workflow with human feedback capability",
        }
