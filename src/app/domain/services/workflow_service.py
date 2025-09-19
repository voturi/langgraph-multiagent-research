"""Workflow domain service - Framework-agnostic business logic"""

from typing import List, Optional, Dict, Any
import logging
import time

from ..models.entities import WorkflowExecution
from ..models.value_objects import (
    UserId, ConversationId, TaskId, WorkflowId, TaskStatus, ExecutionResult
)
from ..models.events import WorkflowStarted, WorkflowFinished
from ..interfaces.repositories import UnitOfWork
from ..interfaces.events import EventPublisher

logger = logging.getLogger(__name__)


class WorkflowService:
    """Domain service for workflow business logic"""
    
    def __init__(self, event_publisher: EventPublisher):
        self.event_publisher = event_publisher
    
    async def create_workflow_execution(
        self,
        uow: UnitOfWork,
        workflow_id: WorkflowId,
        user_id: UserId,
        conversation_id: Optional[ConversationId] = None,
        context: Dict[str, Any] = None
    ) -> WorkflowExecution:
        """Create a new workflow execution"""
        async with uow:
            execution = WorkflowExecution(
                id=f"exec_{workflow_id}_{user_id}_{int(time.time())}",
                workflow_id=workflow_id,
                user_id=user_id,
                conversation_id=conversation_id,
                context=context or {}
            )
            
            await uow.workflows.save(execution)
            await uow.commit()
            
            logger.info(f"Created workflow execution {execution.id}")
            return execution
    
    async def start_workflow_execution(
        self,
        uow: UnitOfWork,
        execution_id: str
    ) -> WorkflowExecution:
        """Start a workflow execution"""
        async with uow:
            execution = await uow.workflows.find_by_id(execution_id)
            if not execution:
                raise ValueError(f"Workflow execution {execution_id} not found")
            
            execution.start()
            await uow.workflows.save(execution)
            await uow.commit()
            
            # Publish event
            event = WorkflowStarted(
                aggregate_id=execution.id,
                workflow_id=execution.workflow_id,
                user_id=execution.user_id,
                conversation_id=execution.conversation_id
            )
            await self.event_publisher.publish(event)
            
            logger.info(f"Started workflow execution {execution_id}")
            return execution
    
    async def complete_workflow_execution(
        self,
        uow: UnitOfWork,
        execution_id: str,
        success: bool = True,
        execution_time: float = 0.0
    ) -> WorkflowExecution:
        """Complete a workflow execution"""
        async with uow:
            execution = await uow.workflows.find_by_id(execution_id)
            if not execution:
                raise ValueError(f"Workflow execution {execution_id} not found")
            
            if success:
                execution.complete()
            else:
                execution.fail()
            
            await uow.workflows.save(execution)
            await uow.commit()
            
            # Publish event
            event = WorkflowFinished(
                aggregate_id=execution.id,
                workflow_id=execution.workflow_id,
                user_id=execution.user_id,
                success=success,
                execution_time=execution_time
            )
            await self.event_publisher.publish(event)
            
            status = "completed" if success else "failed"
            logger.info(f"Workflow execution {execution_id} {status}")
            return execution
    
    async def add_task_to_workflow(
        self,
        uow: UnitOfWork,
        execution_id: str,
        task_id: TaskId
    ) -> WorkflowExecution:
        """Add a task to workflow execution"""
        async with uow:
            execution = await uow.workflows.find_by_id(execution_id)
            if not execution:
                raise ValueError(f"Workflow execution {execution_id} not found")
            
            execution.add_task(task_id)
            await uow.workflows.save(execution)
            await uow.commit()
            
            logger.info(f"Added task {task_id} to workflow {execution_id}")
            return execution
    
    async def get_workflow_execution(
        self,
        uow: UnitOfWork,
        execution_id: str
    ) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID"""
        async with uow:
            return await uow.workflows.find_by_id(execution_id)
    
    async def get_user_workflow_executions(
        self,
        uow: UnitOfWork,
        user_id: UserId,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """Get workflow executions for a user"""
        async with uow:
            return await uow.workflows.find_by_user_id(user_id, limit)
    
    async def get_workflow_executions_by_workflow(
        self,
        uow: UnitOfWork,
        workflow_id: WorkflowId
    ) -> List[WorkflowExecution]:
        """Get executions for a specific workflow"""
        async with uow:
            return await uow.workflows.find_by_workflow_id(workflow_id)
    
    async def get_active_workflow_executions(
        self,
        uow: UnitOfWork
    ) -> List[WorkflowExecution]:
        """Get all active workflow executions"""
        async with uow:
            return await uow.workflows.find_active()
    
    def calculate_workflow_metrics(
        self,
        executions: List[WorkflowExecution]
    ) -> Dict[str, Any]:
        """Calculate workflow execution metrics"""
        total = len(executions)
        if total == 0:
            return {"total": 0}
        
        status_counts = {}
        total_execution_time = 0
        successful_executions = 0
        total_tasks = 0
        
        for execution in executions:
            status = execution.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            total_tasks += len(execution.tasks)
            
            if execution.started_at and execution.completed_at:
                execution_time = (execution.completed_at - execution.started_at).total_seconds()
                total_execution_time += execution_time
                
            if execution.status == TaskStatus.COMPLETED:
                successful_executions += 1
        
        avg_execution_time = total_execution_time / max(1, successful_executions)
        avg_tasks_per_workflow = total_tasks / max(1, total)
        success_rate = successful_executions / total if total > 0 else 0
        
        return {
            "total": total,
            "status_counts": status_counts,
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "avg_tasks_per_workflow": avg_tasks_per_workflow,
            "total_tasks": total_tasks
        }
    
    def get_workflow_execution_summary(
        self,
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Get summary of a workflow execution"""
        duration = None
        if execution.started_at and execution.completed_at:
            duration = (execution.completed_at - execution.started_at).total_seconds()
        elif execution.started_at:
            duration = (execution.updated_at - execution.started_at).total_seconds()
        
        return {
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "task_count": len(execution.tasks),
            "duration": duration,
            "created_at": execution.created_at,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "context_keys": list(execution.context.keys()) if execution.context else []
        }