"""Domain events - Events that occur in the domain"""

from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from pydantic import BaseModel, Field

from .value_objects import ConversationId, MessageId, TaskId, UserId, WorkflowId


class DomainEvent(BaseModel):
    """Base class for domain events"""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    aggregate_id: str
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        allow_mutation = False


class ConversationStarted(DomainEvent):
    """Event fired when a conversation starts"""

    event_type: str = "ConversationStarted"
    aggregate_id: ConversationId
    user_id: UserId
    title: str = None


class MessageReceived(DomainEvent):
    """Event fired when a message is received"""

    event_type: str = "MessageReceived"
    aggregate_id: MessageId
    conversation_id: ConversationId
    user_id: UserId
    content: str
    role: str


class MessageSent(DomainEvent):
    """Event fired when a message is sent"""

    event_type: str = "MessageSent"
    aggregate_id: MessageId
    conversation_id: ConversationId
    content: str
    role: str


class TaskStarted(DomainEvent):
    """Event fired when a task starts"""

    event_type: str = "TaskStarted"
    aggregate_id: TaskId
    user_id: UserId
    task_name: str
    conversation_id: ConversationId = None


class TaskCompleted(DomainEvent):
    """Event fired when a task completes"""

    event_type: str = "TaskCompleted"
    aggregate_id: TaskId
    user_id: UserId
    task_name: str
    success: bool
    result_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: str = None


class WorkflowStarted(DomainEvent):
    """Event fired when a workflow starts"""

    event_type: str = "WorkflowStarted"
    aggregate_id: str  # WorkflowExecution ID
    workflow_id: WorkflowId
    user_id: UserId
    conversation_id: ConversationId = None


class WorkflowFinished(DomainEvent):
    """Event fired when a workflow finishes"""

    event_type: str = "WorkflowFinished"
    aggregate_id: str  # WorkflowExecution ID
    workflow_id: WorkflowId
    user_id: UserId
    success: bool
    execution_time: float = 0.0
