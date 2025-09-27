"""Domain entities - Business objects with identity"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .value_objects import (
    ConversationId,
    MessageContent,
    MessageId,
    TaskId,
    TaskStatus,
    UserId,
    WorkflowId,
)


class BaseEntity(BaseModel):
    """Base class for all entities"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        # Use enum values for serialization
        "use_enum_values": True,
        # Validate assignment
        "validate_assignment": True,
    }


class User(BaseEntity):
    """User entity"""

    id: UserId
    name: str
    email: str
    preferences: Dict[str, Any] = Field(default_factory=dict)

    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences"""
        self.preferences.update(preferences)
        self.updated_at = datetime.utcnow()


class Message(BaseEntity):
    """Message entity"""

    id: MessageId
    conversation_id: ConversationId
    content: MessageContent
    role: str  # "user", "assistant", "system", "tool"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_from_user(self) -> bool:
        """Check if message is from user"""
        return self.role == "user"

    def is_from_assistant(self) -> bool:
        """Check if message is from assistant"""
        return self.role == "assistant"


class Conversation(BaseEntity):
    """Conversation entity"""

    id: ConversationId
    user_id: UserId
    title: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

    def add_message(self, message: Message) -> None:
        """Add message to conversation"""
        if message.conversation_id != self.id:
            raise ValueError("Message conversation_id must match conversation id")
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get recent messages"""
        return self.messages[-limit:]

    def close(self) -> None:
        """Close the conversation"""
        self.is_active = False
        self.updated_at = datetime.utcnow()


class Task(BaseEntity):
    """Task entity"""

    id: TaskId
    name: str
    description: str
    status: TaskStatus
    user_id: UserId
    conversation_id: Optional[ConversationId] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def start(self) -> None:
        """Start the task"""
        if self.status != TaskStatus.PENDING:
            raise ValueError(f"Cannot start task with status {self.status}")
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self, output_data: Dict[str, Any]) -> None:
        """Complete the task"""
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot complete task with status {self.status}")
        self.status = TaskStatus.COMPLETED
        self.output_data = output_data
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def fail(self, error_message: str) -> None:
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_finished(self) -> bool:
        """Check if task is finished"""
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]


class WorkflowExecution(BaseEntity):
    """Workflow execution entity"""

    id: str
    workflow_id: WorkflowId
    user_id: UserId
    conversation_id: Optional[ConversationId] = None
    tasks: List[TaskId] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    context: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def add_task(self, task_id: TaskId) -> None:
        """Add task to workflow"""
        self.tasks.append(task_id)
        self.updated_at = datetime.utcnow()

    def start(self) -> None:
        """Start workflow execution"""
        if self.status != TaskStatus.PENDING:
            raise ValueError(f"Cannot start workflow with status {self.status}")
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Complete workflow execution"""
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot complete workflow with status {self.status}")
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def fail(self) -> None:
        """Mark workflow as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
