"""User domain service - Framework-agnostic business logic"""

from typing import List, Optional, Dict, Any
import logging

from ..models.entities import User
from ..models.value_objects import UserId
from ..interfaces.repositories import UnitOfWork

logger = logging.getLogger(__name__)


class UserService:
    """Domain service for user business logic"""
    
    def __init__(self):
        pass
    
    async def create_user(
        self,
        uow: UnitOfWork,
        name: str,
        email: str,
        preferences: Dict[str, Any] = None
    ) -> User:
        """Create a new user"""
        async with uow:
            # Check if user with email already exists
            existing_user = await uow.users.find_by_email(email)
            if existing_user:
                raise ValueError(f"User with email {email} already exists")
            
            user = User(
                id=UserId(f"user_{hash(email) % 1000000}_{int(__import__('time').time())}"),
                name=name,
                email=email,
                preferences=preferences or {}
            )
            
            await uow.users.save(user)
            await uow.commit()
            
            logger.info(f"Created user {user.id}: {email}")
            return user
    
    async def get_user(
        self,
        uow: UnitOfWork,
        user_id: UserId
    ) -> Optional[User]:
        """Get user by ID"""
        async with uow:
            return await uow.users.find_by_id(user_id)
    
    async def get_user_by_email(
        self,
        uow: UnitOfWork,
        email: str
    ) -> Optional[User]:
        """Get user by email"""
        async with uow:
            return await uow.users.find_by_email(email)
    
    async def update_user_preferences(
        self,
        uow: UnitOfWork,
        user_id: UserId,
        preferences: Dict[str, Any]
    ) -> User:
        """Update user preferences"""
        async with uow:
            user = await uow.users.find_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            user.update_preferences(preferences)
            await uow.users.save(user)
            await uow.commit()
            
            logger.info(f"Updated preferences for user {user_id}")
            return user
    
    async def delete_user(
        self,
        uow: UnitOfWork,
        user_id: UserId
    ) -> None:
        """Delete a user"""
        async with uow:
            user = await uow.users.find_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            await uow.users.delete(user_id)
            await uow.commit()
            
            logger.info(f"Deleted user {user_id}")
    
    def get_user_preference(
        self,
        user: User,
        key: str,
        default: Any = None
    ) -> Any:
        """Get specific user preference"""
        return user.preferences.get(key, default)
    
    def set_user_preference(
        self,
        user: User,
        key: str,
        value: Any
    ) -> None:
        """Set specific user preference"""
        preferences = user.preferences.copy()
        preferences[key] = value
        user.update_preferences(preferences)
    
    def get_user_summary(self, user: User) -> Dict[str, Any]:
        """Get user summary"""
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "preference_count": len(user.preferences),
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_user_data(
        self,
        name: str,
        email: str
    ) -> List[str]:
        """Validate user data and return list of errors"""
        errors = []
        
        if not name or not name.strip():
            errors.append("Name cannot be empty")
        elif len(name.strip()) < 2:
            errors.append("Name must be at least 2 characters long")
        
        if not email or not email.strip():
            errors.append("Email cannot be empty")
        elif not self.validate_email(email.strip()):
            errors.append("Invalid email format")
        
        return errors