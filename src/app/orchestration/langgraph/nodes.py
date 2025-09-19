"""LangGraph nodes - Thin wrappers around domain services"""

import logging
from typing import Dict, Any

from .state import LangGraphState
from ...domain.models.value_objects import ExecutionContext
from ...orchestration.workflows import ConversationWorkflow

logger = logging.getLogger(__name__)


class ConversationNode:
    """LangGraph node that delegates to domain workflow
    
    This is a thin wrapper that translates LangGraph state to domain context
    and delegates the actual work to framework-agnostic domain services.
    """
    
    def __init__(self, conversation_workflow: ConversationWorkflow):
        self.conversation_workflow = conversation_workflow
    
    async def __call__(self, state: LangGraphState) -> Dict[str, Any]:
        """Execute conversation node
        
        This method translates between LangGraph state and domain context,
        keeping the translation layer as thin as possible.
        """
        try:
            # Translate LangGraph state to domain context
            context = ExecutionContext(
                user_id=state["user_id"],
                conversation_id=state.get("conversation_id"),
                session_id=state["session_id"],
                parameters=state.get("execution_metadata", {})
            )
            
            # Execute domain workflow
            result = await self.conversation_workflow.execute_workflow(
                workflow_name=state["workflow_name"],
                context=context,
                input_data=state["input_data"]
            )
            
            # Translate result back to LangGraph state
            return {
                "output_data": result.data,
                "success": result.success,
                "error": result.error_message,
                "current_step": "conversation_completed",
                "execution_metadata": {
                    **state.get("execution_metadata", {}),
                    "execution_time": result.execution_time
                }
            }
            
        except Exception as e:
            logger.error(f"Conversation node failed: {e}")
            return {
                "output_data": {},
                "success": False,
                "error": str(e),
                "current_step": "conversation_failed"
            }


class ToolNode:
    """LangGraph node for tool execution
    
    Another thin wrapper that could handle tool-specific orchestration
    while delegating to domain services.
    """
    
    def __init__(self, conversation_workflow: ConversationWorkflow):
        self.conversation_workflow = conversation_workflow
    
    async def __call__(self, state: LangGraphState) -> Dict[str, Any]:
        """Execute tool node"""
        try:
            # For now, delegate to conversation workflow with tools
            context = ExecutionContext(
                user_id=state["user_id"],
                conversation_id=state.get("conversation_id"),
                session_id=state["session_id"],
                parameters=state.get("execution_metadata", {})
            )
            
            # Force workflow to use tools
            result = await self.conversation_workflow.execute_workflow(
                workflow_name="chat_with_tools",
                context=context,
                input_data=state["input_data"]
            )
            
            return {
                "output_data": result.data,
                "success": result.success,
                "error": result.error_message,
                "current_step": "tool_completed"
            }
            
        except Exception as e:
            logger.error(f"Tool node failed: {e}")
            return {
                "output_data": {},
                "success": False,
                "error": str(e),
                "current_step": "tool_failed"
            }


def should_continue(state: LangGraphState) -> str:
    """Conditional edge function for LangGraph
    
    This determines the next step in the workflow based on state.
    Keeps routing logic separate from domain logic.
    """
    if state.get("error"):
        return "error"
    
    if state.get("success", False):
        return "complete"
    
    # Default to continue processing
    return "continue"


def route_workflow(state: LangGraphState) -> str:
    """Route to appropriate workflow based on input
    
    This is LangGraph-specific routing logic that stays in the
    orchestration layer and doesn't leak into domain services.
    """
    workflow_name = state.get("workflow_name", "")
    
    if "tool" in workflow_name.lower():
        return "tool_node"
    else:
        return "conversation_node"