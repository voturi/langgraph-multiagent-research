"""Task domain service - Framework-agnostic business logic"""

from typing import List, Optional, Dict, Any
import logging
import time

from ..models.entities import Task
from ..models.value_objects import (
    UserId, ConversationId, TaskId, TaskStatus, ExecutionResult
)
from ..models.events import TaskStarted, TaskCompleted
from ..interfaces.repositories import UnitOfWork
from ..interfaces.events import EventPublisher

logger = logging.getLogger(__name__)


class TaskService:
    """Domain service for task business logic"""
    
    def __init__(self, event_publisher: EventPublisher):
        self.event_publisher = event_publisher
    
    async def create_task(
        self,
        uow: UnitOfWork,
        name: str,
        description: str,
        user_id: UserId,
        conversation_id: Optional[ConversationId] = None,
        input_data: Dict[str, Any] = None
    ) -> Task:
        """Create a new task"""
        async with uow:
            task = Task(
                id=TaskId(f"task_{user_id}_{int(time.time())}_{hash(name) % 10000}"),
                name=name,
                description=description,
                status=TaskStatus.PENDING,
                user_id=user_id,
                conversation_id=conversation_id,
                input_data=input_data or {}
            )
            
            await uow.tasks.save(task)
            await uow.commit()
            
            logger.info(f"Created task {task.id}: {name}")
            return task
    
    async def start_task(
        self,
        uow: UnitOfWork,
        task_id: TaskId
    ) -> Task:
        """Start a task"""
        async with uow:
            task = await uow.tasks.find_by_id(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            task.start()
            await uow.tasks.save(task)
            await uow.commit()
            
            # Publish event
            event = TaskStarted(
                aggregate_id=task_id,
                user_id=task.user_id,
                task_name=task.name,
                conversation_id=task.conversation_id
            )
            await self.event_publisher.publish(event)
            
            logger.info(f"Started task {task_id}")
            return task
    
    async def complete_task(
        self,
        uow: UnitOfWork,
        task_id: TaskId,
        output_data: Dict[str, Any],
        success: bool = True,
        error_message: Optional[str] = None
    ) -> Task:
        """Complete a task"""
        async with uow:
            task = await uow.tasks.find_by_id(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            if success:
                task.complete(output_data)
            else:
                task.fail(error_message or "Task failed")
            
            await uow.tasks.save(task)
            await uow.commit()
            
            # Publish event
            event = TaskCompleted(
                aggregate_id=task_id,
                user_id=task.user_id,
                task_name=task.name,
                success=success,
                result_data=output_data if success else {},
                error_message=error_message
            )
            await self.event_publisher.publish(event)
            
            status = "completed" if success else "failed"
            logger.info(f"Task {task_id} {status}")
            return task
    
    async def get_task(
        self,
        uow: UnitOfWork,
        task_id: TaskId
    ) -> Optional[Task]:
        """Get task by ID"""
        async with uow:
            return await uow.tasks.find_by_id(task_id)
    
    async def get_user_tasks(
        self,
        uow: UnitOfWork,
        user_id: UserId,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[Task]:
        """Get tasks for a user"""
        async with uow:
            if status:
                # Get all tasks by status then filter by user
                all_status_tasks = await uow.tasks.find_by_status(status, limit * 2)
                return [t for t in all_status_tasks if t.user_id == user_id][:limit]
            else:
                return await uow.tasks.find_by_user_id(user_id, limit)
    
    async def get_conversation_tasks(
        self,
        uow: UnitOfWork,
        conversation_id: ConversationId
    ) -> List[Task]:
        """Get tasks for a conversation"""
        async with uow:
            return await uow.tasks.find_by_conversation_id(conversation_id)
    
    async def cancel_task(
        self,
        uow: UnitOfWork,
        task_id: TaskId,
        reason: str = "Cancelled by user"
    ) -> Task:
        """Cancel a task"""
        async with uow:
            task = await uow.tasks.find_by_id(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            if task.is_finished():
                raise ValueError(f"Cannot cancel finished task {task_id}")
            
            task.status = TaskStatus.CANCELLED
            task.error_message = reason
            task.completed_at = task.updated_at
            
            await uow.tasks.save(task)
            await uow.commit()
            
            logger.info(f"Cancelled task {task_id}: {reason}")
            return task
    
    def calculate_task_metrics(self, tasks: List[Task]) -> Dict[str, Any]:
        """Calculate task metrics"""
        total = len(tasks)
        if total == 0:
            return {"total": 0}
        
        status_counts = {}
        total_execution_time = 0
        successful_tasks = 0
        
        for task in tasks:
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if task.started_at and task.completed_at:
                execution_time = (task.completed_at - task.started_at).total_seconds()
                total_execution_time += execution_time
                
            if task.status == TaskStatus.COMPLETED:
                successful_tasks += 1
        
        avg_execution_time = total_execution_time / max(1, successful_tasks)
        success_rate = successful_tasks / total if total > 0 else 0
        
        return {
            "total": total,
            "status_counts": status_counts,
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "total_execution_time": total_execution_time
        }
    
    def validate_task_transition(
        self,
        current_status: TaskStatus,
        new_status: TaskStatus
    ) -> bool:
        """Validate if status transition is allowed"""
        allowed_transitions = {
            TaskStatus.PENDING: [TaskStatus.RUNNING, TaskStatus.CANCELLED],
            TaskStatus.RUNNING: [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED],
            TaskStatus.COMPLETED: [],
            TaskStatus.FAILED: [],
            TaskStatus.CANCELLED: []
        }
        
        return new_status in allowed_transitions.get(current_status, [])