"""Domain repository interfaces."""

from abc import ABC, abstractmethod


class UnitOfWork(ABC):
    """Abstract Unit of Work interface."""

    @abstractmethod
    async def __aenter__(self):
        """Async context manager entry."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

    @abstractmethod
    async def commit(self):
        """Commit the current transaction."""
        pass

    @abstractmethod
    async def rollback(self):
        """Rollback the current transaction."""
        pass