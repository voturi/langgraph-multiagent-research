"""Message domain service - Framework-agnostic business logic"""

from typing import List, Optional, Dict, Any
import logging

from ..models.entities import Message
from ..models.value_objects import (
    UserId, ConversationId, MessageId, MessageContent
)
from ..interfaces.repositories import UnitOfWork

logger = logging.getLogger(__name__)


class MessageService:
    """Domain service for message business logic"""
    
    def __init__(self):
        pass
    
    async def get_message(
        self,
        uow: UnitOfWork,
        message_id: MessageId
    ) -> Optional[Message]:
        """Get message by ID"""
        async with uow:
            return await uow.messages.find_by_id(message_id)
    
    async def get_conversation_messages(
        self,
        uow: UnitOfWork,
        conversation_id: ConversationId,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """Get messages for a conversation with pagination"""
        async with uow:
            return await uow.messages.find_by_conversation_id(
                conversation_id, limit=limit, offset=offset
            )
    
    def format_messages_for_llm(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Format messages for LLM consumption"""
        formatted = []
        
        for message in messages:
            formatted.append({
                "role": message.role,
                "content": str(message.content),
                "metadata": message.metadata
            })
        
        return formatted
    
    def filter_messages_by_role(
        self, 
        messages: List[Message], 
        role: str
    ) -> List[Message]:
        """Filter messages by role"""
        return [msg for msg in messages if msg.role == role]
    
    def get_recent_user_messages(
        self, 
        messages: List[Message], 
        limit: int = 5
    ) -> List[Message]:
        """Get recent user messages"""
        user_messages = self.filter_messages_by_role(messages, "user")
        return user_messages[-limit:] if user_messages else []
    
    def calculate_message_statistics(self, messages: List[Message]) -> Dict[str, Any]:
        """Calculate message statistics"""
        if not messages:
            return {"total": 0}
        
        role_counts = {}
        total_length = 0
        
        for message in messages:
            role = message.role
            role_counts[role] = role_counts.get(role, 0) + 1
            total_length += len(str(message.content))
        
        avg_length = total_length / len(messages)
        
        return {
            "total": len(messages),
            "role_counts": role_counts,
            "avg_message_length": avg_length,
            "total_content_length": total_length,
            "first_message_time": messages[0].created_at if messages else None,
            "last_message_time": messages[-1].created_at if messages else None
        }
    
    def extract_conversation_context(
        self, 
        messages: List[Message], 
        max_context_length: int = 4000
    ) -> str:
        """Extract conversation context up to max length"""
        context_parts = []
        current_length = 0
        
        # Start from most recent messages
        for message in reversed(messages):
            content = f"{message.role}: {str(message.content)}"
            
            if current_length + len(content) > max_context_length:
                break
                
            context_parts.insert(0, content)
            current_length += len(content)
        
        return "\n".join(context_parts)
    
    def find_messages_with_keywords(
        self, 
        messages: List[Message], 
        keywords: List[str]
    ) -> List[Message]:
        """Find messages containing any of the keywords"""
        matching_messages = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for message in messages:
            content_lower = str(message.content).lower()
            if any(keyword in content_lower for keyword in keywords_lower):
                matching_messages.append(message)
        
        return matching_messages
    
    def group_messages_by_role(self, messages: List[Message]) -> Dict[str, List[Message]]:
        """Group messages by role"""
        groups = {}
        
        for message in messages:
            role = message.role
            if role not in groups:
                groups[role] = []
            groups[role].append(message)
        
        return groups