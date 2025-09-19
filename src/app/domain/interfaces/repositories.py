"""Repository interfaces - Abstract data access layer"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..models.entities import User, Conversation, Message, Task, WorkflowExecution
from ..models.value_objects import (
    UserId, ConversationId, MessageId, TaskId, WorkflowId, TaskStatus
)


class BaseRepository(ABC):
    """Base repository interface"""
    
    @abstractmethod
    async def save(self, entity) -> None:
        """Save entity"""
        pass
    
    @abstractmethod 
    async def delete(self, entity_id: str) -> None:
        """Delete entity by ID"""
        pass


class UserRepository(BaseRepository):
    """User repository interface"""
    
    @abstractmethod
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Find user by ID"""
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        pass
    
    @abstractmethod
    async def save(self, user: User) -> None:
        """Save user"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: UserId) -> None:
        """Delete user"""
        pass


class ConversationRepository(BaseRepository):
    """Conversation repository interface"""
    
    @abstractmethod
    async def find_by_id(self, conversation_id: ConversationId) -> Optional[Conversation]:
        """Find conversation by ID"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: UserId, limit: int = 50) -> List[Conversation]:
        """Find conversations by user ID"""
        pass
    
    @abstractmethod
    async def find_active_by_user_id(self, user_id: UserId) -> List[Conversation]:
        """Find active conversations by user ID"""
        pass
    
    @abstractmethod
    async def save(self, conversation: Conversation) -> None:
        """Save conversation"""
        pass
    
    @abstractmethod
    async def delete(self, conversation_id: ConversationId) -> None:
        """Delete conversation"""
        pass


class MessageRepository(BaseRepository):
    """Message repository interface"""
    
    @abstractmethod
    async def find_by_id(self, message_id: MessageId) -> Optional[Message]:
        """Find message by ID"""
        pass
    
    @abstractmethod
    async def find_by_conversation_id(
        self, 
        conversation_id: ConversationId,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """Find messages by conversation ID"""
        pass
    
    @abstractmethod
    async def save(self, message: Message) -> None:
        """Save message"""
        pass
    
    @abstractmethod
    async def delete(self, message_id: MessageId) -> None:
        """Delete message"""
        pass


class TaskRepository(BaseRepository):
    """Task repository interface"""
    
    @abstractmethod
    async def find_by_id(self, task_id: TaskId) -> Optional[Task]:
        """Find task by ID"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: UserId, limit: int = 100) -> List[Task]:
        """Find tasks by user ID"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: TaskStatus, limit: int = 100) -> List[Task]:
        """Find tasks by status"""
        pass
    
    @abstractmethod
    async def find_by_conversation_id(self, conversation_id: ConversationId) -> List[Task]:
        """Find tasks by conversation ID"""
        pass
    
    @abstractmethod
    async def save(self, task: Task) -> None:
        """Save task"""
        pass
    
    @abstractmethod
    async def delete(self, task_id: TaskId) -> None:
        """Delete task"""
        pass


class WorkflowRepository(BaseRepository):
    """Workflow execution repository interface"""
    
    @abstractmethod
    async def find_by_id(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Find workflow execution by ID"""
        pass
    
    @abstractmethod
    async def find_by_workflow_id(self, workflow_id: WorkflowId) -> List[WorkflowExecution]:
        """Find executions by workflow ID"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: UserId, limit: int = 100) -> List[WorkflowExecution]:
        """Find executions by user ID"""
        pass
    
    @abstractmethod
    async def find_active(self) -> List[WorkflowExecution]:
        """Find active workflow executions"""
        pass
    
    @abstractmethod
    async def save(self, execution: WorkflowExecution) -> None:
        """Save workflow execution"""
        pass
    
    @abstractmethod
    async def delete(self, execution_id: str) -> None:
        """Delete workflow execution"""
        pass


class UnitOfWork(ABC):
    """Unit of work interface for transactional operations"""
    
    @abstractmethod
    async def __aenter__(self):
        """Enter async context"""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context"""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit transaction"""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback transaction"""
        pass
    
    # Repository access
    @property
    @abstractmethod
    def users(self) -> UserRepository:
        pass
    
    @property
    @abstractmethod
    def conversations(self) -> ConversationRepository:
        pass
    
    @property
    @abstractmethod
    def messages(self) -> MessageRepository:
        pass
    
    @property
    @abstractmethod
    def tasks(self) -> TaskRepository:
        pass
    
    @property
    @abstractmethod
    def workflows(self) -> WorkflowRepository:
        pass