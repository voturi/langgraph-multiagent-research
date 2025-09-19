"""Conversation domain service - Framework-agnostic business logic"""

from typing import List, Optional
import logging

from ..models.entities import Conversation, Message
from ..models.value_objects import UserId, ConversationId, MessageId, MessageContent
from ..models.events import ConversationStarted, MessageReceived, MessageSent
from ..interfaces.repositories import UnitOfWork
from ..interfaces.events import EventPublisher

logger = logging.getLogger(__name__)


class ConversationService:
    """Domain service for conversation business logic"""
    
    def __init__(self, event_publisher: EventPublisher):
        self.event_publisher = event_publisher
    
    async def start_conversation(
        self,
        uow: UnitOfWork,
        user_id: UserId,
        title: Optional[str] = None
    ) -> Conversation:
        """Start a new conversation"""
        async with uow:
            # Create new conversation
            conversation = Conversation(
                id=ConversationId(f"conv_{user_id}_{int(__import__('time').time())}"),
                user_id=user_id,
                title=title or "New Conversation"
            )
            
            # Save to repository
            await uow.conversations.save(conversation)
            await uow.commit()
            
            # Publish event
            event = ConversationStarted(
                aggregate_id=conversation.id,
                user_id=user_id,
                title=conversation.title
            )
            await self.event_publisher.publish(event)
            
            logger.info(f"Started conversation {conversation.id} for user {user_id}")
            return conversation
    
    async def get_conversation(
        self,
        uow: UnitOfWork,
        conversation_id: ConversationId
    ) -> Optional[Conversation]:
        """Get conversation by ID"""
        async with uow:
            return await uow.conversations.find_by_id(conversation_id)
    
    async def get_user_conversations(
        self,
        uow: UnitOfWork,
        user_id: UserId,
        active_only: bool = False,
        limit: int = 50
    ) -> List[Conversation]:
        """Get conversations for a user"""
        async with uow:
            if active_only:
                return await uow.conversations.find_active_by_user_id(user_id)
            else:
                return await uow.conversations.find_by_user_id(user_id, limit)
    
    async def add_message_to_conversation(
        self,
        uow: UnitOfWork,
        conversation_id: ConversationId,
        content: str,
        role: str = "user",
        metadata: dict = None
    ) -> Message:
        """Add a message to a conversation"""
        async with uow:
            # Get conversation
            conversation = await uow.conversations.find_by_id(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            if not conversation.is_active:
                raise ValueError(f"Conversation {conversation_id} is not active")
            
            # Create message
            message_content = MessageContent(text=content, metadata=metadata or {})
            message = Message(
                id=MessageId(f"msg_{conversation_id}_{int(__import__('time').time())}"),
                conversation_id=conversation_id,
                content=message_content,
                role=role,
                metadata=metadata or {}
            )
            
            # Add to conversation
            conversation.add_message(message)
            
            # Save both
            await uow.messages.save(message)
            await uow.conversations.save(conversation)
            await uow.commit()
            
            # Publish event
            if role == "user":
                event = MessageReceived(
                    aggregate_id=message.id,
                    conversation_id=conversation_id,
                    user_id=conversation.user_id,
                    content=content,
                    role=role
                )
            else:
                event = MessageSent(
                    aggregate_id=message.id,
                    conversation_id=conversation_id,
                    content=content,
                    role=role
                )
            
            await self.event_publisher.publish(event)
            
            logger.info(f"Added {role} message to conversation {conversation_id}")
            return message
    
    async def close_conversation(
        self,
        uow: UnitOfWork,
        conversation_id: ConversationId
    ) -> None:
        """Close a conversation"""
        async with uow:
            conversation = await uow.conversations.find_by_id(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            conversation.close()
            await uow.conversations.save(conversation)
            await uow.commit()
            
            logger.info(f"Closed conversation {conversation_id}")
    
    async def get_conversation_messages(
        self,
        uow: UnitOfWork,
        conversation_id: ConversationId,
        limit: int = 100
    ) -> List[Message]:
        """Get messages for a conversation"""
        async with uow:
            return await uow.messages.find_by_conversation_id(
                conversation_id, limit=limit
            )
    
    def calculate_conversation_summary(self, conversation: Conversation) -> dict:
        """Calculate conversation summary statistics"""
        total_messages = len(conversation.messages)
        user_messages = len([m for m in conversation.messages if m.is_from_user()])
        assistant_messages = len([m for m in conversation.messages if m.is_from_assistant()])
        
        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "is_active": conversation.is_active,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at
        }