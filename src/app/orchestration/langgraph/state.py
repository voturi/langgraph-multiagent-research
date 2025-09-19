"""LangGraph state schema - Thin wrapper over domain models"""

from typing import List, Dict, Any, Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph import add_messages

from ...domain.models.value_objects import UserId, ConversationId


class LangGraphState(TypedDict):
    """LangGraph state that wraps domain context
    
    This is a thin translation layer between LangGraph's state format
    and our domain models. It keeps LangGraph-specific concerns isolated.
    """
    
    # Domain context
    user_id: UserId
    conversation_id: Optional[ConversationId]
    session_id: str
    
    # Workflow data
    workflow_name: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    
    # LangGraph-specific messages (if needed)
    messages: Annotated[List[Dict[str, Any]], add_messages]
    
    # Execution tracking
    current_step: str
    execution_metadata: Dict[str, Any]
    
    # Error handling
    error: Optional[str]
    success: bool