"""Base workflow orchestrator - Framework-agnostic orchestration interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from ...domain.models.value_objects import (
    UserId, ConversationId, ExecutionResult, ExecutionContext
)
from ...domain.services import (
    ConversationService, TaskService, WorkflowService, MessageService, UserService
)
from ...domain.interfaces.repositories import UnitOfWork
from ...domain.interfaces.events import EventPublisher

logger = logging.getLogger(__name__)


class WorkflowOrchestrator(ABC):
    """Base class for workflow orchestration
    
    This provides a framework-agnostic interface that can be implemented
    with LangGraph, Apache Airflow, or any other orchestration framework.
    """
    
    def __init__(
        self,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        conversation_service: ConversationService,
        task_service: TaskService,
        workflow_service: WorkflowService,
        message_service: MessageService,
        user_service: UserService
    ):
        self.uow = uow
        self.event_publisher = event_publisher
        self.conversation_service = conversation_service
        self.task_service = task_service
        self.workflow_service = workflow_service
        self.message_service = message_service
        self.user_service = user_service
    
    @abstractmethod
    async def execute_workflow(
        self,
        workflow_name: str,
        context: ExecutionContext,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a workflow with the given context and input data
        
        Args:
            workflow_name: Name of the workflow to execute
            context: Execution context with user, conversation info
            input_data: Input data for the workflow
            
        Returns:
            Execution result with success status and output data
        """
        pass
    
    @abstractmethod
    async def get_available_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available workflows with their metadata
        
        Returns:
            Dict mapping workflow names to their metadata
        """
        pass
    
    @abstractmethod
    async def cancel_workflow_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution
        
        Args:
            execution_id: ID of the execution to cancel
            
        Returns:
            True if cancellation was successful
        """
        pass
    
    @abstractmethod
    async def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow execution
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Status information or None if not found
        """
        pass
    
    # Helper methods that can be used by concrete implementations
    
    async def _validate_context(self, context: ExecutionContext) -> bool:
        """Validate execution context"""
        try:
            # Check if user exists
            user = await self.user_service.get_user(self.uow, context.user_id)
            if not user:
                logger.error(f"User {context.user_id} not found")
                return False
                
            # Check if conversation exists (if provided)
            if context.conversation_id:
                conversation = await self.conversation_service.get_conversation(
                    self.uow, context.conversation_id
                )
                if not conversation:
                    logger.error(f"Conversation {context.conversation_id} not found")
                    return False
                    
                # Check if user owns the conversation
                if conversation.user_id != context.user_id:
                    logger.error(f"User {context.user_id} does not own conversation {context.conversation_id}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Context validation failed: {e}")
            return False
    
    async def _log_workflow_start(
        self,
        workflow_name: str,
        execution_id: str,
        context: ExecutionContext
    ) -> None:
        """Log workflow execution start"""
        logger.info(
            f"Starting workflow '{workflow_name}' (execution: {execution_id}) "
            f"for user {context.user_id}"
        )
    
    async def _log_workflow_completion(
        self,
        workflow_name: str,
        execution_id: str,
        success: bool,
        execution_time: float
    ) -> None:
        """Log workflow execution completion"""
        status = "completed" if success else "failed"
        logger.info(
            f"Workflow '{workflow_name}' (execution: {execution_id}) {status} "
            f"in {execution_time:.2f}s"
        )
    
    def _create_error_result(
        self,
        error_message: str,
        execution_time: float = 0.0
    ) -> ExecutionResult:
        """Create error result"""
        return ExecutionResult.error_result(error_message, execution_time)
    
    def _create_success_result(
        self,
        data: Dict[str, Any] = None,
        execution_time: float = 0.0
    ) -> ExecutionResult:
        """Create success result"""
        return ExecutionResult.success_result(data or {}, execution_time)