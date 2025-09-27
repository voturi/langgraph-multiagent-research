"""Domain value objects - Immutable objects that represent values"""

from enum import Enum
from typing import NewType

from pydantic import BaseModel, Field, validator

# ID Types - Type-safe identifiers
UserId = NewType("UserId", str)
ConversationId = NewType("ConversationId", str)
MessageId = NewType("MessageId", str)
TaskId = NewType("TaskId", str)
WorkflowId = NewType("WorkflowId", str)


class TaskStatus(str, Enum):
    """Task execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageContent(BaseModel):
    """Message content value object"""

    text: str
    content_type: str = "text"
    metadata: dict = Field(default_factory=dict)

    @validator("text")
    def text_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Message text cannot be empty")
        return v.strip()

    def __str__(self) -> str:
        return self.text

    class Config:
        # Value objects are immutable
        allow_mutation = False


class WorkflowDefinition(BaseModel):
    """Workflow definition value object"""

    id: WorkflowId
    name: str
    description: str
    steps: list = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    class Config:
        allow_mutation = False


class ExecutionContext(BaseModel):
    """Execution context value object"""

    user_id: UserId
    conversation_id: ConversationId
    session_id: str
    parameters: dict = Field(default_factory=dict)

    class Config:
        allow_mutation = False


class ExecutionResult(BaseModel):
    """Execution result value object"""

    success: bool
    data: dict = Field(default_factory=dict)
    error_message: str = None
    execution_time: float = 0.0
    metadata: dict = Field(default_factory=dict)

    @classmethod
    def success_result(
        cls, data: dict = None, execution_time: float = 0.0
    ) -> "ExecutionResult":
        """Create successful result"""
        return cls(success=True, data=data or {}, execution_time=execution_time)

    @classmethod
    def error_result(
        cls, error_message: str, execution_time: float = 0.0
    ) -> "ExecutionResult":
        """Create error result"""
        return cls(
            success=False, error_message=error_message, execution_time=execution_time
        )

    class Config:
        allow_mutation = False


class AgentCapability(BaseModel):
    """Agent capability value object"""

    name: str
    description: str
    parameters: dict = Field(default_factory=dict)

    class Config:
        allow_mutation = False


class ToolDefinition(BaseModel):
    """Tool definition value object"""

    name: str
    description: str
    input_schema: dict
    output_schema: dict = Field(default_factory=dict)

    class Config:
        allow_mutation = False
