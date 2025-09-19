"""LangGraph orchestrator - Thin LangGraph wrapper over domain workflows"""

from typing import Dict, Any, Optional
import logging

from langgraph import StateGraph
from langgraph.graph import END, START

from .state import LangGraphState
from .nodes import ConversationNode, ToolNode, should_continue, route_workflow
from ..workflows.base import WorkflowOrchestrator
from ...domain.models.value_objects import ExecutionContext, ExecutionResult, UserId, ConversationId

logger = logging.getLogger(__name__)


class LangGraphOrchestrator(WorkflowOrchestrator):
    """LangGraph implementation of workflow orchestrator
    
    This is a thin wrapper that uses LangGraph for orchestration while
    keeping all business logic in domain services. LangGraph is treated
    as a swappable orchestration framework.
    """
    
    def __init__(self, conversation_workflow, **kwargs):
        super().__init__(**kwargs)
        self.conversation_workflow = conversation_workflow
        self.graph = None
        self._build_graph()
    
    def _build_graph(self) -> None:
        """Build the LangGraph state graph
        
        This creates the LangGraph-specific orchestration graph but keeps
        the actual business logic in domain services.
        """
        # Create nodes
        conversation_node = ConversationNode(self.conversation_workflow)
        tool_node = ToolNode(self.conversation_workflow)
        
        # Build graph
        workflow = StateGraph(LangGraphState)
        
        # Add nodes
        workflow.add_node("conversation_node", conversation_node)
        workflow.add_node("tool_node", tool_node)
        
        # Add routing logic
        workflow.add_conditional_edges(
            START,
            route_workflow,
            {
                "conversation_node": "conversation_node",
                "tool_node": "tool_node"
            }
        )
        
        # Add completion logic
        workflow.add_conditional_edges(
            "conversation_node",
            should_continue,
            {
                "complete": END,
                "error": END,
                "continue": "conversation_node"
            }
        )
        
        workflow.add_conditional_edges(
            "tool_node", 
            should_continue,
            {
                "complete": END,
                "error": END,
                "continue": "tool_node"
            }
        )
        
        self.graph = workflow.compile()
    
    async def execute_workflow(
        self,
        workflow_name: str,
        context: ExecutionContext,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute workflow using LangGraph
        
        This translates domain context to LangGraph state and back,
        keeping LangGraph concerns isolated from domain logic.
        """
        try:
            # Validate context using inherited method
            if not await self._validate_context(context):
                return self._create_error_result("Invalid execution context")
            
            # Translate domain context to LangGraph state
            initial_state = {
                "user_id": context.user_id,
                "conversation_id": context.conversation_id,
                "session_id": context.session_id,
                "workflow_name": workflow_name,
                "input_data": input_data,
                "output_data": {},
                "messages": [],
                "current_step": "start",
                "execution_metadata": context.parameters,
                "error": None,
                "success": False
            }
            
            # Execute LangGraph workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            # Translate result back to domain
            if final_state.get("success", False):
                return ExecutionResult.success_result(
                    data=final_state.get("output_data", {}),
                    execution_time=final_state.get("execution_metadata", {}).get("execution_time", 0.0)
                )
            else:
                return ExecutionResult.error_result(
                    error_message=final_state.get("error", "Workflow execution failed"),
                    execution_time=final_state.get("execution_metadata", {}).get("execution_time", 0.0)
                )
        
        except Exception as e:
            logger.error(f"LangGraph execution failed: {e}")
            return self._create_error_result(str(e))
    
    async def get_available_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Get available workflows from domain service
        
        Delegates to the domain workflow for business logic.
        """
        try:
            workflows = await self.conversation_workflow.get_available_workflows()
            
            # Add LangGraph-specific metadata
            for workflow_name, metadata in workflows.items():
                metadata["orchestrator"] = "langgraph"
                metadata["supports_streaming"] = True  # LangGraph feature
                metadata["supports_checkpoints"] = True  # LangGraph feature
            
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to get available workflows: {e}")
            return {}
    
    async def cancel_workflow_execution(self, execution_id: str) -> bool:
        """Cancel workflow execution
        
        In a production LangGraph setup, you'd integrate with LangGraph's
        execution tracking. For now, delegate to domain service.
        """
        try:
            return await self.conversation_workflow.cancel_workflow_execution(execution_id)
        except Exception as e:
            logger.error(f"Failed to cancel execution {execution_id}: {e}")
            return False
    
    async def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status
        
        In a production setup, this would integrate with LangGraph's
        execution tracking and checkpointing features.
        """
        try:
            status = await self.conversation_workflow.get_workflow_status(execution_id)
            
            if status:
                # Add LangGraph-specific status info
                status["orchestrator"] = "langgraph"
                status["graph_compiled"] = self.graph is not None
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get status for execution {execution_id}: {e}")
            return None
    
    def get_graph_visualization(self) -> Optional[str]:
        """Get LangGraph visualization (LangGraph-specific feature)
        
        This is an example of how you can expose framework-specific features
        while keeping them isolated from domain logic.
        """
        if not self.graph:
            return None
            
        try:
            # In a real implementation, you'd use LangGraph's visualization tools
            return "LangGraph workflow visualization would go here"
        except Exception as e:
            logger.error(f"Failed to generate graph visualization: {e}")
            return None
    
    async def execute_with_streaming(
        self,
        workflow_name: str,
        context: ExecutionContext,
        input_data: Dict[str, Any]
    ):
        """Execute workflow with streaming support (LangGraph-specific feature)
        
        This shows how framework-specific features can be added without
        affecting the core domain logic.
        """
        try:
            # Validate context
            if not await self._validate_context(context):
                yield {"error": "Invalid execution context"}
                return
            
            # Translate to LangGraph state
            initial_state = {
                "user_id": context.user_id,
                "conversation_id": context.conversation_id,
                "session_id": context.session_id,
                "workflow_name": workflow_name,
                "input_data": input_data,
                "output_data": {},
                "messages": [],
                "current_step": "start",
                "execution_metadata": context.parameters,
                "error": None,
                "success": False
            }
            
            # Stream execution steps
            async for step in self.graph.astream(initial_state):
                yield {
                    "step": step,
                    "current_node": step.get("current_step", "unknown"),
                    "partial_output": step.get("output_data", {})
                }
        
        except Exception as e:
            logger.error(f"Streaming execution failed: {e}")
            yield {"error": str(e)}