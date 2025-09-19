"""Conversation workflow - Framework-agnostic conversation handling"""

from typing import Dict, Any, Optional, List
import logging
import time

from .base import WorkflowOrchestrator
from ...domain.models.value_objects import ExecutionResult, ExecutionContext
from ...domain.models.entities import Conversation, Message
from ...domain.interfaces.services import LLMService, ToolService

logger = logging.getLogger(__name__)


class ConversationWorkflow(WorkflowOrchestrator):
    """Framework-agnostic conversation workflow implementation
    
    This handles conversation logic without depending on LangGraph.
    It can be easily adapted to use any orchestration framework.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        tool_service: Optional[ToolService] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.llm_service = llm_service
        self.tool_service = tool_service
        
    async def execute_workflow(
        self,
        workflow_name: str,
        context: ExecutionContext,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute conversation workflow"""
        start_time = time.time()
        
        try:
            # Validate context
            if not await self._validate_context(context):
                return self._create_error_result("Invalid execution context")
            
            # Route to specific workflow
            if workflow_name == "simple_chat":
                result = await self._execute_simple_chat(context, input_data)
            elif workflow_name == "chat_with_tools":
                result = await self._execute_chat_with_tools(context, input_data)
            elif workflow_name == "multi_turn_conversation":
                result = await self._execute_multi_turn_conversation(context, input_data)
            else:
                return self._create_error_result(f"Unknown workflow: {workflow_name}")
            
            execution_time = time.time() - start_time
            await self._log_workflow_completion(workflow_name, context.session_id, result.success, execution_time)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Workflow {workflow_name} failed: {e}")
            return self._create_error_result(str(e), execution_time)
    
    async def _execute_simple_chat(
        self,
        context: ExecutionContext,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute simple chat workflow"""
        user_message = input_data.get("message", "")
        if not user_message:
            return self._create_error_result("Message is required")
        
        try:
            # Get or create conversation
            conversation = await self._get_or_create_conversation(context)
            
            # Add user message
            await self.conversation_service.add_message_to_conversation(
                self.uow, conversation.id, user_message, "user"
            )
            
            # Get conversation history
            messages = await self.message_service.get_conversation_messages(
                self.uow, conversation.id, limit=10
            )
            
            # Format for LLM
            llm_messages = self.message_service.format_messages_for_llm(messages)
            
            # Get LLM response
            llm_result = await self.llm_service.generate_response(llm_messages)
            
            if not llm_result.success:
                return self._create_error_result(llm_result.error_message)
            
            assistant_response = llm_result.data.get("content", "")
            
            # Add assistant message
            assistant_message = await self.conversation_service.add_message_to_conversation(
                self.uow, conversation.id, assistant_response, "assistant"
            )
            
            return self._create_success_result({
                "conversation_id": conversation.id,
                "message_id": assistant_message.id,
                "response": assistant_response,
                "message_count": len(messages) + 2  # +2 for new user and assistant messages
            })
            
        except Exception as e:
            return self._create_error_result(f"Simple chat failed: {e}")
    
    async def _execute_chat_with_tools(
        self,
        context: ExecutionContext,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute chat with tools workflow"""
        if not self.tool_service:
            return self._create_error_result("Tool service not available")
        
        user_message = input_data.get("message", "")
        if not user_message:
            return self._create_error_result("Message is required")
        
        try:
            # Get or create conversation
            conversation = await self._get_or_create_conversation(context)
            
            # Add user message
            await self.conversation_service.add_message_to_conversation(
                self.uow, conversation.id, user_message, "user"
            )
            
            # Get conversation history
            messages = await self.message_service.get_conversation_messages(
                self.uow, conversation.id, limit=10
            )
            
            # Format for LLM with tool schemas
            llm_messages = self.message_service.format_messages_for_llm(messages)
            available_tools = self.tool_service.get_available_tools()
            
            # Get LLM response with potential tool calls
            llm_result = await self.llm_service.generate_response(
                llm_messages,
                tools=[tool.dict() for tool in available_tools]
            )
            
            if not llm_result.success:
                return self._create_error_result(llm_result.error_message)
            
            # Process tool calls if any
            tool_results = []
            if "tool_calls" in llm_result.data:
                for tool_call in llm_result.data["tool_calls"]:
                    tool_result = await self.tool_service.execute_tool(
                        tool_call["name"],
                        tool_call["parameters"],
                        {"conversation_id": conversation.id, "user_id": context.user_id}
                    )
                    tool_results.append(tool_result)
            
            # Generate final response incorporating tool results
            assistant_response = llm_result.data.get("content", "")
            if tool_results:
                # Add tool results to context for final response
                tool_context = "\n".join([
                    f"Tool {i+1} result: {result.data}" 
                    for i, result in enumerate(tool_results) if result.success
                ])
                if tool_context:
                    assistant_response = f"{assistant_response}\n\nBased on the tool results:\n{tool_context}"
            
            # Add assistant message
            assistant_message = await self.conversation_service.add_message_to_conversation(
                self.uow, conversation.id, assistant_response, "assistant"
            )
            
            return self._create_success_result({
                "conversation_id": conversation.id,
                "message_id": assistant_message.id,
                "response": assistant_response,
                "tool_calls": len(tool_results),
                "tools_used": [result.data.get("tool_name") for result in tool_results if result.success]
            })
            
        except Exception as e:
            return self._create_error_result(f"Chat with tools failed: {e}")
    
    async def _execute_multi_turn_conversation(
        self,
        context: ExecutionContext,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute multi-turn conversation workflow"""
        messages = input_data.get("messages", [])
        if not messages:
            return self._create_error_result("Messages are required")
        
        try:
            # Get or create conversation
            conversation = await self._get_or_create_conversation(context)
            
            results = []
            
            # Process each message in sequence
            for msg in messages:
                if not isinstance(msg, dict) or "content" not in msg:
                    continue
                
                role = msg.get("role", "user")
                content = msg["content"]
                
                # Add message to conversation
                message = await self.conversation_service.add_message_to_conversation(
                    self.uow, conversation.id, content, role
                )
                
                # If it's a user message, generate assistant response
                if role == "user":
                    # Get recent conversation history
                    recent_messages = await self.message_service.get_conversation_messages(
                        self.uow, conversation.id, limit=20
                    )
                    
                    # Format for LLM
                    llm_messages = self.message_service.format_messages_for_llm(recent_messages)
                    
                    # Get LLM response
                    llm_result = await self.llm_service.generate_response(llm_messages)
                    
                    if llm_result.success:
                        assistant_response = llm_result.data.get("content", "")
                        
                        # Add assistant message
                        assistant_message = await self.conversation_service.add_message_to_conversation(
                            self.uow, conversation.id, assistant_response, "assistant"
                        )
                        
                        results.append({
                            "user_message_id": message.id,
                            "assistant_message_id": assistant_message.id,
                            "assistant_response": assistant_response
                        })
            
            return self._create_success_result({
                "conversation_id": conversation.id,
                "processed_exchanges": len(results),
                "exchanges": results
            })
            
        except Exception as e:
            return self._create_error_result(f"Multi-turn conversation failed: {e}")
    
    async def _get_or_create_conversation(self, context: ExecutionContext) -> Conversation:
        """Get existing conversation or create new one"""
        if context.conversation_id:
            conversation = await self.conversation_service.get_conversation(
                self.uow, context.conversation_id
            )
            if conversation:
                return conversation
        
        # Create new conversation
        return await self.conversation_service.start_conversation(
            self.uow, context.user_id, "New Conversation"
        )
    
    async def get_available_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Get available conversation workflows"""
        workflows = {
            "simple_chat": {
                "description": "Simple chat with LLM",
                "required_inputs": ["message"],
                "optional_inputs": [],
                "supports_tools": False
            },
            "chat_with_tools": {
                "description": "Chat with tool support",
                "required_inputs": ["message"],
                "optional_inputs": [],
                "supports_tools": True,
                "available": bool(self.tool_service)
            },
            "multi_turn_conversation": {
                "description": "Process multiple messages in sequence",
                "required_inputs": ["messages"],
                "optional_inputs": [],
                "supports_tools": False
            }
        }
        
        return workflows
    
    async def cancel_workflow_execution(self, execution_id: str) -> bool:
        """Cancel workflow execution (simple implementation)"""
        # In a real implementation, you'd track running executions
        # For now, return True as most conversation workflows are quick
        logger.info(f"Cancellation requested for execution {execution_id}")
        return True
    
    async def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        # In a real implementation, you'd track execution status
        # For now, return None as conversations are typically synchronous
        return None