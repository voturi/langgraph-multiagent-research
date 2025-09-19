"""
Basic Usage Example - Framework-Agnostic Approach

This example shows how to use the domain services directly without
any orchestration framework. This demonstrates the core principle:
business logic should be completely independent of frameworks.
"""

import asyncio
import logging
from typing import Dict, Any

# Domain imports - these have no framework dependencies
from app.domain.services import (
    ConversationService, UserService, MessageService
)
from app.domain.models.value_objects import (
    UserId, ConversationId, ExecutionContext
)

# Mock implementations for this example
# In a real app, these would be in the infrastructure layer
class MockEventPublisher:
    async def publish(self, event):
        print(f"📢 Event published: {event.event_type}")

class MockUnitOfWork:
    def __init__(self):
        self.users = MockUserRepository()
        self.conversations = MockConversationRepository() 
        self.messages = MockMessageRepository()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def commit(self):
        print("💾 Transaction committed")
        
    async def rollback(self):
        print("↩️ Transaction rolled back")

class MockUserRepository:
    def __init__(self):
        self.users = {}
        
    async def find_by_id(self, user_id):
        return self.users.get(user_id)
        
    async def find_by_email(self, email):
        for user in self.users.values():
            if user.email == email:
                return user
        return None
        
    async def save(self, user):
        self.users[user.id] = user
        print(f"👤 Saved user: {user.email}")

class MockConversationRepository:
    def __init__(self):
        self.conversations = {}
        
    async def find_by_id(self, conversation_id):
        return self.conversations.get(conversation_id)
        
    async def find_by_user_id(self, user_id, limit=50):
        return [c for c in self.conversations.values() if c.user_id == user_id][:limit]
        
    async def find_active_by_user_id(self, user_id):
        return [c for c in self.conversations.values() 
                if c.user_id == user_id and c.is_active]
        
    async def save(self, conversation):
        self.conversations[conversation.id] = conversation
        print(f"💬 Saved conversation: {conversation.id}")

class MockMessageRepository:
    def __init__(self):
        self.messages = {}
        
    async def find_by_id(self, message_id):
        return self.messages.get(message_id)
        
    async def find_by_conversation_id(self, conversation_id, limit=100, offset=0):
        messages = [m for m in self.messages.values() 
                   if m.conversation_id == conversation_id]
        return messages[offset:offset + limit]
        
    async def save(self, message):
        self.messages[message.id] = message
        print(f"📝 Saved message: {message.role} - {str(message.content)[:50]}...")


async def main():
    """Demonstrate framework-agnostic domain usage"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Framework-Agnostic Domain Services Example")
    print("=" * 50)
    
    # Setup dependencies (normally done via DI container)
    event_publisher = MockEventPublisher()
    uow = MockUnitOfWork()
    
    # Create domain services - notice no framework dependencies!
    user_service = UserService()
    conversation_service = ConversationService(event_publisher)
    message_service = MessageService()
    
    try:
        # 1. Create a user
        print("\n1️⃣ Creating user...")
        user = await user_service.create_user(
            uow, 
            name="Alice Johnson",
            email="alice@example.com",
            preferences={"theme": "dark", "language": "en"}
        )
        
        # 2. Start a conversation
        print("\n2️⃣ Starting conversation...")
        conversation = await conversation_service.start_conversation(
            uow, 
            user.id,
            title="My First Conversation"
        )
        
        # 3. Add some messages
        print("\n3️⃣ Adding messages...")
        
        # User message
        user_message = await conversation_service.add_message_to_conversation(
            uow,
            conversation.id,
            "Hello! I'm interested in learning about clean architecture.",
            role="user"
        )
        
        # Assistant message (simulated)
        assistant_message = await conversation_service.add_message_to_conversation(
            uow,
            conversation.id,
            "Great question! Clean architecture is about separating concerns and keeping business logic independent of frameworks. This allows you to swap out infrastructure components without affecting your core business rules.",
            role="assistant"
        )
        
        # 4. Demonstrate business logic
        print("\n4️⃣ Analyzing conversation...")
        
        # Get conversation messages
        messages = await message_service.get_conversation_messages(
            uow, conversation.id
        )
        
        # Calculate statistics (pure business logic)
        stats = message_service.calculate_message_statistics(messages)
        print(f"📊 Message statistics: {stats}")
        
        # Get conversation summary (pure business logic)
        summary = conversation_service.calculate_conversation_summary(conversation)
        print(f"📋 Conversation summary: {summary}")
        
        # 5. Demonstrate domain rules
        print("\n5️⃣ Testing domain rules...")
        
        # User preferences
        theme = user_service.get_user_preference(user, "theme", "light")
        print(f"🎨 User theme preference: {theme}")
        
        # Message filtering
        user_messages = message_service.filter_messages_by_role(messages, "user")
        print(f"👤 User messages: {len(user_messages)}")
        
        assistant_messages = message_service.filter_messages_by_role(messages, "assistant") 
        print(f"🤖 Assistant messages: {len(assistant_messages)}")
        
        # Context extraction
        context = message_service.extract_conversation_context(messages, max_context_length=200)
        print(f"📄 Extracted context: {context[:100]}...")
        
        print("\n✅ Example completed successfully!")
        print("\n💡 Key Observations:")
        print("   • All business logic worked without any framework")
        print("   • Domain services are pure Python with clear interfaces")
        print("   • Easy to unit test (just mock the repositories)")
        print("   • Can swap infrastructure without changing business logic")
        print("   • LangGraph, FastAPI, etc. are just implementation details")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())