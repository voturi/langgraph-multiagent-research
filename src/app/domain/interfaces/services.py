"""Service interfaces - Abstract external service interfaces"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator

from ..models.value_objects import ExecutionResult, ToolDefinition, AgentCapability


class LLMService(ABC):
    """Language model service interface"""
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, Any]], 
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        **kwargs
    ) -> ExecutionResult:
        """Generate response from messages"""
        pass
    
    @abstractmethod
    async def generate_streaming(
        self,
        messages: List[Dict[str, Any]],
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        pass
    
    @abstractmethod
    async def embed_text(self, text: str, model: str = None) -> ExecutionResult:
        """Generate text embeddings"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass


class ToolService(ABC):
    """Tool execution service interface"""
    
    @abstractmethod
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> ExecutionResult:
        """Execute a tool with parameters"""
        pass
    
    @abstractmethod
    def get_available_tools(self) -> List[ToolDefinition]:
        """Get list of available tools"""
        pass
    
    @abstractmethod
    def register_tool(self, tool_definition: ToolDefinition, handler: callable) -> None:
        """Register a new tool"""
        pass


class NotificationService(ABC):
    """Notification service interface"""
    
    @abstractmethod
    async def send_notification(
        self,
        recipient: str,
        message: str,
        channel: str = "email",
        metadata: Dict[str, Any] = None
    ) -> ExecutionResult:
        """Send notification to recipient"""
        pass
    
    @abstractmethod
    async def broadcast_notification(
        self,
        recipients: List[str],
        message: str, 
        channel: str = "email",
        metadata: Dict[str, Any] = None
    ) -> ExecutionResult:
        """Broadcast notification to multiple recipients"""
        pass


class CacheService(ABC):
    """Cache service interface"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache with TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache"""
        pass


class SchedulerService(ABC):
    """Task scheduler service interface"""
    
    @abstractmethod
    async def schedule_task(
        self,
        task_id: str,
        execute_at: float,  # Unix timestamp
        payload: Dict[str, Any]
    ) -> None:
        """Schedule task for future execution"""
        pass
    
    @abstractmethod
    async def cancel_task(self, task_id: str) -> None:
        """Cancel scheduled task"""
        pass


class AgentService(ABC):
    """Agent service interface"""
    
    @abstractmethod
    async def execute_agent(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> ExecutionResult:
        """Execute an agent with input data"""
        pass
    
    @abstractmethod
    def get_agent_capabilities(self, agent_name: str) -> List[AgentCapability]:
        """Get agent capabilities"""
        pass
    
    @abstractmethod
    def get_available_agents(self) -> List[str]:
        """Get list of available agents"""
        pass


class WorkflowService(ABC):
    """Workflow orchestration service interface"""
    
    @abstractmethod
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> ExecutionResult:
        """Execute a workflow"""
        pass
    
    @abstractmethod
    async def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        pass
    
    @abstractmethod
    async def cancel_workflow(self, execution_id: str) -> None:
        """Cancel workflow execution"""
        pass


class SearchService(ABC):
    """Search service interface"""
    
    @abstractmethod
    async def search(
        self,
        query: str,
        index: str = "default",
        filters: Dict[str, Any] = None,
        limit: int = 10
    ) -> ExecutionResult:
        """Search for documents"""
        pass
    
    @abstractmethod
    async def index_document(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any] = None,
        index: str = "default"
    ) -> None:
        """Index a document"""
        pass


class FileService(ABC):
    """File service interface"""
    
    @abstractmethod
    async def upload_file(
        self,
        file_path: str,
        content: bytes,
        content_type: str = "application/octet-stream"
    ) -> ExecutionResult:
        """Upload file"""
        pass
    
    @abstractmethod
    async def download_file(self, file_path: str) -> ExecutionResult:
        """Download file"""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> None:
        """Delete file"""
        pass