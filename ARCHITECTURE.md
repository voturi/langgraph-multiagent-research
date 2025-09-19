# Architecture Guide

This document explains the architectural principles and design decisions behind this framework-agnostic application template.

## 🎯 Core Principle

**Keep domain logic completely independent of frameworks.** Frameworks are implementation details, not architectural foundations.

## 🏗️ Layer Architecture

### 1. Domain Layer (Core)
**Location**: `src/app/domain/`
**Dependencies**: None (pure Python)
**Purpose**: Contains all business logic and rules

```python
# Domain services have no framework dependencies
class ConversationService:
    def __init__(self, event_publisher: EventPublisher):  # Abstract interface
        self.event_publisher = event_publisher
    
    async def start_conversation(self, uow: UnitOfWork, user_id: UserId):
        # Pure business logic - works with any implementation
        conversation = Conversation(id=..., user_id=user_id)
        await uow.conversations.save(conversation)
        await self.event_publisher.publish(ConversationStarted(...))
        return conversation
```

#### Domain Components:

- **Entities** (`entities.py`): Business objects with identity and behavior
- **Value Objects** (`value_objects.py`): Immutable objects representing values
- **Events** (`events.py`): Domain events that represent business occurrences  
- **Services** (`services/`): Business logic that doesn't belong to entities
- **Interfaces** (`interfaces/`): Abstract contracts for external dependencies

### 2. Orchestration Layer
**Location**: `src/app/orchestration/`
**Dependencies**: Domain layer + chosen orchestration framework
**Purpose**: Coordinates domain services using an orchestration framework

```python
# Framework-agnostic workflow definition
class ConversationWorkflow(WorkflowOrchestrator):
    async def execute_workflow(self, workflow_name, context, input_data):
        # Uses domain services - no framework-specific logic
        conversation = await self.conversation_service.start_conversation(...)
        return ExecutionResult.success_result(...)

# LangGraph-specific wrapper (thin!)
class LangGraphOrchestrator(WorkflowOrchestrator):
    async def execute_workflow(self, workflow_name, context, input_data):
        # Translate to LangGraph state
        initial_state = {...}
        final_state = await self.graph.ainvoke(initial_state)
        # Translate back to domain result
        return ExecutionResult(...)
```

#### Key Insight:
LangGraph is just **one possible orchestration implementation**. You could easily create:
- `AirflowOrchestrator` for Apache Airflow
- `CeleryOrchestrator` for Celery
- `SimpleOrchestrator` for direct execution

### 3. Infrastructure Layer  
**Location**: `src/app/infrastructure/`
**Dependencies**: Domain interfaces + chosen infrastructure
**Purpose**: Concrete implementations of domain interfaces

```python
# Implement domain interfaces with chosen technology
class SqliteUserRepository(UserRepository):  # Domain interface
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        # SQLite-specific implementation
        # Could easily be PostgresUserRepository, MongoUserRepository, etc.
```

### 4. API Layer
**Location**: `src/app/api/`  
**Dependencies**: Orchestration layer + chosen API framework
**Purpose**: Expose functionality via chosen API framework

## 🔄 Dependency Flow

```
API Layer
    ↓ depends on
Orchestration Layer  
    ↓ depends on
Domain Layer
    ↑ interfaces implemented by
Infrastructure Layer
```

**Key Rule**: Dependencies only point inward toward the domain.

## 🔌 Framework Swapping Examples

### Swapping Orchestration Frameworks

**From LangGraph to Apache Airflow:**

```python
# Before (LangGraph)
from app.orchestration.langgraph import LangGraphOrchestrator
orchestrator = LangGraphOrchestrator(conversation_workflow, **deps)

# After (Airflow) - business logic unchanged!
from app.orchestration.airflow import AirflowOrchestrator  
orchestrator = AirflowOrchestrator(conversation_workflow, **deps)
```

**Domain services don't change at all.**

### Swapping Databases

```python
# Before (SQLite)
from app.infrastructure.repositories.sqlite import SqliteUnitOfWork
uow = SqliteUnitOfWork(database_url)

# After (PostgreSQL) - business logic unchanged!
from app.infrastructure.repositories.postgresql import PostgresUnitOfWork
uow = PostgresUnitOfWork(database_url)
```

**Domain services don't change at all.**

### Swapping APIs

```python
# Before (FastAPI)
from app.api.rest.fastapi import FastAPIApp
api = FastAPIApp(orchestrator)

# After (Flask) - business logic unchanged!
from app.api.rest.flask import FlaskApp  
api = FlaskApp(orchestrator)
```

**Domain services don't change at all.**

## 🧪 Testing Strategy

### Unit Tests (Fast, Isolated)
Test domain logic with mock dependencies:

```python
def test_conversation_service():
    # Mock dependencies
    mock_event_publisher = Mock()
    mock_uow = Mock()
    
    # Test pure business logic
    service = ConversationService(mock_event_publisher)
    result = await service.start_conversation(mock_uow, user_id)
    
    # Assert business rules
    assert result.user_id == user_id
    mock_event_publisher.publish.assert_called_once()
```

### Integration Tests (Slower, Real Dependencies)
Test orchestration with real infrastructure:

```python
def test_langgraph_orchestration():
    # Use real dependencies
    real_uow = SqliteUnitOfWork(":memory:")
    real_llm_service = OpenAIService(api_key="test")
    
    orchestrator = LangGraphOrchestrator(...)
    result = await orchestrator.execute_workflow(...)
    
    # Test integration works end-to-end
    assert result.success
```

### Contract Tests
Ensure interface implementations are correct:

```python
def test_repository_contract():
    """Test that SqliteUserRepository correctly implements UserRepository"""
    repo = SqliteUserRepository()
    
    # Test interface contract
    assert hasattr(repo, 'find_by_id')
    assert hasattr(repo, 'save')
    # ... test all interface methods
```

## 🚀 Benefits

### 1. **Risk Reduction**
- Framework changes don't break business logic
- Can evaluate new frameworks without rewriting everything
- Easier to fix framework-specific bugs

### 2. **Team Productivity**  
- Domain experts can work on business logic independently
- Infrastructure team can optimize data layer independently
- Frontend team can work against stable domain contracts

### 3. **Testing & Quality**
- Fast unit tests for business logic (no infrastructure)
- Clear separation makes bugs easier to locate
- Business rules are explicitly encoded in domain services

### 4. **Cost Optimization**
- Choose best infrastructure for each component
- Easy to optimize expensive parts (e.g., switch to faster database)
- Can use different frameworks for different use cases

## ⚠️ Common Anti-Patterns to Avoid

### ❌ Framework Leakage
```python
# BAD: Domain service depends on LangGraph
from langgraph.graph import StateGraph

class ConversationService:
    def process(self, state: StateGraph):  # Framework leak!
        # Business logic mixed with framework
```

```python
# GOOD: Domain service is framework-agnostic
class ConversationService:
    def process(self, context: ExecutionContext):  # Domain concept
        # Pure business logic
```

### ❌ Infrastructure in Domain
```python
# BAD: Domain service directly uses database
import sqlite3

class ConversationService:
    def save(self, conversation):
        conn = sqlite3.connect("db.sqlite3")  # Infrastructure leak!
        # ...
```

```python
# GOOD: Domain service uses abstract interface
class ConversationService:
    def __init__(self, uow: UnitOfWork):  # Abstract interface
        self.uow = uow
        
    async def save(self, conversation):
        await self.uow.conversations.save(conversation)  # No infrastructure details
```

### ❌ Thick Orchestration Layer
```python
# BAD: Business logic in orchestration layer
class LangGraphOrchestrator:
    async def execute_workflow(self, ...):
        # Complex business rules here - wrong layer!
        if user.is_premium and message_count > 100:
            # Business logic belongs in domain layer
```

```python  
# GOOD: Thin orchestration layer
class LangGraphOrchestrator:
    async def execute_workflow(self, ...):
        # Just translate between LangGraph and domain
        result = await self.conversation_workflow.execute(...)
        return self._translate_result(result)
```

## 🎓 Key Architectural Decisions

### 1. **Dependency Inversion**
- Domain layer defines interfaces it needs
- Infrastructure layer implements those interfaces
- Orchestration layer coordinates domain services
- API layer exposes orchestration capabilities

### 2. **Interface Segregation** 
- Small, focused interfaces (e.g., `UserRepository`, `LLMService`)
- Easy to implement and test
- Clear contracts between layers

### 3. **Single Responsibility**
- Domain: business logic only
- Orchestration: coordination only  
- Infrastructure: technology implementation only
- API: presentation only

### 4. **Open/Closed Principle**
- Easy to add new orchestration frameworks (extend)
- Don't need to modify existing domain logic (closed)

## 🔄 Migration Path

If you have an existing LangGraph application, here's how to migrate:

1. **Extract Domain Logic**: Move business rules to domain services
2. **Create Interfaces**: Abstract external dependencies  
3. **Implement Infrastructure**: Create concrete implementations
4. **Wrap LangGraph**: Make LangGraph a thin orchestration layer
5. **Add API Layer**: Separate presentation from orchestration

Each step can be done incrementally without breaking existing functionality.

---

**Remember**: The goal is not to eliminate frameworks, but to control where and how they're used. Frameworks should serve your domain logic, not dictate it.