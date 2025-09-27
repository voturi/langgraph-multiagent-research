"""Research entry point for LangGraph Studio integration."""

import logging
import os

from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver

from ...application.workflows.research_workflow import ResearchWorkflow
from ...domain.services.analyst_service import AnalystService
from ...domain.services.interview_service import InterviewService, SectionService
from ...domain.services.research_service import ResearchService
from ...infrastructure.repositories.research_unit_of_work import ResearchUnitOfWork
from ...infrastructure.services.mock_research_service import MockResearchService
from ...infrastructure.services.research_llm_service import ResearchLLMService
from ...infrastructure.services.tavily_service import TavilySearchService
from ...infrastructure.services.wikipedia_service import WikipediaSearchService
from .research_orchestrator import ResearchOrchestrator

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class StudioEventPublisher:
    """Simple event publisher for Studio demo."""

    async def publish(self, event):
        logger.info(f"Event published: {type(event).__name__}")


def create_research_dependencies():
    """Create dependencies for Research Assistant Studio demo."""

    # Check API keys
    openai_api_key = os.getenv("OPENAI_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")

    # Determine if we should use mock services
    use_mock = not (openai_api_key and tavily_api_key)

    if use_mock:
        logger.warning(
            "API keys not found - using mock services for research assistant"
        )
    else:
        logger.info("API keys found - using real services for research assistant")

    # Create core dependencies
    event_publisher = StudioEventPublisher()
    uow = ResearchUnitOfWork()

    # Create domain services
    research_service = ResearchService(event_publisher)
    analyst_service = AnalystService(event_publisher)
    interview_service = InterviewService(event_publisher)
    section_service = SectionService(event_publisher)

    # Create external services
    llm_service = None
    tavily_service = None
    wikipedia_service = None
    mock_service = None

    if not use_mock:
        # Real services
        llm_service = ResearchLLMService(
            api_key=openai_api_key,
            default_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )
        tavily_service = TavilySearchService(api_key=tavily_api_key)
        wikipedia_service = WikipediaSearchService()
    else:
        # Mock service
        mock_service = MockResearchService()

    # Create research workflow
    research_workflow = ResearchWorkflow(
        research_service=research_service,
        analyst_service=analyst_service,
        interview_service=interview_service,
        section_service=section_service,
        uow=uow,
        event_publisher=event_publisher,
        llm_service=llm_service,
        tavily_service=tavily_service,
        wikipedia_service=wikipedia_service,
        mock_service=mock_service,
        use_mock=use_mock,
    )

    return research_workflow


def build_research_graph():
    """Build the research assistant graph for LangGraph Studio."""

    try:
        # Create dependencies
        research_workflow = create_research_dependencies()

        # Create orchestrator and build graph
        orchestrator = ResearchOrchestrator(research_workflow)
        compiled_graph = orchestrator.build_graph()

        logger.info("Research assistant graph compiled successfully for Studio")
        return compiled_graph

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to build research graph: {error_msg}")

        # Return a minimal fallback graph
        from langgraph.graph import END, START, StateGraph

        from .research_state import ResearchState

        workflow = StateGraph(ResearchState)

        def demo_node(state: ResearchState):
            return {
                "output_data": {
                    "message": "Research Assistant demo - configure API keys for full functionality",
                    "error": f"Graph build failed: {error_msg}",
                },
                "success": False,
                "current_step": "demo_complete",
                "workflow_complete": True,
            }

        workflow.add_node("demo", demo_node)
        workflow.add_edge(START, "demo")
        workflow.add_edge("demo", END)

        # Add checkpointer for consistency
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)


# Create the graph instance that Studio expects
graph = build_research_graph()


def get_graph():
    """Factory function for getting the graph (alternative Studio entry point)."""
    return graph


# Additional Studio configuration
def get_graph_config():
    """Get configuration for Studio."""
    return {
        "title": "Research Assistant - Multi-Analyst Research Workflow",
        "description": "AI-powered research assistant that creates multiple analyst personas, conducts interviews, and generates comprehensive research sections",
        "version": "1.0.0",
        "tags": ["research", "multi-agent", "clean-architecture", "interviews"],
        "sample_inputs": [
            {
                "name": "Software Design Patterns Research",
                "input": {
                    "topic": "Design patterns in Python for enterprise applications",
                    "max_analysts": 3,
                    "max_interview_turns": 2,
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
                },
            },
            {
                "name": "AI/ML Research with Human Feedback",
                "input": {
                    "topic": "Latest developments in Large Language Models",
                    "max_analysts": 2,
                    "max_interview_turns": 3,
                    "human_feedback": "Please include perspectives from both academic researchers and industry practitioners",
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
                },
            },
            {
                "name": "Business Strategy Research",
                "input": {
                    "topic": "Digital transformation strategies for traditional businesses",
                    "max_analysts": 4,
                    "max_interview_turns": 2,
                    "human_feedback": "Focus on both challenges and opportunities",
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
                },
            },
        ],
    }


if __name__ == "__main__":
    # Test the graph creation
    try:
        test_graph = build_research_graph()
        print("✅ Research assistant graph built successfully")
        print(f"Graph nodes: {list(test_graph.get_graph().nodes.keys())}")
        print("🎯 Ready for LangGraph Studio!")

        # Test workflow info
        if hasattr(test_graph, "research_workflow"):
            workflow_info = test_graph.research_workflow.get_workflow_info()
            print(f"📋 Workflow: {workflow_info}")

    except Exception as e:
        print(f"❌ Research assistant graph build failed: {e}")
        import traceback

        traceback.print_exc()
