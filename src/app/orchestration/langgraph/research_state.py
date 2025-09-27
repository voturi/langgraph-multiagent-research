"""Research-specific LangGraph state definition."""

import operator
from typing import Annotated, Any, Dict, List, Optional

from typing_extensions import TypedDict

from ...domain.entities.research import Analyst, Interview, ResearchSection


class ResearchState(TypedDict):
    """State for research assistant LangGraph workflow."""

    # Input parameters
    topic: str
    max_analysts: int
    max_interview_turns: int
    human_feedback: Optional[str]

    # Project management
    project_id: Optional[str]
    project_status: str

    # Analysts
    analysts: List[Analyst]
    current_analyst_index: int

    # Interviews
    interviews: List[Interview]
    current_interview: Optional[Interview]

    # Messages and context
    messages: Annotated[List[Dict[str, Any]], operator.add]
    search_context: List[str]

    # Research sections
    sections: List[ResearchSection]

    # Workflow control
    current_step: str
    workflow_complete: bool

    # Output data
    output_data: Dict[str, Any]

    # Error handling
    error: Optional[str]
    success: bool

    # Execution metadata
    execution_metadata: Dict[str, Any]


# State update helpers
def update_research_state(**kwargs) -> Dict[str, Any]:
    """Helper function to create state updates."""
    return {k: v for k, v in kwargs.items() if v is not None}


def add_message_to_state(
    role: str, content: str, name: Optional[str] = None
) -> Dict[str, Any]:
    """Helper to add a message to the state."""
    message = {
        "role": role,
        "content": content,
        "timestamp": None,  # Could add timestamp if needed
    }
    if name:
        message["name"] = name

    return {"messages": [message]}


def set_error_state(error_message: str) -> Dict[str, Any]:
    """Helper to set error state."""
    return {"error": error_message, "success": False, "workflow_complete": True}


def set_success_state(output_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Helper to set success state."""
    return {
        "success": True,
        "workflow_complete": True,
        "output_data": output_data or {},
    }
