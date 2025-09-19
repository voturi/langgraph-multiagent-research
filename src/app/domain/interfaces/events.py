"""Event handling interfaces"""

from abc import ABC, abstractmethod
from typing import List

from ..models.events import DomainEvent


class EventHandler(ABC):
    """Base event handler interface"""
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Handle domain event"""
        pass
    
    @abstractmethod
    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this handler can handle the event"""
        pass


class EventPublisher(ABC):
    """Event publisher interface"""
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish single event"""
        pass
    
    @abstractmethod
    async def publish_many(self, events: List[DomainEvent]) -> None:
        """Publish multiple events"""
        pass


class EventStore(ABC):
    """Event store interface"""
    
    @abstractmethod
    async def save_event(self, event: DomainEvent) -> None:
        """Save event to store"""
        pass
    
    @abstractmethod
    async def get_events(
        self, 
        aggregate_id: str, 
        from_version: int = 0
    ) -> List[DomainEvent]:
        """Get events for aggregate"""
        pass
    
    @abstractmethod
    async def get_all_events(
        self, 
        from_timestamp: float = None,
        event_types: List[str] = None
    ) -> List[DomainEvent]:
        """Get all events with optional filters"""
        pass